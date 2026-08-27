import base64
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape


def render_scenario_report(
    scenario: dict[str, Any],
    classes: list[dict[str, Any]],
    template_dir: Path,
    scenario_dir: Path,
) -> str:
    environment = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(("html", "xml")),
    )
    template = environment.get_template("report.html.j2")
    return template.render(
        scenario=scenario,
        classes=classes,
        generated_at=datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
        before_image=_image_data_uri(scenario_dir / "before.png"),
        after_image=_image_data_uri(scenario_dir / "after.png"),
    )


def _image_data_uri(path: Path) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"
