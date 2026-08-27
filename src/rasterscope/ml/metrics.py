from dataclasses import dataclass
from itertools import pairwise

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class SegmentationMetrics:
    confusion_matrix: NDArray[np.int64]
    per_class_iou: tuple[float, ...]
    per_class_dice: tuple[float, ...]
    mean_iou: float
    mean_dice: float
    pixel_accuracy: float
    expected_calibration_error: float | None = None

    def to_dict(self, class_names: tuple[str, ...]) -> dict[str, object]:
        return {
            "mean_iou": self.mean_iou,
            "mean_dice": self.mean_dice,
            "pixel_accuracy": self.pixel_accuracy,
            "expected_calibration_error": self.expected_calibration_error,
            "per_class": [
                {"name": name, "iou": self.per_class_iou[index], "dice": self.per_class_dice[index]}
                for index, name in enumerate(class_names)
            ],
            "confusion_matrix": self.confusion_matrix.tolist(),
        }


def segmentation_metrics(
    prediction: NDArray[np.integer],
    target: NDArray[np.integer],
    class_count: int,
    ignore_index: int,
) -> SegmentationMetrics:
    if prediction.shape != target.shape:
        raise ValueError("Prediction and target masks must have the same shape")

    valid = target != ignore_index
    valid_target = target[valid].astype(np.int64)
    valid_prediction = prediction[valid].astype(np.int64)
    encoded = class_count * valid_target + valid_prediction
    matrix = np.bincount(encoded, minlength=class_count**2).reshape(class_count, class_count)

    true_positive = np.diag(matrix).astype(np.float64)
    false_positive = matrix.sum(axis=0) - true_positive
    false_negative = matrix.sum(axis=1) - true_positive
    union = true_positive + false_positive + false_negative
    dice_denominator = 2 * true_positive + false_positive + false_negative

    iou = np.divide(true_positive, union, out=np.full(class_count, np.nan), where=union > 0)
    dice = np.divide(
        2 * true_positive,
        dice_denominator,
        out=np.full(class_count, np.nan),
        where=dice_denominator > 0,
    )
    total = matrix.sum()
    accuracy = float(true_positive.sum() / total) if total else 0.0

    return SegmentationMetrics(
        confusion_matrix=matrix,
        per_class_iou=tuple(float(value) for value in iou),
        per_class_dice=tuple(float(value) for value in dice),
        mean_iou=float(np.nanmean(iou)),
        mean_dice=float(np.nanmean(dice)),
        pixel_accuracy=accuracy,
    )


def expected_calibration_error(
    probabilities: NDArray[np.floating],
    target: NDArray[np.integer],
    ignore_index: int,
    bin_count: int = 15,
) -> float:
    if probabilities.ndim != target.ndim + 1:
        raise ValueError("Probabilities must add one class dimension to target")
    confidence = probabilities.max(axis=1)
    prediction = probabilities.argmax(axis=1)
    valid = target != ignore_index
    confidence = confidence[valid]
    correctness = (prediction[valid] == target[valid]).astype(np.float64)
    if confidence.size == 0:
        return 0.0

    boundaries = np.linspace(0.0, 1.0, bin_count + 1)
    calibration_error = 0.0
    for lower, upper in pairwise(boundaries):
        in_bin = (confidence > lower) & (confidence <= upper)
        if np.any(in_bin):
            weight = np.count_nonzero(in_bin) / confidence.size
            calibration_error += weight * abs(
                correctness[in_bin].mean() - confidence[in_bin].mean()
            )
    return float(calibration_error)
