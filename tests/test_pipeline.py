"""Pipeline integration tests: real skill scripts, synthetic data, known trends."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from src.common.config import REPO_ROOT
from src.skills.compute_trends import anomalies_annual

sys.path.insert(0, str(REPO_ROOT / "scripts"))
from make_synthetic_data import target_lat_lon  # noqa: E402


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise AssertionError(f"command failed: {' '.join(cmd)}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")
    return proc


def make_subset(tmp_path: Path, *, lat=(40, 60), lon=(40, 100), start="2002-01", end="2024-12") -> Path:
    out = tmp_path / "synthetic"
    run([
        sys.executable, str(REPO_ROOT / "scripts" / "make_synthetic_data.py"),
        "--out", str(out),
        "--lat-range", str(lat[0]), str(lat[1]),
        "--lon-range", str(lon[0]), str(lon[1]),
        "--start", start, "--end", end,
    ])
    return out


def prep(tmp_path: Path, synth: Path, var: str, *, meta: list[str] | None = None) -> Path:
    cube = tmp_path / "cache" / f"{var}.zarr"
    cmd = [
        sys.executable, str(REPO_ROOT / "src" / "skills" / "prep_cube.py"),
        "--inputs", str(synth / f"{var}.zarr"),
        "--variable", var,
        "--out", str(cube),
        "--res", "0.5",
        "--start", "2002-01", "--end", "2024-12",
    ]
    for item in meta or ["synthetic=true"]:
        cmd += ["--meta", item]
    run(cmd)
    return cube


def trends(tmp_path: Path, cube: Path, var: str, *, jobs: int = 2, ok_years: int = 15) -> xr.Dataset:
    out = tmp_path / "layers" / f"{var}_trend.zarr"
    run([
        sys.executable, str(REPO_ROOT / "src" / "skills" / "compute_trends.py"),
        "--cube", str(cube),
        "--variable", var,
        "--out", str(out),
        "--min-years", "10",
        "--ok-years", str(ok_years),
        "--alpha", "0.05",
        "--jobs", str(jobs),
    ])
    return xr.open_zarr(out).load()


def test_annual_anomalies_remove_seasonal_cycle():
    lat, lon = target_lat_lon(5.0)
    times = pd.date_range("2002-01-01", "2020-12-01", freq="MS")
    month = times.month.to_numpy()
    seasonal = np.cos(2 * np.pi * (month[:, None, None] - 7) / 12) * 8.0
    data = np.broadcast_to(seasonal, (len(times), len(lat), len(lon))).copy()
    da = xr.DataArray(data, coords={"time": times, "lat": lat, "lon": lon}, dims=("time", "lat", "lon"))
    annual = anomalies_annual(da, min_months=9)
    assert annual.dims == ("year", "lat", "lon")
    assert np.nanmax(np.abs(annual.values)) < 1e-6
    # Drop 4 months of 2010 -> that year must be a gap, not interpolated.
    partial = da.where(~((da.time.dt.year == 2010) & (da.time.dt.month <= 4)))
    annual_partial = anomalies_annual(partial, min_months=9)
    assert bool(np.isnan(annual_partial.sel(year=2010)).all())
    assert bool(np.isfinite(annual_partial.sel(year=2011)).all())


def test_pipeline_recovers_planted_trends_and_nan(tmp_path):
    synth = make_subset(tmp_path)
    cube = prep(tmp_path, synth, "precipitation", meta=["synthetic=true", "units=mm/month"])
    layer = trends(tmp_path, cube, "precipitation")

    west = layer.sel(lat=slice(48, 58), lon=slice(45, 65))
    east = layer.sel(lat=slice(48, 58), lon=slice(75, 95))
    no_trend = layer.sel(lat=slice(40.25, 43.75), lon=slice(45, 65))

    west_slope = float(west["slope_per_year"].median())
    east_slope = float(east["slope_per_year"].median())
    assert west_slope == pytest.approx(0.25, abs=0.03), west_slope
    assert east_slope == pytest.approx(-0.25, abs=0.03), east_slope
    assert float(west["significant"].mean()) > 0.8
    assert float(east["significant"].mean()) > 0.8
    # The planted opposite-trend regions must both appear in the class layer.
    assert int((west["class"] == 1).sum()) > 0
    assert int((east["class"] == -1).sum()) > 0
    # FDR keeps the null-region false-positive share modest (not zero, by design).
    assert float(no_trend["significant"].mean()) < 0.2
    assert layer.attrs["synthetic"] is True
    assert layer.attrs["units"] == "mm/month"
    assert layer.attrs["method"].startswith("anomalies; annual means; Theil-Sen")


def test_vegetation_ocean_cells_stay_nan(tmp_path):
    lat, lon = target_lat_lon(0.5)
    lat = lat[(lat >= -10) & (lat <= 10)]
    lon = lon[(lon >= -170) & (lon <= -140)]
    synth = tmp_path / "ocean_synth"
    run([
        sys.executable, str(REPO_ROOT / "scripts" / "make_synthetic_data.py"),
        "--out", str(synth),
        "--lat-range", str(lat.min()), str(lat.max()),
        "--lon-range", str(lon.min()), str(lon.max()),
        "--start", "2002-01", "--end", "2024-12",
    ])
    cube = prep(tmp_path, synth, "vegetation")
    layer = trends(tmp_path, cube, "vegetation")
    assert bool(np.isnan(layer["slope_per_year"]).all())
    assert bool(np.isnan(layer["class"]).all())
    assert bool(np.isnan(layer["p_value"]).all())


def test_prep_reports_missing_months_without_filling(tmp_path):
    lat, lon = target_lat_lon(5.0)
    times = pd.date_range("2002-01-01", "2012-12-01", freq="MS")
    rng = np.random.default_rng(3)
    data = rng.normal(10, 2, (len(times), len(lat), len(lon)))
    da = xr.DataArray(
        data, coords={"time": times, "lat": lat, "lon": lon},
        dims=("time", "lat", "lon"), name="precipitation",
        attrs={"units": "mm/month", "synthetic": True},
    )
    da = da.drop_sel(time="2005-06")
    cube_in = tmp_path / "with_gap.zarr"
    da.to_dataset().to_zarr(cube_in, mode="w")
    out = tmp_path / "cache" / "gap_precip.zarr"
    run([
        sys.executable, str(REPO_ROOT / "src" / "skills" / "prep_cube.py"),
        "--inputs", str(cube_in),
        "--variable", "precipitation",
        "--out", str(out),
        "--res", "5.0",
        "--start", "2002-01", "--end", "2012-12",
        "--meta", "synthetic=true",
    ])
    ds = xr.open_zarr(out)
    assert ds.sizes["time"] == len(times) - 1
    assert "2005-06" in ds["precipitation"].attrs["missing_months"]
    assert bool(np.isnan(ds["precipitation"].sel(time="2005-06")).all())


def test_low_confidence_flag_for_short_record(tmp_path):
    synth = make_subset(tmp_path, start="2002-01", end="2012-12")
    cube = prep(tmp_path, synth, "temperature")
    layer = trends(tmp_path, cube, "temperature", ok_years=15)
    valid = layer["low_confidence"].where(layer["slope_per_year"].notnull())
    assert float(valid.mean()) == 1.0
    assert layer.attrs["ok_years"] == 15
