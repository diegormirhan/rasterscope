from dataclasses import dataclass
from pathlib import Path

import numpy as np
import onnxruntime as ort
from numpy.typing import NDArray
from PIL import Image

from rasterscope.domain.analysis import normalized_entropy


@dataclass(frozen=True)
class SegmentationPrediction:
    mask: NDArray[np.uint8]
    probabilities: NDArray[np.float32]
    uncertainty: NDArray[np.float32]


class OnnxSegmenter:
    def __init__(self, model_path: Path, input_size: int) -> None:
        if not model_path.exists():
            raise FileNotFoundError(f"ONNX model not found: {model_path}")
        self._session = ort.InferenceSession(
            str(model_path),
            providers=["CPUExecutionProvider"],
        )
        self._input_name = self._session.get_inputs()[0].name
        self._input_size = input_size

    def predict(self, image: Image.Image) -> SegmentationPrediction:
        original_size = image.size
        prepared = image.convert("RGB").resize(
            (self._input_size, self._input_size),
            Image.Resampling.BILINEAR,
        )
        values = np.asarray(prepared, dtype=np.float32).transpose(2, 0, 1)[None] / 255.0
        logits = self._session.run(None, {self._input_name: values})[0][0]
        probabilities = _softmax(logits)
        mask = probabilities.argmax(axis=0).astype(np.uint8)

        if original_size != (self._input_size, self._input_size):
            mask = np.asarray(
                Image.fromarray(mask).resize(original_size, Image.Resampling.NEAREST),
                dtype=np.uint8,
            )
            resized_probabilities = [
                np.asarray(
                    Image.fromarray(class_map).resize(original_size, Image.Resampling.BILINEAR),
                    dtype=np.float32,
                )
                for class_map in probabilities
            ]
            probabilities = np.stack(resized_probabilities)
            probabilities /= probabilities.sum(axis=0, keepdims=True).clip(min=1e-8)

        return SegmentationPrediction(
            mask=mask,
            probabilities=probabilities.astype(np.float32),
            uncertainty=normalized_entropy(probabilities),
        )


def _softmax(logits: NDArray[np.floating]) -> NDArray[np.float32]:
    shifted = logits - logits.max(axis=0, keepdims=True)
    exponentials = np.exp(shifted)
    return (exponentials / exponentials.sum(axis=0, keepdims=True)).astype(np.float32)
