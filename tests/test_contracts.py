"""Contract tests for Python analysis request/response shape (Issue #51).

These tests verify required fields from docs/API_CONTRACTS.md are present in
engine outputs. They fail on contract drift.

IMPORTANT: Any synthetic data used here is a labeled test fixture only, never
a real NASA observation or real scientific result.
"""

import numpy as np
import pandas as pd
import xarray as xr

from scientific_engine.grid_analysis import analyze_grid


def _synthetic_da(periods=240):
    # SYNTHETIC TEST FIXTURE - not NASA observations
    t = pd.date_range("2001-01-01", periods=periods, freq="MS")
    vals = 50.0 + 0.1 * (np.arange(periods) / 12.0)
    return xr.DataArray(
        vals.reshape(periods, 1, 1),
        coords={"time": t, "lat": [0.0], "lon": [36.8]},
        dims=("time", "lat", "lon"),
        name="precipitation",
        attrs={"units": "mm/month", "synthetic": True},
    )


def test_analysis_response_contract_shape():
    da = _synthetic_da()
    res = analyze_grid(
        da,
        investigation_id="INV-001",
        bounds={"min_lon": 36.7, "min_lat": -0.1, "max_lon": 36.9, "max_lat": 0.1},
        period={"start": "2001-01-01", "end": "2020-12-31"},
        config={"min_months": 9, "min_years": 10, "alpha": 0.05},
        dataset_meta={"short_name": "GPM_3IMERGM", "version": "07"},
    )

    # Top-level contract fields
    for key in ("status", "cells", "run_metadata", "summary"):
        assert key in res
    assert res["status"] == "completed"
    assert isinstance(res["cells"], list)
    assert isinstance(res["summary"], dict)

    # Run metadata contract
    meta = res["run_metadata"]
    for key in ("contract", "version", "investigation_id", "methods", "parameters", "dataset", "bounds", "period", "generated_at", "engine_version", "grid"):
        assert key in meta, f"missing run_metadata.{key}"
    assert meta["contract"] == "analysis-response"
    for key in ("trend_test", "slope", "multiple_testing"):
        assert key in meta["methods"]
    for key in ("min_months", "min_years", "alpha"):
        assert key in meta["parameters"]

    # Cell contract
    cell = res["cells"][0]
    for key in ("cell_id", "lat", "lon", "n_observations", "completeness", "classification", "flags"):
        assert key in cell, f"missing cell.{key}"
    assert cell["classification"] in {
        "significant_increase",
        "significant_decrease",
        "no_significant_trend",
        "insufficient_data",
        "inconclusive",
    }
    # For sufficient cells, trend stats should be present
    if cell["classification"] != "insufficient_data":
        assert "sens_slope" in cell
        assert "mann_kendall" in cell
        assert "p_value" in cell


def test_analysis_response_seasonal_contract_shape():
    da = _synthetic_da()
    res = analyze_grid(
        da,
        investigation_id="INV-001",
        config={"aggregation": "seasonal", "seasons": {"MAM": [3, 4, 5], "OND": [10, 11, 12]}, "min_months_per_season": 2, "min_years": 10},
    )
    cell = res["cells"][0]
    assert "seasonal_trends" in cell
    mam = cell["seasonal_trends"]["MAM"]
    for key in ("season", "classification", "flags", "n_years", "completeness"):
        assert key in mam
    assert res["run_metadata"]["parameters"]["aggregation_mode"] == "seasonal"
