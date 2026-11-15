"""Overlay export tests: Mercator rows, colours, metadata, and transparency."""
from __future__ import annotations

import json

import numpy as np
import xarray as xr
from PIL import Image

from scripts.export_overlays import (
    BLUE,
    ORANGE,
    class_rgba,
    export_mode,
    inverse_mercator_y,
    mercator_y,
    resample_to_mercator,
    std_trend_rgba,
)
from src.common.config import load_app_config


def test_mercator_round_trip_and_resample_shape():
    lat = np.arange(87.5, -90, -5.0)
    data = np.repeat(lat[:, None], 4, axis=1)
    out = resample_to_mercator(data, lat, height=100, lat_limit=85.0)
    assert out.shape == (100, 4)
    # Top row is near +85, bottom near -85, and ordering is monotonic.
    assert abs(out[0, 0] - 85) < 3
    assert abs(out[-1, 0] + 85) < 3
    assert np.all(np.diff(out[:, 0]) <= 0)
    assert out[0, 0] > out[-1, 0]
    assert abs(float(inverse_mercator_y(mercator_y(23.5))) - 23.5) < 1e-9


def test_class_colours_and_transparency():
    classes = np.array([[1.0, -1.0, 0.0], [np.nan, 1.0, 0.0]])
    rgba = class_rgba(classes)
    assert tuple(rgba[0, 0, :3]) == tuple(BLUE.astype(np.uint8))
    assert tuple(rgba[0, 1, :3]) == tuple(ORANGE.astype(np.uint8))
    assert rgba[0, 2, 3] == 0
    assert rgba[1, 0, 3] == 0
    assert rgba[0, 0, 3] > 0


def test_std_trend_is_diverging_and_zero_is_transparent():
    std = np.array([[-3.0, -1.0, 0.0, 1.0, 3.0, np.nan]])
    rgba = std_trend_rgba(std)
    assert tuple(rgba[0, 0, :3]) == tuple(ORANGE.astype(np.uint8))
    assert tuple(rgba[0, 4, :3]) == tuple(BLUE.astype(np.uint8))
    assert rgba[0, 2, 3] == 0
    assert rgba[0, 5, 3] == 0
    assert rgba[0, 3, 3] < rgba[0, 4, 3]


def _write_layer(path, lat, lon, classes, attrs):
    std = np.where(np.isfinite(classes), classes * 2.0, np.nan)
    ds = xr.Dataset(
        {
            "class": (("lat", "lon"), classes),
            "std_trend": (("lat", "lon"), std),
            "slope_per_decade": (("lat", "lon"), std),
            "significant": (("lat", "lon"), np.isfinite(classes) & (classes != 0)),
            "n_years": (("lat", "lon"), np.full(classes.shape, 23.0)),
            "low_confidence": (("lat", "lon"), np.zeros(classes.shape, dtype=bool)),
        },
        coords={"lat": lat, "lon": lon},
        attrs={
            "variable": "precipitation",
            "units": "mm/month",
            "display_name": "Precipitation",
            "synthetic": True,
            "model_based": False,
            "surface": "land,ocean",
            "period_start": "2002-01",
            "period_end": "2024-12",
            "min_years": 10,
            "ok_years": 15,
            "alpha": 0.05,
            "source": "SYNTHETIC DEMO DATA",
        },
    )
    ds.to_zarr(path, mode="w")


def test_export_mode_writes_pngs_and_metadata(tmp_path):
    lat = np.array([60.0, 30.0, 0.0, -30.0])
    lon = np.array([-120.0, -60.0, 0.0, 60.0, 120.0, 180.0])
    classes = np.array([
        [1, 1, 0, -1, 0, np.nan],
        [0, 1, 0, -1, 0, np.nan],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, -1, 0],
    ], dtype=float)
    layers = tmp_path / "layers"
    layers.mkdir()
    _write_layer(layers / "precipitation_trend.zarr", lat, lon, classes, {})

    cfg = load_app_config()
    out = tmp_path / "overlays"
    meta = export_mode(cfg, layers_dir=layers, out_dir=out, only={"precipitation"})

    assert meta["synthetic"] is True
    assert meta["bounds"] == [-180.0, -85.0, 180.0, 85.0]
    assert meta["default_layer"] == "change_score"
    assert set(meta["layers"]) == {"change_score", "precipitation_class", "precipitation_std_trend"}
    class_meta = meta["layers"]["precipitation_class"]
    assert class_meta["bounds"] == meta["bounds"]
    assert class_meta["units"] == "mm/month"
    assert class_meta["legend"][0]["label"] == "Significant increase"

    for name in ("change_score", "precipitation_class", "precipitation_std_trend"):
        image = Image.open(out / f"{name}.png")
        assert image.size == (6, 720)
        assert image.mode == "RGBA"

    rgba = np.array(Image.open(out / "precipitation_class.png"))
    unique = {tuple(px) for px in rgba.reshape(-1, 4)}
    assert tuple(BLUE.astype(np.uint8)) + (225,) in unique
    assert tuple(ORANGE.astype(np.uint8)) + (225,) in unique
    assert (0, 0, 0, 0) in unique

    saved = json.loads((out / "metadata.json").read_text())
    assert saved["mode"] == "synthetic"
    assert saved["layers"]["change_score"]["legend"][0]["count"] == 0
