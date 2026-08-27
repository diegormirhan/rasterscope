import io
import json
from datetime import UTC, datetime
from functools import lru_cache
from typing import Any
from uuid import uuid4

import numpy as np
from fastapi import HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

from rasterscope.domain.analysis import calculate_transition_matrix
from rasterscope.runtime.inference import OnnxSegmenter, SegmentationPrediction
from rasterscope.runtime.rendering import render_mask, render_uncertainty
from rasterscope.settings import AppConfig, get_config


@lru_cache(maxsize=1)
def get_segmenter() -> OnnxSegmenter:
    config = get_config()
    return OnnxSegmenter(config.inference.model_path, config.inference.input_size)


def analyze_upload_pair(
    before_upload: UploadFile,
    after_upload: UploadFile,
    config: AppConfig,
) -> dict[str, Any]:
    before_image = _read_upload(before_upload, config.api.max_upload_megabytes)
    after_image = _read_upload(after_upload, config.api.max_upload_megabytes)
    size = config.inference.input_size
    before_image = before_image.resize((size, size), Image.Resampling.BILINEAR)
    after_image = after_image.resize((size, size), Image.Resampling.BILINEAR)
    try:
        segmenter = get_segmenter()
    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail="Inference model is unavailable") from error

    before_prediction = segmenter.predict(before_image)
    after_prediction = segmenter.predict(after_image)
    analysis_id = str(uuid4())
    analysis_dir = config.paths.scenario_dir / "uploads" / analysis_id
    analysis_dir.mkdir(parents=True, exist_ok=False)
    before_image.save(analysis_dir / "before.png")
    after_image.save(analysis_dir / "after.png")
    colors = tuple(item.color for item in config.classes)
    render_mask(before_prediction.mask, colors, analysis_dir / "before-mask.png")
    render_mask(after_prediction.mask, colors, analysis_dir / "after-mask.png")
    render_uncertainty(before_prediction.uncertainty, analysis_dir / "before-uncertainty.png")
    render_uncertainty(after_prediction.uncertainty, analysis_dir / "after-uncertainty.png")
    np.savez_compressed(
        analysis_dir / "predictions.npz",
        before_mask=before_prediction.mask,
        after_mask=after_prediction.mask,
        before_probability=before_prediction.probabilities.max(axis=0),
        after_probability=after_prediction.probabilities.max(axis=0),
        before_uncertainty=before_prediction.uncertainty,
        after_uncertainty=after_prediction.uncertainty,
    )
    record = _upload_record(config, analysis_id, before_prediction, after_prediction)
    (analysis_dir / "record.json").write_text(
        json.dumps(record, indent=2) + "\n",
        encoding="utf-8",
    )
    return record


def _read_upload(upload: UploadFile, maximum_megabytes: int) -> Image.Image:
    content = upload.file.read(maximum_megabytes * 1024 * 1024 + 1)
    if len(content) > maximum_megabytes * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"{upload.filename} exceeds the upload limit")
    try:
        image = Image.open(io.BytesIO(content))
        image.load()
    except (UnidentifiedImageError, OSError) as error:
        raise HTTPException(
            status_code=422, detail=f"{upload.filename} is not a valid image"
        ) from error
    return image.convert("RGB")


def _upload_record(
    config: AppConfig,
    analysis_id: str,
    before: SegmentationPrediction,
    after: SegmentationPrediction,
) -> dict[str, Any]:
    class_count = len(config.classes)
    transitions = calculate_transition_matrix(
        before.mask,
        after.mask,
        class_count,
        config.dataset.ignore_index,
    )
    return {
        "id": analysis_id,
        "name": "Uploaded comparison",
        "location": "Local files",
        "domain_shift": True,
        "note": "User-provided RGB images; geographic scale and acquisition metadata are unknown.",
        "before": {"datetime": None, "item_id": "local-upload", "cloud_cover": None},
        "after": {"datetime": None, "item_id": "local-upload", "cloud_cover": None},
        "assets": {
            key: f"/scenarios/uploads/{analysis_id}/{filename}"
            for key, filename in {
                "before": "before.png",
                "after": "after.png",
                "before_mask": "before-mask.png",
                "after_mask": "after-mask.png",
                "before_uncertainty": "before-uncertainty.png",
                "after_uncertainty": "after-uncertainty.png",
            }.items()
        },
        "area_unit": "pixels",
        "class_areas": [
            _class_area(item.model_dump(), before.mask, after.mask) for item in config.classes
        ],
        "transition_matrix": transitions.tolist(),
        "mean_uncertainty": {
            "before": float(before.uncertainty.mean()),
            "after": float(after.uncertainty.mean()),
        },
        "source_type": "local-upload",
        "created_at": datetime.now(UTC).isoformat(),
        "limitations": [
            "Pixel counts are not physical area measurements without georeferencing.",
            "The model was trained on Norway-focused Sentinel-2 RGB tiles.",
            "Inputs are resized to 256 x 256 and assumed to be spatially aligned.",
        ],
    }


def _class_area(
    class_item: dict[str, Any],
    before_mask: np.ndarray,
    after_mask: np.ndarray,
) -> dict[str, Any]:
    class_id = class_item["id"]
    before_count = int(np.count_nonzero(before_mask == class_id))
    after_count = int(np.count_nonzero(after_mask == class_id))
    return {
        **class_item,
        "before": before_count,
        "after": after_count,
        "delta": after_count - before_count,
    }
