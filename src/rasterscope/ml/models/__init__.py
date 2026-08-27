from torch import nn

from rasterscope.ml.models.unet import CompactUNet


def create_model(
    name: str,
    class_count: int,
    base_channels: int = 16,
    pretrained: bool = True,
) -> nn.Module:
    normalized_name = name.lower()
    if normalized_name == "unet":
        return CompactUNet(class_count=class_count, base_channels=base_channels)
    if normalized_name == "segformer":
        from rasterscope.ml.models.segformer import create_segformer

        return create_segformer(class_count=class_count, pretrained=pretrained)
    raise ValueError(f"Unknown model: {name}")


__all__ = ["CompactUNet", "create_model"]
