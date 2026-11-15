"""Focused quality tests for the scientific helpers and report wording."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from src.skills.change_report import build_report, nearby_sentence, sentence
from src.skills.compute_trends import fdr_significant
from src.skills.prep_cube import convert_units, standardize_coords


# --------------------------------------------------------------------- units
def test_temperature_unit_conversion():
    da = xr.DataArray([273.15, 283.15], dims=("x",), attrs={"units": "K"})
    out = convert_units(da, "k_to_c")
    np.testing.assert_allclose(out.values, [0.0, 10.0])
    assert out.attrs["units"] == "degC"


def test_precipitation_rate_conversion_uses_days_in_month():
    times = pd.to_datetime(["2021-02-01", "2021-04-01"])
    da = xr.DataArray(
        [1.0, 1.0], coords={"time": times}, dims=("time",), attrs={"units": "mm/hr"}
    )
    out = convert_units(da, "mm_per_hr_to_mm_per_month")
    # February 2021 has 28 days; April has 30.
    np.testing.assert_allclose(out.values, [1.0 * 24 * 28, 1.0 * 24 * 30])
    assert out.attrs["units"] == "mm/month"


def test_scale_conversion_preserves_attrs():
    da = xr.DataArray([1.0, -2.0], dims=("x",), attrs={"units": "NDVI", "synthetic": True})
    out = convert_units(da, "scale:0.0001")
    np.testing.assert_allclose(out.values, [0.0001, -0.0002])
    assert out.attrs["units"] == "NDVI"
    assert out.attrs["synthetic"] is True


def test_unknown_unit_operation_is_rejected():
    with pytest.raises(ValueError, match="Unknown --units op"):
        convert_units(xr.DataArray([1.0], dims=("x",)), "furlongs_to_metres")


# ------------------------------------------------------------- coordinates
def test_longitude_is_normalized_and_sorted():
    lon = [0.0, 90.0, 180.0, 270.0]
    da = xr.DataArray(
        np.arange(4.0).reshape(1, 4),
        coords={"lat": [0.0], "lon": lon},
        dims=("lat", "lon"),
    )
    ds = standardize_coords(da.to_dataset(name="value"))
    assert list(ds["lon"].values) == [-180.0, -90.0, 0.0, 90.0]
    # The value stored at 270 E must move with its coordinate to 90 W.
    assert float(ds["value"].sel(lat=0, lon=-90)) == 3.0


def test_latitude_names_are_standardized_and_sorted():
    ds = xr.Dataset(
        {"value": (("latitude", "longitude"), [[1.0, 2.0], [3.0, 4.0]])},
        coords={"latitude": [10.0, -10.0], "longitude": [20.0, 30.0]},
    )
    out = standardize_coords(ds)
    assert set(out.dims) == {"lat", "lon"}
    assert list(out["lat"].values) == [-10.0, 10.0]
    assert float(out["value"].sel(lat=-10, lon=20)) == 3.0


# -------------------------------------------------------------------- FDR
def test_fdr_controls_false_discoveries_and_ignores_missing_cells():
    p = np.array([[0.001, 0.01, 0.5, np.nan]])
    sig = fdr_significant(p, alpha=0.05)
    assert sig.tolist() == [[True, True, False, False]]
    # A missing p-value is never significant.
    assert not sig[0, 3]


def test_fdr_all_missing_is_all_false():
    sig = fdr_significant(np.full((3, 3), np.nan))
    assert sig.shape == (3, 3)
    assert not sig.any()


def test_single_non_significant_p_value_is_not_promoted():
    assert fdr_significant(np.array([0.2]), alpha=0.05).tolist() == [False]


# ----------------------------------------------------------------- wording
def _row(**overrides):
    row = {
        "variable": "Precipitation",
        "rate_per_decade": 2.5,
        "n_years": 23,
        "significant": True,
        "low_confidence": False,
    }
    row.update(overrides)
    return row


def test_significant_increase_wording_mentions_direction_and_fdr():
    text = sentence(_row(), "mm/month")
    assert "has increased" in text
    assert "2.5 mm/month per decade" in text
    assert "statistically significant after correcting" in text


def test_significant_decrease_wording_mentions_direction():
    text = sentence(_row(rate_per_decade=-2.5), "mm/month")
    assert "has decreased" in text
    assert "increased" not in text


def test_non_significant_wording_never_claims_no_change():
    text = sentence(_row(significant=False, rate_per_decade=0.0), "mm/month")
    lower = text.lower()
    assert "no statistically significant change" in lower
    assert "no change" not in lower
    assert "nothing changed" not in lower


def test_short_record_adds_caution():
    text = sentence(_row(low_confidence=True, n_years=12), "mm/month")
    assert "treat this result with caution" in text


def test_nearby_divergence_wording():
    text = nearby_sentence({"up": 0.4, "down": 0.3, "none": 0.3, "n_cells": 9})
    assert "opposite directions" in text


# ------------------------------------------------------------------ ranking
def _tiny_layer(*, significant: bool, standardized: float, variable: str) -> xr.Dataset:
    return xr.Dataset(
        {
            "slope_per_decade": (("lat", "lon"), np.array([[standardized]])),
            "significant": (("lat", "lon"), np.array([[significant]])),
            "class": (("lat", "lon"), np.array([[1.0 if significant else 0.0]])),
            "std_trend": (("lat", "lon"), np.array([[standardized]])),
            "n_years": (("lat", "lon"), np.array([[23.0]])),
            "low_confidence": (("lat", "lon"), np.array([[False]])),
        },
        coords={"lat": [0.0], "lon": [0.0]},
        attrs={
            "variable": variable,
            "display_name": variable.title(),
            "units": "unit",
            "surface": "land,ocean",
            "period_start": "2002-01",
            "period_end": "2024-12",
        },
    )


def test_significant_rows_rank_above_larger_but_noisy_rows():
    datasets = {
        "alpha": _tiny_layer(significant=True, standardized=1.0, variable="alpha"),
        "beta": _tiny_layer(significant=False, standardized=99.0, variable="beta"),
    }
    report = build_report(
        0.0, 0.0, {"alpha": "unused", "beta": "unused"}, window=5, datasets=datasets
    )
    assert [row["key"] for row in report["variables"]] == ["alpha", "beta"]
    assert "statistically significant" in report["variables"][0]["summary"]
    assert "no statistically significant change" in report["variables"][1]["summary"].lower()
    assert "not a forecast" in report["not_a_forecast"].lower()
