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
