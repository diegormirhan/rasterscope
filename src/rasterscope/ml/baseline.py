from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class ColorCentroidBaseline:
    centroids: NDArray[np.float32]

    def predict(self, image: NDArray[np.uint8]) -> NDArray[np.uint8]:
        pixels = image.reshape(-1, 3).astype(np.float32)
        distances = ((pixels[:, None, :] - self.centroids[None, :, :]) ** 2).sum(axis=2)
        return distances.argmin(axis=1).reshape(image.shape[:2]).astype(np.uint8)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(path, centroids=self.centroids)

    @classmethod
    def load(cls, path: Path) -> "ColorCentroidBaseline":
        with np.load(path) as artifact:
            return cls(centroids=artifact["centroids"].astype(np.float32))


def fit_color_centroid_baseline(
    samples: list[tuple[NDArray[np.uint8], NDArray[np.uint8]]],
    class_count: int,
    ignore_index: int,
    pixels_per_image: int = 2048,
    seed: int = 42,
) -> ColorCentroidBaseline:
    generator = np.random.default_rng(seed)
    sums = np.zeros((class_count, 3), dtype=np.float64)
    counts = np.zeros(class_count, dtype=np.int64)

    for image, mask in samples:
        flat_image = image.reshape(-1, 3)
        flat_mask = mask.reshape(-1)
        valid_indices = np.flatnonzero(flat_mask != ignore_index)
        if len(valid_indices) > pixels_per_image:
            valid_indices = generator.choice(valid_indices, pixels_per_image, replace=False)
        selected_pixels = flat_image[valid_indices]
        selected_labels = flat_mask[valid_indices]
        for class_id in range(class_count):
            class_pixels = selected_pixels[selected_labels == class_id]
            if class_pixels.size:
                sums[class_id] += class_pixels.sum(axis=0)
                counts[class_id] += len(class_pixels)

    if np.any(counts == 0):
        missing = np.flatnonzero(counts == 0).tolist()
        raise ValueError(f"Cannot fit baseline; no sampled pixels for classes: {missing}")
    return ColorCentroidBaseline((sums / counts[:, None]).astype(np.float32))
