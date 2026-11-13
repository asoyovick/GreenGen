"""Pytest fixtures: a tiny, fully controlled layer set for API tests."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import xarray as xr
from fastapi.testclient import TestClient

from src.common.config import load_app_config

LAT = np.array([-10.0, -5.0, 0.0, 5.0, 10.0, 40.0, 45.0, 50.0, 55.0, 60.0, 80.0])
LON = np.array([-160.0, -150.0, -140.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0,
                80.0, 85.0, 90.0, 95.0, 100.0, 170.0])
YEARS = np.arange(2002, 2025)
META = {
    "precipitation": {
        "display_name": "Precipitation", "units": "mm/month", "surface": "land,ocean",
        "model_based": False, "source_dataset": "SYNTHETIC", "dataset_version": "test",
        "doi": "n/a (test)",
    },
    "vegetation": {
        "display_name": "Vegetation greenness (NDVI)", "units": "NDVI", "surface": "land",
        "model_based": False, "source_dataset": "SYNTHETIC", "dataset_version": "test",
        "doi": "n/a (test)",
    },
    "temperature": {
        "display_name": "Air temperature at 2 m", "units": "degC", "surface": "land,ocean",
        "model_based": True, "source_dataset": "SYNTHETIC", "dataset_version": "test",
        "doi": "n/a (test)",
    },
}
SLOPES = {
    "precipitation": 0.25,   # per year in the planted boxes
    "vegetation": 0.004,
    "temperature": 0.06,
}
STD = {"precipitation": 1.0, "vegetation": 3.0, "temperature": 2.0}


def _grid():
    lat2, lon2 = np.meshgrid(LAT, LON, indexing="ij")
    land = (lat2 >= 40) & (lat2 <= 60) & (lon2 >= 40) & (lon2 <= 100)
    no_data = (lat2 == 80) & (lon2 == 170)
    west = (lat2 >= 45) & (lat2 <= 60) & (lon2 >= 40) & (lon2 <= 70)
    east = (lat2 >= 45) & (lat2 <= 60) & (lon2 > 70) & (lon2 <= 100)
    return lat2, lon2, land, no_data, west, east


def _layer(key: str) -> xr.Dataset:
    lat2, lon2, land, no_data, west, east = _grid()
    applies = ~no_data
    if key == "vegetation":
        applies &= land
    slope = np.zeros_like(lat2, dtype=float)
    if key == "temperature":
        slope[:] = SLOPES[key]
    else:
        slope[west] = SLOPES[key]
        slope[east] = -SLOPES[key]
    slope[~applies] = np.nan
    cls = np.where(np.isfinite(slope) & (slope > 0), 1.0, np.where(np.isfinite(slope) & (slope < 0), -1.0, 0.0))
    cls[~applies] = np.nan
    sig = np.isfinite(cls) & (cls != 0)
    std = np.where(sig, np.sign(slope) * STD[key], np.where(np.isfinite(slope), 0.0, np.nan))
    anomaly = np.empty((len(YEARS), len(LAT), len(LON)), dtype=float)
    for i, year in enumerate(YEARS):
        anomaly[i] = slope * (year - YEARS[0]) + 0.001 * np.sin(year + lon2)
    anomaly[:, ~applies] = np.nan
    attrs = {
        "variable": key,
        **META[key],
        "synthetic": True,
        "period_start": "2002-01",
        "period_end": "2024-12",
        "min_years": 10,
        "ok_years": 15,
        "alpha": 0.05,
        "source": "test fixture; SYNTHETIC DEMO DATA",
        "missing_months": "",
    }
    return xr.Dataset(
        {
            "slope_per_year": (("lat", "lon"), slope),
            "slope_per_decade": (("lat", "lon"), slope * 10),
            "p_value": (("lat", "lon"), np.where(np.isfinite(slope), 0.01, np.nan)),
            "significant": (("lat", "lon"), sig),
            "class": (("lat", "lon"), cls),
            "std_trend": (("lat", "lon"), std),
            "n_years": (("lat", "lon"), np.where(np.isfinite(slope), 23.0, 0.0)),
            "low_confidence": (("lat", "lon"), np.zeros(lat2.shape, dtype=bool)),
            "annual_anomaly": (("year", "lat", "lon"), anomaly),
        },
        coords={"lat": LAT, "lon": LON, "year": YEARS},
        attrs=attrs,
    )


@pytest.fixture(scope="session")
def layer_dirs(tmp_path_factory):
    root = tmp_path_factory.mktemp("api_layers")
    layers = root / "layers"
    layers.mkdir()
    for key in META:
        _layer(key).to_zarr(layers / f"{key}_trend.zarr", mode="w")
    overlays_root = root / "overlays"
    from scripts.export_overlays import export_mode
    cfg = load_app_config()
    export_mode(cfg, layers_dir=layers, out_dir=overlays_root / "synthetic", only=set(META))
    return layers, overlays_root


@pytest.fixture()
def client(layer_dirs):
    from src.api.main import create_app
    layers, overlays_root = layer_dirs
    app = create_app(load_app_config(), layers_dir=layers, overlays_root=overlays_root)
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def empty_client(tmp_path):
    from src.api.main import create_app
    app = create_app(
        load_app_config(),
        layers_dir=tmp_path / "no_layers",
        overlays_root=tmp_path / "no_overlays",
    )
    with TestClient(app) as c:
        yield c
