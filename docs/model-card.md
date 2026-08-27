# Model card: RasterScope compact U-Net

## Summary

RasterScope uses a compact U-Net for seven-class semantic segmentation of 256 × 256 RGB satellite tiles. The runtime artifact is `artifacts/models/unet.onnx` and executes locally with ONNX Runtime.

The model is a portfolio-scale experiment, not a production remote-sensing foundation model.

## Model details

| Field | Value |
| --- | --- |
| Architecture | Compact U-Net |
| Input | RGB, 3 × 256 × 256, normalized to [0, 1] |
| Output | Seven per-pixel class logits |
| Base channels | 16 |
| Training device | CPU |
| Epochs | 4 |
| Batch size | 8 |
| Optimizer | AdamW |
| Learning rate | 0.001 |
| Weight decay | 0.0001 |
| Loss | Weighted cross-entropy + Dice |
| Seed | 42 |
| Selection metric | Validation mean IoU |
| Best validation mIoU | 0.383 |

## Held-out performance

The fixed test split contains 119 images.

| Metric | Value |
| --- | ---: |
| Mean IoU | 0.3873 |
| Macro Dice | 0.4865 |
| Pixel accuracy | 0.7979 |
| Expected calibration error | 0.0695 |

| Class | IoU | Dice |
| --- | ---: | ---: |
| Tree cover | 0.7887 | 0.8818 |
| Low vegetation | 0.3581 | 0.5274 |
| Cropland | 0.4115 | 0.5830 |
| Built-up | 0.3592 | 0.5286 |
| Exposed terrain | 0.0000 | 0.0000 |
| Permanent water | 0.7934 | 0.8848 |
| Herbaceous wetland | 0.0000 | 0.0000 |

The 0.3873 aggregate mIoU should not obscure the complete failure on the two rarest classes.

## Baseline

The RGB color-centroid baseline reaches 0.2141 mIoU, 0.3248 macro Dice, and 0.5340 pixel accuracy. The U-Net produces an 80.85% relative mIoU improvement.

## Calibration and uncertainty

Expected calibration error is computed over per-pixel maximum softmax confidence. The UI visualizes normalized predictive entropy:

`H(p) / log(K)` for `K = 7` classes.

Entropy expresses how distributed the model probabilities are. Low entropy does not prove correctness, particularly under geographic domain shift.

## Export validation

PyTorch and ONNX outputs were compared on a real Sentinel-2 demonstration scene:

- maximum absolute logit error: `2.74e-6`;
- mean absolute logit error: `1.95e-7`;
- mask agreement: `100%`.

## Intended use

- local demonstrations of semantic segmentation;
- model-debugging and uncertainty UI experiments;
- educational before/after screening on aligned RGB scenes.

## Limitations

- Training data is Norway-focused.
- The model uses only three visible bands.
- Two rare classes are effectively absent from predictions.
- Temporal summaries compare independent predictions and can amplify classification error.
- The model cannot infer the cause of a land-cover transition.
- Area conversion assumes 10 m square pixels for prepared scenes.

## SegFormer path

The codebase includes an optional SegFormer transfer-learning implementation for experimentation. It was not trained for the published benchmark and is intentionally omitted from the result table. Users should not infer performance from its presence in the source tree.

## Ethical and operational guidance

Do not use this model for legal boundaries, ecological certification, high-stakes monitoring, or automated action. Review source imagery, uncertainty, geography, and suitable ground truth before drawing conclusions.
