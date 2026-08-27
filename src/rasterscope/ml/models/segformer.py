from torch import Tensor, nn
from torch.nn import functional as functional
from transformers import SegformerConfig, SegformerForSemanticSegmentation


class SegFormerAdapter(nn.Module):
    def __init__(self, model: SegformerForSemanticSegmentation) -> None:
        super().__init__()
        self.model = model

    def forward(self, image: Tensor) -> Tensor:
        logits = self.model(pixel_values=image).logits
        return functional.interpolate(
            logits,
            size=image.shape[-2:],
            mode="bilinear",
            align_corners=False,
        )


def create_segformer(class_count: int, pretrained: bool = True) -> SegFormerAdapter:
    if pretrained:
        model = SegformerForSemanticSegmentation.from_pretrained(
            "nvidia/segformer-b0-finetuned-ade-512-512",
            num_labels=class_count,
            ignore_mismatched_sizes=True,
            id2label={index: str(index) for index in range(class_count)},
            label2id={str(index): index for index in range(class_count)},
        )
    else:
        model = SegformerForSemanticSegmentation(
            SegformerConfig(num_labels=class_count, semantic_loss_ignore_index=255)
        )
    return SegFormerAdapter(model)
