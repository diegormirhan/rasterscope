from fastapi.testclient import TestClient

from rasterscope.api.app import create_app


def test_health_reports_service_status() -> None:
    client = TestClient(create_app(serve_frontend=False))

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] in {"ready", "degraded"}
    assert response.json()["service"] == "RasterScope"


def test_scenario_catalog_contains_auditable_source_metadata() -> None:
    client = TestClient(create_app(serve_frontend=False))

    response = client.get("/api/scenarios")

    assert response.status_code == 200
    scenarios = response.json()["scenarios"]
    assert len(scenarios) >= 2
    assert scenarios[0]["before"]["item_id"].startswith("S2")


def test_unknown_scenario_returns_not_found() -> None:
    client = TestClient(create_app(serve_frontend=False))

    response = client.get("/api/scenarios/does-not-exist")

    assert response.status_code == 404
    assert response.json()["detail"] == "Scenario not found"


def test_pixel_inspection_returns_model_evidence() -> None:
    client = TestClient(create_app(serve_frontend=False))

    response = client.get(
        "/api/scenarios/norway-agriculture/inspect",
        params={"phase": "after", "x": 128, "y": 128},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["class_name"]
    assert 0 <= payload["confidence"] <= 1
    assert 0 <= payload["uncertainty"] <= 1


def test_report_is_self_contained_html() -> None:
    client = TestClient(create_app(serve_frontend=False))

    response = client.get("/api/scenarios/norway-agriculture/report")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "attachment;" in response.headers["content-disposition"]
    assert "data:image/png;base64," in response.text
