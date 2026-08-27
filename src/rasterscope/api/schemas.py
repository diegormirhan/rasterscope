from typing import Any

from pydantic import BaseModel


class HealthResponse(BaseModel):
    service: str
    version: str
    status: str
    model_ready: bool
    scenarios_ready: bool


class ScenarioCatalog(BaseModel):
    generated_at: str
    model: str
    scenarios: list[dict[str, Any]]


class PixelInspection(BaseModel):
    x: int
    y: int
    phase: str
    class_id: int
    class_name: str
    color: str
    confidence: float
    uncertainty: float


class ModelCatalog(BaseModel):
    baseline: dict[str, Any]
    unet: dict[str, Any]
