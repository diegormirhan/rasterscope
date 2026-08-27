import json
from datetime import UTC, datetime

import numpy as np
import planetary_computer
import pystac_client
import rasterio
from PIL import Image
from rasterio.warp import transform
from rasterio.windows import Window

from rasterscope.domain.analysis import calculate_area_summary, calculate_transition_matrix
from rasterscope.runtime.inference import OnnxSegmenter
from rasterscope.runtime.rendering import render_mask, render_uncertainty
from rasterscope.settings import AppConfig, ScenarioSettings

STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"


def build_scenarios(config: AppConfig) -> dict[str, object]:
    catalog = pystac_client.Client.open(STAC_URL, modifier=planetary_computer.sign_inplace)
    segmenter = OnnxSegmenter(config.inference.model_path, config.inference.input_size)
    manifest: list[dict[str, object]] = []
    for scenario in config.scenarios:
        before_item = _select_item(catalog, scenario, scenario.before)
        after_item = _select_item(catalog, scenario, scenario.after)
        scenario_dir = config.paths.scenario_dir / scenario.id
        scenario_dir.mkdir(parents=True, exist_ok=True)
        before_image = _read_visual_window(before_item, scenario.bbox, config.inference.input_size)
        after_image = _read_visual_window(after_item, scenario.bbox, config.inference.input_size)
        before_path = scenario_dir / "before.png"
        after_path = scenario_dir / "after.png"
        before_image.save(before_path)
        after_image.save(after_path)

        before_prediction = segmenter.predict(before_image)
        after_prediction = segmenter.predict(after_image)
        colors = tuple(item.color for item in config.classes)
        render_mask(before_prediction.mask, colors, scenario_dir / "before-mask.png")
        render_mask(after_prediction.mask, colors, scenario_dir / "after-mask.png")
        render_uncertainty(before_prediction.uncertainty, scenario_dir / "before-uncertainty.png")
        render_uncertainty(after_prediction.uncertainty, scenario_dir / "after-uncertainty.png")
        np.savez_compressed(
            scenario_dir / "predictions.npz",
            before_mask=before_prediction.mask,
            after_mask=after_prediction.mask,
            before_probability=before_prediction.probabilities.max(axis=0),
            after_probability=after_prediction.probabilities.max(axis=0),
            before_uncertainty=before_prediction.uncertainty,
            after_uncertainty=after_prediction.uncertainty,
        )
        manifest.append(
            _scenario_record(
                config,
                scenario,
                before_item,
                after_item,
                before_prediction.mask,
                after_prediction.mask,
                before_prediction.uncertainty,
                after_prediction.uncertainty,
            )
        )

    record = {
        "generated_at": datetime.now(UTC).isoformat(),
        "model": config.inference.model_path.name,
        "scenarios": manifest,
    }
    (config.paths.scenario_dir / "manifest.json").write_text(
        json.dumps(record, indent=2) + "\n",
        encoding="utf-8",
    )
    return record


def _select_item(
    catalog: pystac_client.Client,
    scenario: ScenarioSettings,
    date_range: str,
):
    search = catalog.search(
        collections=["sentinel-2-l2a"],
        bbox=scenario.bbox,
        datetime=date_range,
        query={"eo:cloud_cover": {"lt": scenario.max_cloud_cover}},
        max_items=30,
    )
    items = list(search.items())
    if not items:
        raise RuntimeError(f"No Sentinel-2 items found for {scenario.id} in {date_range}")
    return min(items, key=lambda item: float(item.properties.get("eo:cloud_cover", 100)))


def _read_visual_window(item, bbox: tuple[float, float, float, float], size: int) -> Image.Image:
    asset = item.assets["visual"]
    with rasterio.open(asset.href) as source:
        center_longitude = (bbox[0] + bbox[2]) / 2
        center_latitude = (bbox[1] + bbox[3]) / 2
        projected_x, projected_y = transform(
            "EPSG:4326",
            source.crs,
            [center_longitude],
            [center_latitude],
        )
        center_row, center_column = source.index(projected_x[0], projected_y[0])
        window = Window(center_column - size // 2, center_row - size // 2, size, size)
        values = source.read(
            indexes=(1, 2, 3),
            window=window,
            boundless=True,
            fill_value=0,
        )
    return Image.fromarray(np.moveaxis(values, 0, -1).astype(np.uint8), mode="RGB")


def _scenario_record(
    config: AppConfig,
    scenario: ScenarioSettings,
    before_item,
    after_item,
    before_mask: np.ndarray,
    after_mask: np.ndarray,
    before_uncertainty: np.ndarray,
    after_uncertainty: np.ndarray,
) -> dict[str, object]:
    class_count = len(config.classes)
    ignore_index = config.dataset.ignore_index
    before_area = calculate_area_summary(
        before_mask,
        class_count,
        config.dataset.meters_per_pixel,
        ignore_index,
    )
    after_area = calculate_area_summary(
        after_mask,
        class_count,
        config.dataset.meters_per_pixel,
        ignore_index,
    )
    transitions = calculate_transition_matrix(before_mask, after_mask, class_count, ignore_index)
    return {
        "id": scenario.id,
        "name": scenario.name,
        "location": scenario.location,
        "bbox": scenario.bbox,
        "domain_shift": scenario.domain_shift,
        "note": scenario.note,
        "before": _item_record(before_item),
        "after": _item_record(after_item),
        "assets": {
            "before": f"/scenarios/{scenario.id}/before.png",
            "after": f"/scenarios/{scenario.id}/after.png",
            "before_mask": f"/scenarios/{scenario.id}/before-mask.png",
            "after_mask": f"/scenarios/{scenario.id}/after-mask.png",
            "before_uncertainty": f"/scenarios/{scenario.id}/before-uncertainty.png",
            "after_uncertainty": f"/scenarios/{scenario.id}/after-uncertainty.png",
        },
        "area_unit": "hectares",
        "class_areas": [
            {
                "id": item.id,
                "name": item.name,
                "short_name": item.short_name,
                "color": item.color,
                "before_hectares": before_area.hectares[item.id],
                "after_hectares": after_area.hectares[item.id],
                "delta_hectares": round(
                    after_area.hectares[item.id] - before_area.hectares[item.id],
                    4,
                ),
                "before": before_area.hectares[item.id],
                "after": after_area.hectares[item.id],
                "delta": round(
                    after_area.hectares[item.id] - before_area.hectares[item.id],
                    4,
                ),
            }
            for item in config.classes
        ],
        "transition_matrix": transitions.tolist(),
        "mean_uncertainty": {
            "before": float(before_uncertainty.mean()),
            "after": float(after_uncertainty.mean()),
        },
        "source_type": "sentinel-2-stac",
        "limitations": [
            "Area values are model-derived estimates at an assumed 10 m pixel size.",
            "The RGB model cannot establish the cause of a detected class transition.",
            *(
                ["This scene is outside the Norway-focused training geography."]
                if scenario.domain_shift
                else []
            ),
        ],
    }


def _item_record(item) -> dict[str, object]:
    return {
        "item_id": item.id,
        "datetime": item.datetime.isoformat() if item.datetime else None,
        "cloud_cover": item.properties.get("eo:cloud_cover"),
        "platform": item.properties.get("platform"),
    }
