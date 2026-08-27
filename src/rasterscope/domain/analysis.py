from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class AreaSummary:
    pixel_counts: tuple[int, ...]
    hectares: tuple[float, ...]
    valid_hectares: float


def calculate_area_summary(
    mask: NDArray[np.integer],
    class_count: int,
    meters_per_pixel: float,
    ignore_index: int,
) -> AreaSummary:
    valid = mask != ignore_index
    pixel_counts = tuple(
        int(np.count_nonzero(mask[valid] == class_id)) for class_id in range(class_count)
    )
    hectares_per_pixel = (meters_per_pixel**2) / 10_000
    hectares = tuple(round(count * hectares_per_pixel, 6) for count in pixel_counts)
    return AreaSummary(
        pixel_counts=pixel_counts,
        hectares=hectares,
        valid_hectares=round(sum(pixel_counts) * hectares_per_pixel, 6),
    )


def calculate_transition_matrix(
    before: NDArray[np.integer],
    after: NDArray[np.integer],
    class_count: int,
    ignore_index: int,
) -> NDArray[np.int64]:
    if before.shape != after.shape:
        raise ValueError("Before and after masks must have the same shape")
    valid = (before != ignore_index) & (after != ignore_index)
    encoded = class_count * before[valid].astype(np.int64) + after[valid].astype(np.int64)
    return np.bincount(encoded, minlength=class_count**2).reshape(class_count, class_count)


def normalized_entropy(probabilities: NDArray[np.floating]) -> NDArray[np.float32]:
    if probabilities.ndim != 3:
        raise ValueError("Probabilities must have shape (classes, height, width)")
    class_count = probabilities.shape[0]
    if class_count < 2:
        raise ValueError("At least two classes are required")
    terms = np.zeros_like(probabilities, dtype=np.float64)
    positive = probabilities > 0
    terms[positive] = probabilities[positive] * np.log(probabilities[positive])
    entropy = -np.sum(terms, axis=0) / np.log(class_count)
    return entropy.astype(np.float32)
