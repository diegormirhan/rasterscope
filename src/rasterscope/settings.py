from functools import lru_cache
from pathlib import Path
from typing import Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class PathSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_parquet: Path
    split_manifest: Path
    model_dir: Path
    run_dir: Path
    scenario_dir: Path
    report_dir: Path
    frontend_dist: Path


class SplitSettings(BaseModel):
    train: float = Field(gt=0, lt=1)
    validation: float = Field(gt=0, lt=1)
    test: float = Field(gt=0, lt=1)

    @model_validator(mode="after")
    def validate_total(self) -> Self:
        if abs(self.train + self.validation + self.test - 1.0) > 1e-9:
            raise ValueError("Dataset split ratios must sum to 1")
        return self


class DatasetSettings(BaseModel):
    repository: str
    revision: str
    sample_count: int = Field(gt=0)
    tile_size: int = Field(gt=0)
    meters_per_pixel: float = Field(gt=0)
    split: SplitSettings
    ignore_index: int = 255
    raw_to_training: dict[int, int]


class ClassSettings(BaseModel):
    id: int = Field(ge=0)
    name: str
    short_name: str
    color: str


class TrainingSettings(BaseModel):
    model: str
    batch_size: int = Field(gt=0)
    epochs: int = Field(gt=0)
    learning_rate: float = Field(gt=0)
    weight_decay: float = Field(ge=0)
    num_workers: int = Field(ge=0)
    base_channels: int = Field(gt=0)
    max_class_weight: float = Field(ge=1)
    dice_weight: float = Field(ge=0, le=1)
    device: str


class InferenceSettings(BaseModel):
    model_path: Path
    input_size: int = Field(gt=0)
    overlay_opacity: float = Field(ge=0, le=1)
    uncertainty_threshold: float = Field(ge=0, le=1)


class ApiSettings(BaseModel):
    host: str
    port: int = Field(gt=0, le=65535)
    max_upload_megabytes: int = Field(gt=0)


class ScenarioSettings(BaseModel):
    id: str
    name: str
    location: str
    bbox: tuple[float, float, float, float]
    before: str
    after: str
    max_cloud_cover: float = Field(ge=0, le=100)
    domain_shift: bool
    note: str


class ProjectSettings(BaseModel):
    name: str
    seed: int


class AppConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project: ProjectSettings
    paths: PathSettings
    dataset: DatasetSettings
    classes: tuple[ClassSettings, ...]
    training: TrainingSettings
    inference: InferenceSettings
    scenarios: tuple[ScenarioSettings, ...]
    api: ApiSettings

    def resolve_paths(self, project_root: Path) -> Self:
        path_values = {
            field: project_root / value if not value.is_absolute() else value
            for field, value in self.paths.model_dump().items()
        }
        inference_path = self.inference.model_path
        if not inference_path.is_absolute():
            inference_path = project_root / inference_path
        return self.model_copy(
            update={
                "paths": PathSettings(**path_values),
                "inference": self.inference.model_copy(update={"model_path": inference_path}),
            }
        )


class EnvironmentSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RASTERSCOPE_", env_file=".env")

    config: Path = Path("config.yaml")
    log_level: str = "INFO"


def find_project_root(config_path: Path) -> Path:
    resolved = config_path.resolve()
    if resolved.exists():
        return resolved.parent
    raise FileNotFoundError(f"Configuration file not found: {resolved}")


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    environment = EnvironmentSettings()
    project_root = find_project_root(environment.config)
    with environment.config.open(encoding="utf-8") as config_file:
        raw_config = yaml.safe_load(config_file)
    return AppConfig.model_validate(raw_config).resolve_paths(project_root)
