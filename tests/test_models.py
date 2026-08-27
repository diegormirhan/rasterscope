import numpy as np
import torch

from rasterscope.ml.baseline import ColorCentroidBaseline, fit_color_centroid_baseline
from rasterscope.ml.losses import CrossEntropyDiceLoss
from rasterscope.ml.models.unet import CompactUNet


def test_unet_preserves_spatial_resolution_and_class_count() -> None:
    model = CompactUNet(class_count=7, base_channels=4)

    logits = model(torch.rand(2, 3, 64, 64))

    assert logits.shape == (2, 7, 64, 64)


def test_combined_loss_backpropagates_with_ignored_pixels() -> None:
    logits = torch.randn(1, 3, 8, 8, requires_grad=True)
    target = torch.randint(0, 3, (1, 8, 8))
    target[0, 0, 0] = 255
    loss_function = CrossEntropyDiceLoss(torch.ones(3), ignore_index=255, dice_weight=0.4)

    loss = loss_function(logits, target)
    loss.backward()

    assert torch.isfinite(loss)
    assert logits.grad is not None


def test_color_centroid_baseline_learns_separable_colors(tmp_path) -> None:
    image = np.array([[[20, 30, 20], [200, 210, 190]]], dtype=np.uint8)
    mask = np.array([[0, 1]], dtype=np.uint8)
    baseline = fit_color_centroid_baseline([(image, mask)], 2, ignore_index=255)
    artifact = tmp_path / "baseline.npz"

    baseline.save(artifact)
    restored = ColorCentroidBaseline.load(artifact)

    assert restored.predict(image).tolist() == [[0, 1]]
