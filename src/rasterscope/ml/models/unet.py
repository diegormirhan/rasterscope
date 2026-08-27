import torch
from torch import Tensor, nn
from torch.nn import functional as functional


class ConvBlock(nn.Sequential):
    def __init__(self, input_channels: int, output_channels: int) -> None:
        super().__init__(
            nn.Conv2d(input_channels, output_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(output_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(output_channels, output_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(output_channels),
            nn.ReLU(inplace=True),
        )


class UpBlock(nn.Module):
    def __init__(self, input_channels: int, skip_channels: int, output_channels: int) -> None:
        super().__init__()
        self.upsample = nn.ConvTranspose2d(
            input_channels,
            output_channels,
            kernel_size=2,
            stride=2,
        )
        self.convolutions = ConvBlock(output_channels + skip_channels, output_channels)

    def forward(self, values: Tensor, skip: Tensor) -> Tensor:
        values = self.upsample(values)
        if values.shape[-2:] != skip.shape[-2:]:
            values = functional.interpolate(values, size=skip.shape[-2:], mode="bilinear")
        return self.convolutions(torch.cat((skip, values), dim=1))


class CompactUNet(nn.Module):
    def __init__(self, class_count: int, base_channels: int = 16) -> None:
        super().__init__()
        self.encoder_one = ConvBlock(3, base_channels)
        self.encoder_two = ConvBlock(base_channels, base_channels * 2)
        self.encoder_three = ConvBlock(base_channels * 2, base_channels * 4)
        self.bottleneck = ConvBlock(base_channels * 4, base_channels * 8)
        self.pool = nn.MaxPool2d(2)
        self.decoder_three = UpBlock(base_channels * 8, base_channels * 4, base_channels * 4)
        self.decoder_two = UpBlock(base_channels * 4, base_channels * 2, base_channels * 2)
        self.decoder_one = UpBlock(base_channels * 2, base_channels, base_channels)
        self.classifier = nn.Conv2d(base_channels, class_count, kernel_size=1)

    def forward(self, image: Tensor) -> Tensor:
        encoder_one = self.encoder_one(image)
        encoder_two = self.encoder_two(self.pool(encoder_one))
        encoder_three = self.encoder_three(self.pool(encoder_two))
        bottleneck = self.bottleneck(self.pool(encoder_three))
        decoder_three = self.decoder_three(bottleneck, encoder_three)
        decoder_two = self.decoder_two(decoder_three, encoder_two)
        decoder_one = self.decoder_one(decoder_two, encoder_one)
        return self.classifier(decoder_one)
