import torch
from torch import Tensor, nn
from torch.nn import functional as functional


class CrossEntropyDiceLoss(nn.Module):
    def __init__(
        self,
        class_weights: Tensor,
        ignore_index: int,
        dice_weight: float,
    ) -> None:
        super().__init__()
        self.register_buffer("class_weights", class_weights)
        self.ignore_index = ignore_index
        self.dice_weight = dice_weight

    def forward(self, logits: Tensor, target: Tensor) -> Tensor:
        cross_entropy = functional.cross_entropy(
            logits,
            target,
            weight=self.class_weights,
            ignore_index=self.ignore_index,
        )
        dice = self._dice_loss(logits, target)
        return (1 - self.dice_weight) * cross_entropy + self.dice_weight * dice

    def _dice_loss(self, logits: Tensor, target: Tensor) -> Tensor:
        class_count = logits.shape[1]
        valid = target != self.ignore_index
        safe_target = torch.where(valid, target, torch.zeros_like(target))
        one_hot = functional.one_hot(safe_target, class_count).permute(0, 3, 1, 2).float()
        valid_channels = valid.unsqueeze(1)
        probabilities = torch.softmax(logits, dim=1) * valid_channels
        one_hot = one_hot * valid_channels
        intersection = (probabilities * one_hot).sum(dim=(0, 2, 3))
        denominator = probabilities.sum(dim=(0, 2, 3)) + one_hot.sum(dim=(0, 2, 3))
        dice = (2 * intersection + 1e-6) / (denominator + 1e-6)
        return 1 - dice.mean()
