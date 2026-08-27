import json
import random
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import structlog
import torch
from torch import Tensor, nn
from torch.optim import AdamW
from torch.utils.data import DataLoader

from rasterscope.ml.losses import CrossEntropyDiceLoss
from rasterscope.ml.metrics import expected_calibration_error, segmentation_metrics

logger = structlog.get_logger()


@dataclass(frozen=True)
class EpochResult:
    loss: float
    metrics: dict[str, object]
    duration_seconds: float


def set_reproducible_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(True, warn_only=True)


def resolve_device(requested: str) -> torch.device:
    if requested != "auto":
        return torch.device(requested)
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def train_model(
    model: nn.Module,
    train_loader: DataLoader[tuple[Tensor, Tensor]],
    validation_loader: DataLoader[tuple[Tensor, Tensor]],
    class_names: tuple[str, ...],
    class_weights: Tensor,
    ignore_index: int,
    dice_weight: float,
    epochs: int,
    learning_rate: float,
    weight_decay: float,
    device: torch.device,
    artifact_path: Path,
    metadata: dict[str, object],
) -> dict[str, object]:
    model.to(device)
    loss_function = CrossEntropyDiceLoss(class_weights, ignore_index, dice_weight).to(device)
    optimizer = AdamW(model.parameters(), lr=learning_rate, weight_decay=weight_decay)
    history: list[dict[str, object]] = []
    best_mean_iou = -1.0

    for epoch in range(1, epochs + 1):
        train_loss = _train_epoch(model, train_loader, loss_function, optimizer, device)
        validation = evaluate_model(
            model,
            validation_loader,
            class_names,
            ignore_index,
            loss_function,
            device,
        )
        epoch_record = {
            "epoch": epoch,
            "train_loss": train_loss,
            "validation": validation.metrics,
            "validation_loss": validation.loss,
            "duration_seconds": validation.duration_seconds,
        }
        history.append(epoch_record)
        mean_iou = float(validation.metrics["mean_iou"])
        logger.info("epoch_complete", **epoch_record)
        if mean_iou > best_mean_iou:
            best_mean_iou = mean_iou
            artifact_path.parent.mkdir(parents=True, exist_ok=True)
            torch.save(
                {"model_state": model.state_dict(), "metadata": metadata, "history": history},
                artifact_path,
            )

    return {"best_validation_mean_iou": best_mean_iou, "history": history}


def _train_epoch(
    model: nn.Module,
    loader: DataLoader[tuple[Tensor, Tensor]],
    loss_function: nn.Module,
    optimizer: AdamW,
    device: torch.device,
) -> float:
    model.train()
    total_loss = 0.0
    for images, masks in loader:
        images = images.to(device)
        masks = masks.to(device)
        optimizer.zero_grad(set_to_none=True)
        loss = loss_function(model(images), masks)
        loss.backward()
        optimizer.step()
        total_loss += float(loss.detach()) * images.shape[0]
    return total_loss / len(loader.dataset)


def evaluate_model(
    model: nn.Module,
    loader: DataLoader[tuple[Tensor, Tensor]],
    class_names: tuple[str, ...],
    ignore_index: int,
    loss_function: nn.Module | None,
    device: torch.device,
) -> EpochResult:
    started = time.perf_counter()
    model.eval()
    predictions: list[np.ndarray] = []
    targets: list[np.ndarray] = []
    probability_batches: list[np.ndarray] = []
    total_loss = 0.0

    with torch.inference_mode():
        for images, masks in loader:
            images = images.to(device)
            masks_on_device = masks.to(device)
            logits = model(images)
            if loss_function is not None:
                total_loss += float(loss_function(logits, masks_on_device)) * images.shape[0]
            probabilities = torch.softmax(logits, dim=1).cpu().numpy()
            probability_batches.append(probabilities)
            predictions.append(probabilities.argmax(axis=1).astype(np.uint8))
            targets.append(masks.numpy().astype(np.uint8))

    prediction = np.concatenate(predictions)
    target = np.concatenate(targets)
    probabilities = np.concatenate(probability_batches)
    result = segmentation_metrics(prediction, target, len(class_names), ignore_index)
    metrics = result.to_dict(class_names)
    metrics["expected_calibration_error"] = expected_calibration_error(
        probabilities,
        target,
        ignore_index,
    )
    average_loss = total_loss / len(loader.dataset) if loss_function is not None else 0.0
    return EpochResult(
        loss=average_loss,
        metrics=metrics,
        duration_seconds=round(time.perf_counter() - started, 3),
    )


def write_run_record(path: Path, record: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
