import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pyarrow.parquet as parquet
import structlog
import torch
from torch.utils.data import DataLoader

from rasterscope.ml.baseline import fit_color_centroid_baseline
from rasterscope.ml.dataset import SatelliteDataset, calculate_class_counts, calculate_class_weights
from rasterscope.ml.engine import (
    evaluate_model,
    resolve_device,
    set_reproducible_seed,
    train_model,
    write_run_record,
)
from rasterscope.ml.metrics import segmentation_metrics
from rasterscope.ml.models import create_model
from rasterscope.ml.splits import SplitManifest, create_split_manifest
from rasterscope.ml.taxonomy import Taxonomy
from rasterscope.settings import AppConfig

logger = structlog.get_logger()


def taxonomy_from_config(config: AppConfig) -> Taxonomy:
    return Taxonomy(
        raw_to_training=config.dataset.raw_to_training,
        class_names=tuple(item.name for item in config.classes),
        ignore_index=config.dataset.ignore_index,
    )


def prepare_dataset(config: AppConfig) -> dict[str, object]:
    parquet_file = parquet.ParquetFile(config.paths.dataset_parquet)
    actual_count = parquet_file.metadata.num_rows
    if actual_count != config.dataset.sample_count:
        raise ValueError(f"Expected {config.dataset.sample_count} samples but found {actual_count}")
    split = create_split_manifest(
        sample_count=actual_count,
        seed=config.project.seed,
        train_ratio=config.dataset.split.train,
        validation_ratio=config.dataset.split.validation,
    )
    split.write(config.paths.split_manifest)
    audit = {
        "dataset": config.dataset.repository,
        "revision": config.dataset.revision,
        "sample_count": actual_count,
        "split_counts": {
            "train": len(split.train),
            "validation": len(split.validation),
            "test": len(split.test),
        },
        "tile_size": config.dataset.tile_size,
        "meters_per_pixel": config.dataset.meters_per_pixel,
    }
    write_run_record(config.paths.run_dir / "dataset_audit.json", audit)
    return audit


def train_baseline(config: AppConfig) -> dict[str, object]:
    split = ensure_split(config)
    taxonomy = taxonomy_from_config(config)
    dataset = SatelliteDataset(config.paths.dataset_parquet, split.train, taxonomy)
    samples = [dataset.source_pair(index) for index in split.train]
    baseline = fit_color_centroid_baseline(
        samples,
        taxonomy.class_count,
        taxonomy.ignore_index,
        seed=config.project.seed,
    )
    artifact_path = config.paths.model_dir / "color_centroid_baseline.npz"
    baseline.save(artifact_path)

    test_dataset = SatelliteDataset(config.paths.dataset_parquet, split.test, taxonomy)
    predictions: list[np.ndarray] = []
    targets: list[np.ndarray] = []
    for source_index in split.test:
        image, mask = test_dataset.source_pair(source_index)
        predictions.append(baseline.predict(image))
        targets.append(mask)
    metrics = segmentation_metrics(
        np.stack(predictions),
        np.stack(targets),
        taxonomy.class_count,
        taxonomy.ignore_index,
    ).to_dict(taxonomy.class_names)
    record = {
        "model": "color-centroid-baseline",
        "created_at": datetime.now(UTC).isoformat(),
        "artifact": str(artifact_path),
        "test_metrics": metrics,
    }
    write_run_record(config.paths.run_dir / "baseline_metrics.json", record)
    return record


def train_segmentation_model(config: AppConfig, model_name: str) -> dict[str, object]:
    set_reproducible_seed(config.project.seed)
    split = ensure_split(config)
    taxonomy = taxonomy_from_config(config)
    train_dataset = SatelliteDataset(
        config.paths.dataset_parquet,
        split.train,
        taxonomy,
        augment=True,
        seed=config.project.seed,
    )
    validation_dataset = SatelliteDataset(
        config.paths.dataset_parquet,
        split.validation,
        taxonomy,
    )
    class_counts = calculate_class_counts(train_dataset, taxonomy.class_count)
    class_weights = calculate_class_weights(class_counts, config.training.max_class_weight)
    train_loader = DataLoader(
        train_dataset,
        batch_size=config.training.batch_size,
        shuffle=True,
        num_workers=config.training.num_workers,
    )
    validation_loader = DataLoader(
        validation_dataset,
        batch_size=config.training.batch_size,
        shuffle=False,
        num_workers=config.training.num_workers,
    )
    model = create_model(
        model_name,
        taxonomy.class_count,
        config.training.base_channels,
        pretrained=True,
    )
    device = resolve_device(config.training.device)
    artifact_path = config.paths.model_dir / f"{model_name}.pt"
    metadata = {
        "model": model_name,
        "class_names": taxonomy.class_names,
        "base_channels": config.training.base_channels,
        "dataset_revision": config.dataset.revision,
        "seed": config.project.seed,
    }
    logger.info(
        "training_started", model=model_name, device=str(device), samples=len(train_dataset)
    )
    training_result = train_model(
        model=model,
        train_loader=train_loader,
        validation_loader=validation_loader,
        class_names=taxonomy.class_names,
        class_weights=class_weights,
        ignore_index=taxonomy.ignore_index,
        dice_weight=config.training.dice_weight,
        epochs=config.training.epochs,
        learning_rate=config.training.learning_rate,
        weight_decay=config.training.weight_decay,
        device=device,
        artifact_path=artifact_path,
        metadata=metadata,
    )
    record = {
        **metadata,
        "created_at": datetime.now(UTC).isoformat(),
        "device": str(device),
        "class_counts": class_counts.tolist(),
        "class_weights": class_weights.tolist(),
        **training_result,
    }
    write_run_record(config.paths.run_dir / f"{model_name}_training.json", record)
    return record


def evaluate_checkpoint(config: AppConfig, model_name: str) -> dict[str, object]:
    split = ensure_split(config)
    taxonomy = taxonomy_from_config(config)
    checkpoint_path = config.paths.model_dir / f"{model_name}.pt"
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    model = create_model(
        model_name,
        taxonomy.class_count,
        config.training.base_channels,
        pretrained=False,
    )
    model.load_state_dict(checkpoint["model_state"])
    test_dataset = SatelliteDataset(config.paths.dataset_parquet, split.test, taxonomy)
    test_loader = DataLoader(
        test_dataset,
        batch_size=config.training.batch_size,
        shuffle=False,
        num_workers=config.training.num_workers,
    )
    device = resolve_device(config.training.device)
    model.to(device)
    result = evaluate_model(
        model,
        test_loader,
        taxonomy.class_names,
        taxonomy.ignore_index,
        loss_function=None,
        device=device,
    )
    record = {
        "model": model_name,
        "created_at": datetime.now(UTC).isoformat(),
        "dataset_revision": config.dataset.revision,
        "split": "test",
        "metrics": result.metrics,
        "duration_seconds": result.duration_seconds,
    }
    write_run_record(config.paths.run_dir / f"{model_name}_test_metrics.json", record)
    return record


def export_onnx(config: AppConfig, model_name: str) -> Path:
    taxonomy = taxonomy_from_config(config)
    checkpoint = torch.load(
        config.paths.model_dir / f"{model_name}.pt",
        map_location="cpu",
        weights_only=True,
    )
    model = create_model(
        model_name,
        taxonomy.class_count,
        config.training.base_channels,
        pretrained=False,
    )
    model.load_state_dict(checkpoint["model_state"])
    model.eval()
    destination = config.paths.model_dir / f"{model_name}.onnx"
    destination.parent.mkdir(parents=True, exist_ok=True)
    example = torch.randn(1, 3, config.inference.input_size, config.inference.input_size)
    program = torch.onnx.export(
        model,
        (example,),
        input_names=["image"],
        output_names=["logits"],
        dynamo=True,
    )
    program.save(destination)
    return destination


def ensure_split(config: AppConfig) -> SplitManifest:
    if not config.paths.split_manifest.exists():
        prepare_dataset(config)
    return SplitManifest.read(config.paths.split_manifest)


def print_record(record: dict[str, object]) -> None:
    print(json.dumps(record, indent=2))
