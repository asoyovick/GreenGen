"""API contract and edge-case tests on a controlled synthetic layer set."""
from __future__ import annotations


def test_health_and_mode(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["mode"] == "synthetic"
    assert body["synthetic"] is True
    assert set(body["variables_loaded"]) == {"precipitation", "vegetation", "temperature"}
    assert body["overlays_available"] is True
    assert "not real observations" in body["synthetic_banner"].lower()
    assert r.headers["X-GCE-Synthetic"] == "true"


def test_variables_payload(client):
    r = client.get("/api/variables")
    assert r.status_code == 200
    body = r.json()
    assert body["mode"] == "synthetic"
    keys = {v["key"] for v in body["variables"]}
    assert keys == {"precipitation", "vegetation", "temperature"}
    by_key = {v["key"]: v for v in body["variables"]}
    assert by_key["vegetation"]["surface"] == ["land"]
    assert by_key["temperature"]["model_based"] is True
    assert by_key["precipitation"]["unit"] == "mm/month"
    assert by_key["vegetation"]["period"] == ["2002-01", "2024-12"]
    assert body["not_a_forecast"].startswith("Observed change only")


def test_layers_payload(client):
    r = client.get("/api/layers")
    assert r.status_code == 200
    body = r.json()
    assert body["default_layer"] == "change_score"
    assert body["bounds"] == [-180.0, -85.0, 180.0, 85.0]
    assert body["synthetic"] is True
    assert "change_score" in body["layers"]
    assert "vegetation_class" in body["layers"]
    assert body["layers"]["vegetation_class"]["legend"][0]["label"] == "Significant increase"
    assert body["layers"]["vegetation_class"]["units"] == "NDVI"
    assert body["layers"]["change_score"]["url"].startswith("/overlays/synthetic/")


def test_overlay_png_is_served(client):
    meta = client.get("/api/layers").json()
    url = meta["layers"]["vegetation_class"]["url"]
    r = client.get(url)
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"
    assert r.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_land_report_ranks_significant_variables(client):
    r = client.get("/api/report", params={"lat": 55, "lon": 55})
    assert r.status_code == 200
    body = r.json()
    assert len(body["variables"]) == 3
    assert body["variables"][0]["key"] == "vegetation"  # largest standardized trend
    top = body["variables"][0]
    assert top["significant"] is True
    assert top["class"] == 1
    assert top["rate_per_decade"] > 0
    assert top["low_confidence"] is False
    assert top["n_years"] == 23
    assert top["cell"] == {"lat": 55.0, "lon": 55.0}
    assert "statistically significant" in top["summary"]
    assert body["cell"] == {"lat": 55.0, "lon": 55.0}
    assert body["surface_inferred"]["value"] == "land"
    assert body["mode"] == "synthetic"
    assert "not a forecast" in body["not_a_forecast"].lower()
    assert "p_value" not in top
    assert "p_value" not in body


def test_ocean_report_excludes_land_only_variables(client):
    r = client.get("/api/report", params={"lat": 0, "lon": -150})
    assert r.status_code == 200
    body = r.json()
    keys = {v["key"] for v in body["variables"]}
    assert "vegetation" not in keys
    assert keys == {"precipitation", "temperature"}
    assert body["surface_inferred"]["value"] != "land"
    assert body["variables"][0]["key"] == "temperature"


def test_divergence_is_reported_near_boundary(client):
    r = client.get("/api/report", params={"lat": 55, "lon": 70, "window": 5})
    body = r.json()
    veg = next(v for v in body["variables"] if v["key"] == "vegetation")
    assert veg["nearby"]["up"] > 0.15
    assert veg["nearby"]["down"] > 0.15
    assert body["divergence_detected"] is True
    assert "opposite directions" in body["summary"]


def test_decreasing_cell_reports_negative_class_and_rate(client):
    r = client.get("/api/report", params={"lat": 55, "lon": 85})
    body = r.json()
    veg = next(v for v in body["variables"] if v["key"] == "vegetation")
    assert veg["class"] == -1
    assert veg["rate_per_decade"] < 0
    assert veg["significant"] is True


def test_no_applicable_variables_returns_empty_report(client):
    r = client.get("/api/report", params={"lat": 89, "lon": 179})
    assert r.status_code == 200
    body = r.json()
    assert body["variables"] == []
    assert body["summary"] == "No variables apply at this location."
    assert body["surface_inferred"]["value"] == "unknown"


def test_timeseries_uses_stored_slope_and_flags_significance(client):
    r = client.get("/api/timeseries", params={"lat": 55, "lon": 55, "variable": "vegetation"})
    assert r.status_code == 200
    body = r.json()
    assert body["applies"] is True
    assert body["variable"] == "Vegetation greenness (NDVI)"
    assert body["years"][0] == 2002 and body["years"][-1] == 2024
    assert len(body["annual_anomaly"]) == len(body["years"]) == 23
    assert len(body["trend_line"]) == 23
    assert body["slope_per_year"] > 0
    assert body["slope_per_decade"] == body["slope_per_year"] * 10
    assert body["significant"] is True
    assert body["verdict"] == "significant increase"
    assert body["fdr_corrected"] is True
    assert "p_value" not in body
    # The reconstructed line must have the stored slope.
    assert abs((body["trend_line"][-1] - body["trend_line"][0]) / 22 - body["slope_per_year"]) < 1e-9


def test_timeseries_for_ocean_vegetation_is_explicit_no_data(client):
    r = client.get("/api/timeseries", params={"lat": 0, "lon": -150, "variable": "vegetation"})
    assert r.status_code == 200
    body = r.json()
    assert body["applies"] is False
    assert body["years"] == []
    assert body["annual_anomaly"] == []
    assert "does not apply" in body["summary"]


def test_input_validation_and_errors(client):
    assert client.get("/api/report", params={"lat": 100, "lon": 0}).status_code == 422
    assert client.get("/api/report", params={"lat": 0, "lon": 200}).status_code == 422
    assert client.get("/api/report", params={"lat": 0, "lon": 0, "window": 0}).status_code == 422
    assert client.get("/api/timeseries", params={"lat": 0, "lon": 0, "variable": "nope"}).status_code == 404
    assert client.get("/api/timeseries", params={"lat": -100, "lon": 0, "variable": "vegetation"}).status_code == 422


def test_missing_layers_returns_clear_503(empty_client):
    health = empty_client.get("/api/health").json()
    assert health["status"] == "degraded"
    assert health["variables_loaded"] == []
    r = empty_client.get("/api/report", params={"lat": 0, "lon": 0})
    assert r.status_code == 503
    assert "make pipeline" in r.json()["detail"].lower()
    assert empty_client.get("/api/variables").status_code == 503
    assert empty_client.get("/api/layers").status_code == 503


def test_api_index_lists_contract_and_scope(client):
    r = client.get("/api")
    assert r.status_code == 200
    body = r.json()
    assert body["mode"] == "synthetic"
    assert set(body["endpoints"]) >= {
        "/api/health", "/api/variables", "/api/report", "/api/timeseries", "/api/layers"
    }
    assert "not a forecast" in body["note"].lower()


def test_unknown_path_returns_json_404(client):
    r = client.get("/api/does-not-exist")
    assert r.status_code == 404
    assert r.headers["content-type"].startswith("application/json")
    assert "detail" in r.json()


def test_cors_allows_the_dev_frontend(client):
    r = client.options(
        "/api/health",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"


def test_root_serves_built_frontend_when_present(client):
    from src.common.config import REPO_ROOT

    built = REPO_ROOT / "frontend" / "dist" / "index.html"
    r = client.get("/")
    if built.exists():
        assert r.status_code == 200
        assert 'id="root"' in r.text
    else:
        assert r.status_code == 404


def test_timeseries_unknown_variable_lists_available(client):
    r = client.get("/api/timeseries", params={"lat": 0, "lon": 0, "variable": "nope"})
    assert r.status_code == 404
    detail = r.json()["detail"]
    assert "nope" in detail
    assert "precipitation" in detail


def test_mode_headers_on_every_response(client):
    r = client.get("/api/variables")
    assert r.headers["X-GCE-Mode"] == "synthetic"
    assert r.headers["X-GCE-Synthetic"] == "true"
