"""Reference tests for the scientific analysis engine.

IMPORTANT: Test fixtures below are synthetic, programmatically generated arrays
used only to validate statistical/mathematical behavior in isolated tests.
They are NOT NASA observations and must never be presented as real results.
"""

import numpy as np
import pandas as pd
import xarray as xr

from scientific_engine.aggregation import annual_mean_anomalies
from scientific_engine.grid_analysis import analyze_grid
from scientific_engine.reliability import fdr_significance_mask


def _monthly_time(start="2001-01-01", periods=240):
    # default 20 years monthly
    return pd.date_range(start=start, periods=periods, freq="MS")


def _make_cube(values, lats=None, lons=None, start="2001-01-01"):
    """Create synthetic test DataArray (time, lat, lon). values shape (time, lat, lon)."""
    t = _monthly_time(start=start, periods=values.shape[0])
    if lats is None:
        lats = np.linspace(-1.0, 1.0, values.shape[1])
    if lons is None:
        lons = np.linspace(36.0, 37.0, values.shape[2])
    da = xr.DataArray(
        values,
        coords={"time": t, "lat": lats, "lon": lons},
        dims=("time", "lat", "lon"),
        name="precipitation",
        attrs={"units": "mm/month", "synthetic": True, "source": "SYNTHETIC TEST FIXTURE - not NASA observations"},
    )
    return da


def test_annual_aggregation_excludes_incomplete_years():
    # 2 years, monthly; make second year have too few valid months
    t = _monthly_time("2001-01-01", 24)
    vals = np.ones((24, 1, 1), dtype=float) * 10.0
    vals[12:, 0, 0] = np.nan  # all months in 2002 missing
    vals[12:15, 0, 0] = 10.0    # only 3 valid months (< 9)
    da = xr.DataArray(vals, coords={"time": t, "lat": [0.0], "lon": [36.0]}, dims=("time", "lat", "lon"), attrs={"units": "mm/month"})
    annual = annual_mean_anomalies(da, min_months=9)
    # 2001 valid, 2002 excluded -> NaN
    assert annual.sizes["year"] == 2
    assert np.isfinite(annual.sel(year=2001).values).all()
    assert not np.isfinite(annual.sel(year=2002).values).any()


def test_detects_strong_increasing_trend():
    # Synthetic increasing signal with small noise over 20 years
    rng = np.random.default_rng(42)
    n = 240
    years_idx = np.arange(n) / 12.0
    base = 50.0 + 0.5 * years_idx  # +0.5 mm/month per year
    seasonal = 10.0 * np.sin(2 * np.pi * np.arange(n) / 12.0)
    noise = rng.normal(0, 1.0, size=n)
    series = base + seasonal + noise
    da = _make_cube(series.reshape(n, 1, 1))
    res = analyze_grid(da, investigation_id="INV-001", config={"min_months": 9, "min_years": 10, "ok_years": 15, "alpha": 0.05})
    assert res["status"] == "completed"
    cell = res["cells"][0]
    assert cell["classification"] in {"significant_increase", "inconclusive", "no_significant_trend"} or cell["classification"] == "significant_increase"
    # strong trend should be detected as increasing/significant in this controlled case
    assert cell["trend_direction"] == "increasing"
    assert cell["sens_slope"]["value"] is not None and cell["sens_slope"]["value"] > 0
    assert cell["classification"] == "significant_increase"


def test_detects_strong_decreasing_trend():
    rng = np.random.default_rng(7)
    n = 240
    years_idx = np.arange(n) / 12.0
    base = 80.0 - 0.4 * years_idx
    seasonal = 8.0 * np.sin(2 * np.pi * np.arange(n) / 12.0)
    noise = rng.normal(0, 1.0, size=n)
    series = base + seasonal + noise
    da = _make_cube(series.reshape(n, 1, 1))
    res = analyze_grid(da, config={"min_months": 9, "min_years": 10, "alpha": 0.05})
    cell = res["cells"][0]
    assert cell["trend_direction"] == "decreasing"
    assert cell["sens_slope"]["value"] < 0
    assert cell["classification"] == "significant_decrease"


def test_no_significant_trend_for_noise():
    rng = np.random.default_rng(123)
    n = 240
    seasonal = 5.0 * np.sin(2 * np.pi * np.arange(n) / 12.0)
    noise = rng.normal(0, 3.0, size=n)
    series = 50.0 + seasonal + noise
    da = _make_cube(series.reshape(n, 1, 1))
    res = analyze_grid(da, config={"min_months": 9, "min_years": 10, "alpha": 0.05})
    cell = res["cells"][0]
    assert cell["classification"] in {"no_significant_trend", "inconclusive"}
    # should not be classified as significant increase/decrease in typical noise case
    assert cell["classification"] not in {"significant_increase", "significant_decrease"}


def test_insufficient_data_no_trend_assigned():
    # only 5 years -> below min_years default 10
    n = 60
    series = 50.0 + 0.5 * (np.arange(n) / 12.0)
    da = _make_cube(series.reshape(n, 1, 1))
    res = analyze_grid(da, config={"min_months": 9, "min_years": 10})
    cell = res["cells"][0]
    assert cell["classification"] == "insufficient_data"
    assert cell["sens_slope"] is None
    assert cell["mann_kendall"] is None
    assert cell["trend_direction"] is None
    assert cell["significant_fdr"] is False


def test_missing_data_not_treated_as_zero():
    rng = np.random.default_rng(99)
    n = 240
    years_idx = np.arange(n) / 12.0
    series = 60.0 + 0.3 * years_idx + rng.normal(0, 1.0, size=n)
    # inject many NaNs but leave enough valid annual points
    series[::5] = np.nan  # 20% missing scattered
    da = _make_cube(series.reshape(n, 1, 1))
    res = analyze_grid(da, config={"min_months": 6, "min_years": 10, "alpha": 0.05})
    cell = res["cells"][0]
    # trend should still be positive/increasing based on valid data, not driven by zeros
    assert cell["trend_direction"] == "increasing"
    assert cell["sens_slope"]["value"] > 0
    # completeness/observations reflect missingness
    assert cell["n_observations"] < n


def test_fdr_excludes_nonfinite_pvalues():
    p = np.array([0.01, np.nan, 0.5, np.inf, 0.001])
    sig = fdr_significance_mask(p, alpha=0.05)
    assert sig.shape == p.shape
    assert sig[1] == False
    assert sig[3] == False
    # finite small p-values may be significant depending on correction
    assert sig.dtype == bool


def test_classify_cell_covers_all_required_classes():
    # significant increase/decrease
    assert fdr_significance_mask(np.array([0.01]), alpha=0.05)[0] in {True, False}
    from scientific_engine.reliability import classify_cell

    assert classify_cell(sufficient=True, fdr_significant=True, direction="increasing", flags=[], completeness=1.0) == "significant_increase"
    assert classify_cell(sufficient=True, fdr_significant=True, direction="decreasing", flags=[], completeness=1.0) == "significant_decrease"
    # no significant trend (not "stable")
    assert classify_cell(sufficient=True, fdr_significant=False, direction="increasing", flags=[], completeness=1.0) == "no_significant_trend"
    # insufficient data
    assert classify_cell(sufficient=False, fdr_significant=False, direction=None, flags=["insufficient_data"], completeness=0.2) == "insufficient_data"
    assert classify_cell(sufficient=True, fdr_significant=False, direction="increasing", flags=[], completeness=0.1, min_completeness=0.5) == "insufficient_data"
    # inconclusive
    assert classify_cell(sufficient=True, fdr_significant=False, direction="increasing", flags=["inconclusive"], completeness=1.0) == "inconclusive"
    assert classify_cell(sufficient=True, fdr_significant=False, direction="increasing", flags=["mann_kendall_failed"], completeness=1.0) == "inconclusive"


def test_trend_constant_series_is_no_trend():
    from scientific_engine.trend import compute_trend
    years = np.arange(2000, 2020)
    values = np.full_like(years, 50.0, dtype=float)
    tr = compute_trend(years, values, min_years=10)
    assert tr.sufficient is True
    assert tr.direction == "no_trend"
    assert tr.slope_per_year == 0.0
    assert tr.p_value == 1.0
    assert "insufficient_data" not in tr.flags


def test_analysis_output_includes_reproducibility_metadata_and_is_deterministic():
    rng = np.random.default_rng(2026)
    n = 240
    years_idx = np.arange(n) / 12.0
    series = 60.0 + 0.2 * years_idx + 5.0 * np.sin(2 * np.pi * np.arange(n) / 12.0) + rng.normal(0, 0.5, size=n)
    da = _make_cube(series.reshape(n, 1, 1))
    req = {
        "investigation_id": "INV-001",
        "bounds": {"min_lon": 36.0, "min_lat": -1.0, "max_lon": 37.0, "max_lat": 1.0},
        "period": {"start": "2001-01-01", "end": "2020-12-31"},
        "config": {"min_months": 9, "min_years": 10, "ok_years": 15, "alpha": 0.05},
        "dataset_meta": {"short_name": "GPM_3IMERGM", "version": "07", "retrieved_at": "2026-11-20T00:00:00Z"},
    }
    r1 = analyze_grid(da, **req)
    r2 = analyze_grid(da, **req)
    assert r1["status"] == "completed"
    meta = r1["run_metadata"]
    for key in ["contract", "version", "methods", "parameters", "dataset", "bounds", "period", "generated_at", "engine_version", "grid"]:
        assert key in meta
    assert meta["investigation_id"] == "INV-001"
    assert meta["parameters"]["min_months"] == 9
    assert meta["parameters"]["alpha"] == 0.05
    assert meta["dataset"]["short_name"] == "GPM_3IMERGM"
    assert meta["dataset"]["retrieved_at"] == "2026-11-20T00:00:00Z"
    # determinism (exclude generated_at timestamp)
    m1 = {k: v for k, v in r1["run_metadata"].items() if k != "generated_at"}
    m2 = {k: v for k, v in r2["run_metadata"].items() if k != "generated_at"}
    assert m1 == m2
    assert r1["cells"] == r2["cells"]
    assert r1["summary"] == r2["summary"]


def test_trend_statistics_match_independent_reference_implementations():
    """Reference comparison against independent library implementations (SciPy/pymannkendall)."""
    import pymannkendall as mk
    from scipy.stats import theilslopes
    from scientific_engine.trend import compute_trend

    years = np.arange(2001, 2021, dtype=float)
    values = 10.0 + 0.35 * (years - years[0]) + np.array([
        0.2, -0.1, 0.0, 0.3, -0.2, 0.1, 0.0, -0.1, 0.2, 0.0,
        0.1, -0.2, 0.0, 0.2, -0.1, 0.0, 0.1, -0.1, 0.2, 0.0,
    ])
    tr = compute_trend(years, values, min_years=10)
    assert tr.sufficient is True
    ref_ts = theilslopes(values, years, alpha=0.95)
    ref_mk = mk.hamed_rao_modification_test(values)
    assert tr.slope_per_year is not None and np.isclose(tr.slope_per_year, float(ref_ts.slope), atol=1e-12)
    assert tr.ci_lower is not None and np.isclose(tr.ci_lower, float(ref_ts.low_slope), atol=1e-12)
    assert tr.ci_upper is not None and np.isclose(tr.ci_upper, float(ref_ts.high_slope), atol=1e-12)
    assert tr.p_value is not None and np.isclose(tr.p_value, float(ref_mk.p), atol=1e-12)
    assert tr.mk_tau is not None and np.isclose(tr.mk_tau, float(getattr(ref_mk, "Tau")), atol=1e-12)
    assert tr.direction == "increasing"


def test_trend_handles_ties_and_missing_values():
    from scientific_engine.trend import compute_trend
    years = np.arange(2000, 2020, dtype=float)
    values = np.array([
        10.0, 10.0, 10.0, 10.5, 10.5, np.nan, 11.0, 11.0, 11.0, 11.5,
        11.5, 12.0, np.nan, 12.0, 12.5, 12.5, 13.0, 13.0, 13.5, 13.5,
    ])
    tr = compute_trend(years, values, min_years=10)
    assert tr.sufficient is True
    assert tr.n_years == int(np.isfinite(values).sum())
    assert tr.p_value is not None and np.isfinite(tr.p_value)
    assert tr.slope_per_year is not None and tr.slope_per_year >= 0
    # ties/missing must not be treated as zero; result should indicate non-decreasing/increasing tendency
    assert tr.direction in {"increasing", "no_trend"}

