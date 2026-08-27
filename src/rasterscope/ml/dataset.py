import io
from collections.abc import Sequence
from pathlib import Path

import numpy as np
import pyarrow.parquet as parquet
import torch
from PIL import Image
from torch import Tensor
from torch.utils.data import Dataset

from rasterscope.ml.taxonomy import Taxonomy


class SatelliteDataset(Dataset[tuple[Tensor, Tensor]]):
    def __init__(
        self,
        parquet_path: Path,
        indices: Sequence[int],
        taxonomy: Taxonomy,
        augment: bool = False,
        seed: int = 42,
    ) -> None:
        if not parquet_path.exists():
            raise FileNotFoundError(f"Dataset parquet not found: {parquet_path}")
        self._table = parquet.read_table(parquet_path, columns=["image", "mask"])
        self._indices = tuple(indices)
        self._taxonomy = taxonomy
        self._augment = augment
        self._seed = seed

    def __len__(self) -> int:
        return len(self._indices)

    def __getitem__(self, item: int) -> tuple[Tensor, Tensor]:
        source_index = self._indices[item]
        image_bytes = self._table["image"][source_index].as_py()["bytes"]
        mask_bytes = self._table["mask"][source_index].as_py()["bytes"]

        image = np.asarray(Image.open(io.BytesIO(image_bytes)).convert("RGB"), dtype=np.float32)
        raw_mask = np.asarray(Image.open(io.BytesIO(mask_bytes)), dtype=np.uint8)
        mask = self._taxonomy.remap(raw_mask)

        if self._augment:
            image, mask = self._apply_deterministic_augmentation(image, mask, source_index)

        image_tensor = torch.from_numpy(np.ascontiguousarray(image.transpose(2, 0, 1))) / 255.0
        mask_tensor = torch.from_numpy(np.ascontiguousarray(mask)).long()
        return image_tensor, mask_tensor

    def source_pair(self, source_index: int) -> tuple[np.ndarray, np.ndarray]:
        image_bytes = self._table["image"][source_index].as_py()["bytes"]
        mask_bytes = self._table["mask"][source_index].as_py()["bytes"]
        image = np.asarray(Image.open(io.BytesIO(image_bytes)).convert("RGB"), dtype=np.uint8)
        raw_mask = np.asarray(Image.open(io.BytesIO(mask_bytes)), dtype=np.uint8)
        return image, self._taxonomy.remap(raw_mask)

    def _apply_deterministic_augmentation(
        self,
        image: np.ndarray,
        mask: np.ndarray,
        source_index: int,
    ) -> tuple[np.ndarray, np.ndarray]:
        generator = np.random.default_rng(self._seed + source_index)
        if generator.random() < 0.5:
            image = np.flip(image, axis=1)
            mask = np.flip(mask, axis=1)
        if generator.random() < 0.5:
            image = np.flip(image, axis=0)
            mask = np.flip(mask, axis=0)
        rotations = int(generator.integers(0, 4))
        return np.rot90(image, rotations), np.rot90(mask, rotations)


def calculate_class_counts(dataset: SatelliteDataset, class_count: int) -> np.ndarray:
    counts = np.zeros(class_count, dtype=np.int64)
    for _, mask in dataset:
        values, frequencies = np.unique(mask.numpy(), return_counts=True)
        for value, frequency in zip(values, frequencies, strict=True):
            if 0 <= value < class_count:
                counts[value] += frequency
    return counts


def calculate_class_weights(counts: np.ndarray, maximum: float) -> Tensor:
    present = counts > 0
    frequencies = counts[present] / counts[present].sum()
    weights = np.ones_like(counts, dtype=np.float32)
    weights[present] = np.minimum(1.0 / np.sqrt(frequencies), maximum)
    weights[present] /= weights[present].mean()
    return torch.from_numpy(weights)
