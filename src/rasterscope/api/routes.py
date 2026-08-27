import json
from pathlib import Path
from typing import Annotated, Any

import numpy as np
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi import Path as ApiPath
from fastapi.responses import HTMLResponse

from rasterscope import __version__
from rasterscope.api.repository import ScenarioRepository
from rasterscope.api.schemas import (
    HealthResponse,
    ModelCatalog,
    PixelInspection,
    ScenarioCatalog,
)
from rasterscope.api.upload_analysis import analyze_upload_pair
from rasterscope.reporting.html_report import render_scenario_report
from rasterscope.settings import AppConfig, get_config

router = APIRouter(prefix="/api")


def get_repository(config: Annotated[AppConfig, Depends(get_config)]) -> ScenarioRepository:
    return ScenarioRepository(config.paths.scenario_dir)


ConfigDependency = Annotated[AppConfig, Depends(get_config)]
RepositoryDependency = Annotated[ScenarioRepository, Depends(get_repository)]


@router.get("/health")
def health(config: ConfigDependency, repository: RepositoryDependency) -> HealthResponse:
    model_ready = config.inference.model_path.exists()
    scenarios_ready = repository.manifest_path.exists()
    return HealthResponse(
        service=config.project.name,
        version=__version__,
        status="ready" if model_ready and scenarios_ready else "degraded",
        model_ready=model_ready,
        scenarios_ready=scenarios_ready,
    )


@router.get("/scenarios")
def list_scenarios(repository: RepositoryDependency) -> ScenarioCatalog:
    return ScenarioCatalog.model_validate(repository.catalog())


@router.get("/scenarios/{scenario_id}")
def get_scenario(
    scenario_id: Annotated[str, ApiPath(pattern="^[a-zA-Z0-9-]+$", max_length=80)],
    repository: RepositoryDependency,
) -> dict[str, Any]:
    return _require_scenario(repository, scenario_id)


@router.get("/scenarios/{scenario_id}/inspect")
def inspect_pixel(
    scenario_id: Annotated[str, ApiPath(pattern="^[a-zA-Z0-9-]+$", max_length=80)],
    repository: RepositoryDependency,
    config: ConfigDependency,
    phase: Annotated[str, Query(pattern="^(before|after)$")] = "after",
    x: Annotated[int, Query(ge=0)] = 0,
    y: Annotated[int, Query(ge=0)] = 0,
) -> PixelInspection:
    _require_scenario(repository, scenario_id)
    artifact_path = repository.predictions(scenario_id)
    if not artifact_path.exists():
        raise HTTPException(status_code=503, detail="Scenario predictions are unavailable")
    with np.load(artifact_path) as artifact:
        mask = artifact[f"{phase}_mask"]
        confidence = artifact[f"{phase}_probability"]
        uncertainty = artifact[f"{phase}_uncertainty"]
        if y >= mask.shape[0] or x >= mask.shape[1]:
            raise HTTPException(status_code=422, detail="Pixel is outside the image")
        class_id = int(mask[y, x])
        class_item = config.classes[class_id]
        return PixelInspection(
            x=x,
            y=y,
            phase=phase,
            class_id=class_id,
            class_name=class_item.name,
            color=class_item.color,
            confidence=float(confidence[y, x]),
            uncertainty=float(uncertainty[y, x]),
        )


@router.get("/models")
def list_models(config: ConfigDependency) -> ModelCatalog:
    return ModelCatalog(
        baseline=_read_json(config.paths.run_dir / "baseline_metrics.json"),
        unet=_read_json(config.paths.run_dir / "unet_test_metrics.json"),
    )


@router.post("/analyze")
def analyze_pair(
    config: ConfigDependency,
    before: Annotated[UploadFile, File(description="Earlier RGB image")],
    after: Annotated[UploadFile, File(description="Later RGB image")],
) -> dict[str, Any]:
    return analyze_upload_pair(before, after, config)


@router.get("/scenarios/{scenario_id}/report", response_class=HTMLResponse)
def scenario_report(
    scenario_id: Annotated[str, ApiPath(pattern="^[a-zA-Z0-9-]+$", max_length=80)],
    repository: RepositoryDependency,
    config: ConfigDependency,
) -> HTMLResponse:
    scenario = _require_scenario(repository, scenario_id)
    template_dir = Path(__file__).resolve().parents[1] / "reporting" / "templates"
    html = render_scenario_report(
        scenario,
        [item.model_dump() for item in config.classes],
        template_dir,
        repository.scenario_path(scenario_id),
    )
    headers = {"Content-Disposition": f'attachment; filename="rasterscope-{scenario_id}.html"'}
    return HTMLResponse(html, headers=headers)


def _require_scenario(
    repository: ScenarioRepository,
    scenario_id: str,
) -> dict[str, Any]:
    scenario = repository.get(scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"status": "unavailable"}
    return json.loads(path.read_text(encoding="utf-8"))
