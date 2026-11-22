"""Data integration and grid-alignment tests (Issues #33, #52).

IMPORTANT: All fixtures in this file are SYNTHETIC, programmatically generated
test data used only for isolated software tests. They are NOT NASA observations
and must never be presented as real scientific results.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from scientific_engine.grid_analysis import analyze_grid
from scientific_engine.io import load_observation


SYNTHETIC_ATTRS = {
    "synthetic": True,
    "source": "SYNTHETIC TEST FIXTURE - not NASA observations",
}


def _make_synthetic_monthly_da(*, n_years=20, lats=None, lons=None, seed=0):
    # SYNTHETIC TEST FIXTURE - not NASA observations
    rng = np.random.default_rng(seed)
    periods = n_years * 12
    t = pd.date_range("2001-01-01", periods=periods, freq="MS")
    if lats is None:
        lats = np.array([-1.0, -0.9], dtype=float)  # 0.1 degree spacing
    if lons is None:
        lons = np.array([36.8, 36.9], dtype=float)
    base = 60.0
    trend = 0.05 * (np.arange(periods) / 12.0)[:, None, None]
    seasonal = 10.0 * np.sin(2 * np.pi * np.arange(periods) / 12.0)[:, None, None]
    noise = rng.normal(0, 1.0, size=(periods, len(lats), len(lons)))
    vals = base + trend + seasonal + noise
    da = xr.DataArray(
        vals,
        coords={"time": t, "lat": lats, "lon": lons},
        dims=("time", "lat", "lon"),
        name="precipitation",
        attrs={"units": "mm/month", **SYNTHETIC_ATTRS},
    )
    return da


def test_grid_alignment_preserves_native_coordinates():
    # SYNTHETIC fixture with explicit 0.1 degree native-like grid
    da = _make_synthetic_monthly_da(lats=np.array([-1.3, -1.2, -1.1]), lons=np.array([36.7, 36.8, 36.9]))
    res = analyze_grid(da, config={"min_months": 9, "min_years": 10})
    cells = res["cells"]
    lats = sorted({c["lat"] for c in cells})
    lons = sorted({c["lon"] for c in cells})
    assert lats == [-1.3, -1.2, -1.1]
    assert lons == [36.7, 36.8, 36.9]
    # No resampling: one cell per input grid point
    assert len(cells) == 9
    assert res["run_metadata"]["grid"]["n_lat"] == 3
    assert res["run_metadata"]["grid"]["n_lon"] == 3


def test_subsetting_matches_source_coordinates_and_values():
    # SYNTHETIC fixture
    da = _make_synthetic_monthly_da(
        lats=np.array([-1.2, -1.1, -1.0, -0.9]),
        lons=np.array([36.7, 36.8, 36.9, 37.0]),
    )
    bounds = {"min_lon": 36.8, "min_lat": -1.1, "max_lon": 36.9, "max_lat": -1.0}
    period = {"start": "2005-01-01", "end": "2015-12-31"}
    res = analyze_grid(da, bounds=bounds, period=period, config={"min_months": 9, "min_years": 5})
    cells = res["cells"]
    assert sorted({c["lat"] for c in cells}) == [-1.1, -1.0]
    assert sorted({c["lon"] for c in cells}) == [36.8, 36.9]
    assert res["run_metadata"]["bounds"] == bounds
    assert res["run_metadata"]["period"] == period

    # Independent check: mean over selected subset matches source subset mean
    src_sub = da.sel(lat=slice(-1.1, -1.0), lon=slice(36.8, 36.9), time=slice(period["start"], period["end"]))
    for c in cells:
        src_cell = src_sub.sel(lat=c["lat"], lon=c["lon"])
        expected = float(np.nanmean(src_cell.values))
        got = c["mean"]["value"]
        assert got is not None
        assert np.isclose(got, expected, atol=1e-6)


def test_missing_values_and_quality_flags_handled_transparently():
    # SYNTHETIC fixture with explicit missing values
    da = _make_synthetic_monthly_da(n_years=20)
    vals = da.values.copy()
    vals[:24, 0, 0] = np.nan  # missing first 2 years for one cell
    vals[::7, 0, 1] = np.nan   # scattered missing
    da2 = da.copy(data=vals)
    res = analyze_grid(da2, config={"min_months": 9, "min_years": 10})
    by_coord = {(c["lat"], c["lon"]): c for c in res["cells"]}
    c_missing = by_coord[(da["lat"].values[0], da["lon"].values[0])]
    c_scattered = by_coord[(da["lat"].values[0], da["lon"].values[1])]
    assert c_missing["n_observations"] < 240
    assert c_scattered["n_observations"] < 240
    # Missing never becomes zero; means should remain in plausible range
    assert c_missing["mean"]["value"] > 40
    assert c_scattered["mean"]["value"] > 40


def test_insufficient_data_when_completeness_too_low():
    # SYNTHETIC fixture: mostly missing
    da = _make_synthetic_monthly_da(n_years=20)
    vals = da.values.copy()
    vals[:, 0, 0] = np.nan
    vals[:200, 0, 0] = 50.0  # only ~16-17 years worth scattered? make insufficient by year completeness
    # easier: leave only 5 valid years
    vals[:, 0, 0] = np.nan
    vals[:60, 0, 0] = 50.0
    da2 = da.copy(data=vals)
    res = analyze_grid(da2, config={"min_months": 9, "min_years": 10})
    c = res["cells"][0]
    assert c["classification"] == "insufficient_data"


def test_load_observation_rejects_synthetic_marked_dataset(tmp_path: Path):
    # SYNTHETIC fixture written to disk only to test guardrail
    da = _make_synthetic_monthly_da(n_years=2)
    ds = da.to_dataset(name="precipitation")
    ds.attrs["synthetic"] = True
    path = tmp_path / "synthetic_fixture.zarr"
    try:
        ds.to_zarr(path, mode="w")
    except Exception as e:
        pytest.skip(f"zarr engine unavailable in test env: {e}")
    with pytest.raises(ValueError, match="Synthetic data is not permitted"):
        load_observation(str(path), variable="precipitation")


def test_load_observation_missing_file_fails_explicitly():
    with pytest.raises(FileNotFoundError):
        load_observation("/tmp/does-not-exist-greengen.nc")


def test_load_observation_rejects_unsupported_format(tmp_path: Path):
    p = tmp_path / "data.csv"
    p.write_text("a,b\n1,2\n")
    with pytest.raises(ValueError, match="Unsupported observation format"):
        load_observation(str(p))
