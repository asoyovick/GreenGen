"""Temporal aggregation for gridded time series.

Missing observations must be represented explicitly (NaN/mask) and are never
treated as zero. Incomplete periods are excluded per configured thresholds.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import xarray as xr


@dataclass
class AggregationConfig:
    min_months: int = 9
    min_years: int = 10


def _to_data_array(obj: Any, variable: str | None = None) -> xr.DataArray:
    if isinstance(obj, xr.DataArray):
        return obj
    if isinstance(obj, xr.Dataset):
        if variable is None:
            # choose first data variable
            names = list(obj.data_vars)
            if not names:
                raise ValueError("Dataset has no data variables")
            variable = names[0]
        if variable not in obj:
            raise ValueError(f"Variable '{variable}' not found in dataset")
        return obj[variable]
    raise TypeError("Expected xarray Dataset or DataArray")


def monthly_anomalies(da: xr.DataArray) -> xr.DataArray:
    """Compute monthly anomalies relative to calendar-month climatology.

    Climatology is computed over valid (finite) observations only.
    """
    if "time" not in da.dims:
        raise ValueError("Input must have a 'time' dimension")
    clim = da.groupby("time.month").mean("time", skipna=True)
    anom = da.groupby("time.month") - clim
    # preserve attrs/units (anomaly in same units as input)
    anom.attrs = {**da.attrs, **anom.attrs}
    return anom


def annual_mean_anomalies(
    da: xr.DataArray,
    min_months: int = 9,
    variable: str | None = None,
) -> xr.DataArray:
    """Aggregate monthly observations to annual mean anomalies.

    - Computes monthly climatology and anomalies.
    - Computes annual mean of monthly anomalies for years with >= min_months
      valid monthly values; other years become missing (NaN), never zero.
    Returns DataArray with dimension 'year' (and spatial dims preserved).
    """
    da = _to_data_array(da, variable)
    anom = monthly_anomalies(da)
    annual = anom.groupby("time.year").mean("time", skipna=True)
    n_valid = anom.notnull().groupby("time.year").sum("time")
    annual = annual.where(n_valid >= min_months)
    annual.name = "annual_anomaly"
    annual.attrs = {**da.attrs}
    annual.attrs["aggregation"] = "annual_mean_of_monthly_anomalies"
    annual.attrs["min_months"] = int(min_months)
    return annual


def annual_valid_counts(da: xr.DataArray, min_months: int = 9) -> xr.DataArray:
    """Count valid months per year for the anomaly aggregation."""
    da = _to_data_array(da)
    anom = monthly_anomalies(da)
    n_valid = anom.notnull().groupby("time.year").sum("time")
    return n_valid


def series_completeness(n_years_valid: int, n_years_total: int) -> float:
    if n_years_total <= 0:
        return 0.0
    return float(np.clip(n_years_valid / n_years_total, 0.0, 1.0))


# Default seasons for Kenya (bimodal rainfall regime).
# MAM: Long rains (Mar-May), OND: Short rains (Oct-Dec),
# JJAS: June-September season, JF: January-February season.
# Season definitions must be documented in run metadata and can be overridden via config.
KENYA_SEASONS: dict[str, list[int]] = {
    "MAM": [3, 4, 5],
    "JJAS": [6, 7, 8, 9],
    "OND": [10, 11, 12],
    "JF": [1, 2],
}


def _normalize_seasons(seasons: dict[str, list[int]] | None) -> dict[str, list[int]]:
    src = seasons or KENYA_SEASONS
    out: dict[str, list[int]] = {}
    for name, months in src.items():
        if not name or not isinstance(months, (list, tuple)):
            raise ValueError(f"Invalid season definition for {name!r}")
        norm = sorted({int(m) for m in months})
        if any(m < 1 or m > 12 for m in norm):
            raise ValueError(f"Season {name!r} has invalid month numbers: {months!r}")
        if not norm:
            raise ValueError(f"Season {name!r} must include at least one month")
        out[str(name)] = norm
    return out


def seasonal_mean_anomalies(
    da: xr.DataArray,
    seasons: dict[str, list[int]] | None = None,
    min_months_per_season: int | dict[str, int] | None = None,
    variable: str | None = None,
) -> xr.DataArray:
    """Aggregate monthly observations to seasonal mean anomalies.

    For each season, computes calendar-month climatology from valid observations,
    then monthly anomalies, then seasonal mean anomaly per year. Seasons with fewer
    than the required valid months are set to NaN (never zero).

    Returns DataArray with dims ('year', 'season', ...spatial dims...).
    """
    da = _to_data_array(da, variable)
    if "time" not in da.dims:
        raise ValueError("Input must have a 'time' dimension")
    seasons_norm = _normalize_seasons(seasons)
    anom = monthly_anomalies(da)
    years = np.unique(anom["time.year"].values)
    season_names = list(seasons_norm.keys())

    if isinstance(min_months_per_season, dict):
        min_map = {k: int(v) for k, v in min_months_per_season.items()}
    else:
        default_min = 2 if min_months_per_season is None else int(min_months_per_season)
        min_map = {s: max(1, min(default_min, len(months))) for s, months in seasons_norm.items()}

    arrays = []
    for season in season_names:
        months = seasons_norm[season]
        req = int(min_map.get(season, max(1, min(2, len(months)))))
        req = max(1, min(req, len(months)))
        sel = anom.sel(time=anom["time.month"].isin(months))
        seasonal = sel.groupby("time.year").mean("time", skipna=True)
        n_valid = sel.notnull().groupby("time.year").sum("time")
        seasonal = seasonal.where(n_valid >= req)
        seasonal = seasonal.expand_dims({"season": [season]})
        seasonal.attrs["min_months_per_season"] = req
        arrays.append(seasonal)

    out = xr.concat(arrays, dim="season")
    # Ensure all years present in full series are represented? keep observed years.
    out = out.reindex(year=sorted(int(y) for y in years))
    out.name = "seasonal_anomaly"
    out.attrs = {**da.attrs}
    out.attrs["aggregation"] = "seasonal_mean_of_monthly_anomalies"
    out.attrs["season_definitions"] = {k: list(v) for k, v in seasons_norm.items()}
    return out
