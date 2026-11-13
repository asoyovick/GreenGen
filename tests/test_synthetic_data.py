"""Tests for the clearly-fake synthetic data generator."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from scripts.make_synthetic_data import generate_cube, land_mask, target_lat_lon
from src.common.config import REPO_ROOT, load_app_config

LAT, LON = target_lat_lon(0.5)


@pytest.fixture(scope="module")
def cfg():
    return load_app_config()


def test_land_mask_known_places():
    mask = land_mask(LAT, LON, 0.5)

    def at(lat: float, lon: float) -> bool:
        return bool(mask[np.argmin(abs(LAT - lat)), np.argmin(abs(LON - lon))])

    assert at(-1.25, 36.75), "Nairobi should be land"
    assert at(-3.0, -60.0), "Amazon should be land"
    assert at(23.0, 10.0), "Sahara should be land"
    assert at(-80.0, 0.0), "Antarctica should be land"
    assert not at(0.0, -150.0), "central Pacific should be ocean"
    assert not at(30.0, -40.0), "Atlantic should be ocean"
    assert 0.25 < mask.mean() < 0.40


def test_cubes_have_contract_and_synthetic_flag(cfg):
    lat = LAT[(LAT >= 40) & (LAT <= 65)]
    lon = LON[(LON >= 35) & (LON <= 105)]
    times = pd.date_range("2002-01-01", "2024-12-01", freq="MS")
    for var in cfg.mode_variables("synthetic"):
        da = generate_cube(var, cfg, lat=lat, lon=lon, times=times)
        assert da.dims == ("time", "lat", "lon")
        assert da.shape == (276, len(lat), len(lon))
        assert da.attrs["synthetic"] is True
        assert "synthetic demo data" in da.attrs["source"].lower()
        assert np.isfinite(da.values).any()


def test_vegetation_is_nan_over_ocean(cfg):
    # Mid-Pacific box
    lat = LAT[(LAT >= -10) & (LAT <= 10)]
    lon = LON[(LON >= -170) & (LON <= -140)]
    times = pd.date_range("2002-01-01", "2011-12-01", freq="MS")
    da = generate_cube("vegetation", cfg, lat=lat, lon=lon, times=times)
    assert np.isnan(da.values).all()
    assert da.attrs["surface"] == "land"


def test_opposite_trend_boxes_move_apart(cfg):
    lat = LAT[(LAT >= 42) & (LAT <= 63)]
    lon = LON[(LON >= 35) & (LON <= 105)]
    times = pd.date_range("2002-01-01", "2024-12-01", freq="MS")
    for var in ("vegetation", "precipitation"):
        da = generate_cube(var, cfg, lat=lat, lon=lon, times=times)
        # Annual means remove the synthetic seasonal cycle.
        annual = da.groupby("time.year").mean("time")
        west = annual.sel(lat=slice(48, 58), lon=slice(45, 65)).mean(["lat", "lon"])
        east = annual.sel(lat=slice(48, 58), lon=slice(75, 95)).mean(["lat", "lon"])
        west_change = float(west.isel(year=-1) - west.isel(year=0))
        east_change = float(east.isel(year=-1) - east.isel(year=0))
        assert west_change > 0, f"{var} west box should increase, got {west_change}"
        assert east_change < 0, f"{var} east box should decrease, got {east_change}"


def test_cli_writes_manifest_and_cubes(tmp_path):
    out = tmp_path / "synthetic"
    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "make_synthetic_data.py"),
        "--out",
        str(out),
        "--lat-range",
        "40",
        "60",
        "--lon-range",
        "40",
        "100",
        "--start",
        "2002-01",
        "--end",
        "2012-12",
    ]
    proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    assert proc.returncode == 0, proc.stderr
    manifest = json.loads((out / "manifest.json").read_text())
    assert manifest["synthetic"] is True
    assert manifest["grid"]["n_lat"] == 40
    assert set(manifest["variables"]) == {"precipitation", "vegetation", "temperature"}
    for var in manifest["variables"]:
        assert (out / f"{var}.zarr").exists()
    assert "not real observations" in manifest["warning"].lower()
