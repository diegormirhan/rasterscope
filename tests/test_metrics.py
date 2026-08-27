import numpy as np

from rasterscope.ml.metrics import segmentation_metrics


def test_segmentation_metrics_report_macro_scores_and_ignored_pixels() -> None:
    target = np.array([[0, 0, 1], [1, 2, 255]], dtype=np.uint8)
    prediction = np.array([[0, 1, 1], [1, 2, 0]], dtype=np.uint8)

    metrics = segmentation_metrics(prediction, target, class_count=3, ignore_index=255)

    assert metrics.confusion_matrix.tolist() == [[1, 1, 0], [0, 2, 0], [0, 0, 1]]
    assert np.isclose(metrics.pixel_accuracy, 0.8)
    assert 0.0 < metrics.mean_iou < 1.0
    assert 0.0 < metrics.mean_dice < 1.0
