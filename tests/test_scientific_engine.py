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
