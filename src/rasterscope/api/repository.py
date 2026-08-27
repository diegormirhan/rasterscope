import json
from pathlib import Path
from typing import Any


class ScenarioRepository:
    def __init__(self, scenario_dir: Path) -> None:
        self._scenario_dir = scenario_dir

    @property
    def manifest_path(self) -> Path:
        return self._scenario_dir / "manifest.json"

    def catalog(self) -> dict[str, Any]:
        if not self.manifest_path.exists():
            return {"generated_at": "", "model": "unavailable", "scenarios": []}
        return json.loads(self.manifest_path.read_text(encoding="utf-8"))

    def get(self, scenario_id: str) -> dict[str, Any] | None:
        bundled = next(
            (scenario for scenario in self.catalog()["scenarios"] if scenario["id"] == scenario_id),
            None,
        )
        if bundled is not None:
            return bundled
        upload_record = self._scenario_dir / "uploads" / scenario_id / "record.json"
        if upload_record.exists():
            return json.loads(upload_record.read_text(encoding="utf-8"))
        return None

    def predictions(self, scenario_id: str) -> Path:
        bundled = self._scenario_dir / scenario_id / "predictions.npz"
        if bundled.exists():
            return bundled
        return self._scenario_dir / "uploads" / scenario_id / "predictions.npz"

    def scenario_path(self, scenario_id: str) -> Path:
        bundled = self._scenario_dir / scenario_id
        return bundled if bundled.exists() else self._scenario_dir / "uploads" / scenario_id
