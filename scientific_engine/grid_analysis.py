"""Grid-level analysis for gridded precipitation (or similar) observations.

Produces per-cell trend results and run metadata aligned with the draft
Go/Python contract. No trends/significance are assigned to cells with
insufficient valid observations.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

import numpy as np
import xarray as xr

from . import __version__
from .aggregation import annual_mean_anomalies, seasonal_mean_anomalies, KENYA_SEASONS
from .reliability import classify_cell, fdr_significance_mask, low_confidence_flag
from .trend import compute_trend


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _subset_bounds(da: xr.DataArray, bounds: dict | None) -> xr.DataArray:
    if not bounds:
        return da
    min_lon = float(bounds["min_lon"])
    min_lat = float(bounds["min_lat"])
    max_lon = float(bounds["max_lon"])
    max_lat = float(bounds["max_lat"])
    # assume coords named lat/lon
    if "lat" in da.coords:
        lat = da["lat"]
        if lat.size >= 2 and float(lat[0]) > float(lat[-1]):
            da = da.sel(lat=slice(max_lat, min_lat))
        else:
            da = da.sel(lat=slice(min_lat, max_lat))
    if "lon" in da.coords:
        lon = da["lon"]
        if lon.size >= 2 and float(lon[0]) > float(lon[-1]):
            da = da.sel(lon=slice(max_lon, min_lon))
        else:
            da = da.sel(lon=slice(min_lon, max_lon))
    return da


def _subset_period(da: xr.DataArray, period: dict | None) -> xr.DataArray:
    if not period or "time" not in da.coords:
        return da
    start = period.get("start")
    end = period.get("end")
    if start and end:
        # support date strings
        da = da.sel(time=slice(str(start), str(end)))
    return da


def _cell_id(i: int, j: int) -> str:
    return f"r{i}c{j}"


def _finite_mean(values: np.ndarray) -> float | None:
    v = np.asarray(values, dtype=float)
    ok = np.isfinite(v)
    if not ok.any():
        return None
    return float(np.mean(v[ok]))


def analyze_grid(
    da: xr.DataArray,
    *,
    investigation_id: str | None = None,
    bounds: dict | None = None,
    period: dict | None = None,
    config: dict | None = None,
    dataset_meta: dict | None = None,
    variable_name: str | None = None,
) -> dict[str, Any]:
    """Run grid-level trend analysis and return contract-aligned results.

    da: monthly observation DataArray with dims including time, lat, lon.
    """
    cfg = config or {}
    min_months = int(cfg.get("min_months", 9))
    min_years = int(cfg.get("min_years", 10))
    ok_years = int(cfg.get("ok_years", 15))
    alpha = float(cfg.get("alpha", 0.05))
    alpha_ci = float(cfg.get("alpha_ci", 0.95))
    min_completeness = float(cfg.get("min_completeness", 0.0))
    aggregation_mode = str(cfg.get("aggregation", "annual")).lower()
    seasons_cfg = cfg.get("seasons")
    min_months_per_season = cfg.get("min_months_per_season")

    if variable_name is None:
        variable_name = str(da.name or "precipitation")
    units = str(da.attrs.get("units", cfg.get("units", "")) or "")

    da = _subset_period(da, period)
    da = _subset_bounds(da, bounds)

    if "time" not in da.dims or "lat" not in da.dims or "lon" not in da.dims:
        raise ValueError("Observation data must include time, lat, lon dimensions")
    if da.sizes.get("time", 0) == 0 or da.sizes.get("lat", 0) == 0 or da.sizes.get("lon", 0) == 0:
        raise ValueError("Observation subset is empty for the requested bounds/period")

    annual = annual_mean_anomalies(da, min_months=min_months, variable=variable_name)
    years = np.asarray(annual["year"].values)
    # ensure lat/lon order for indexing
    annual = annual.transpose("year", "lat", "lon")
    n_years_total = int(annual.sizes["year"])

    seasonal_results_by_idx: dict[int, dict[str, Any]] = {}
    seasonal_meta: dict[str, Any] | None = None
    if aggregation_mode == "seasonal":
        seasonal = seasonal_mean_anomalies(
            da,
            seasons=seasons_cfg,
            min_months_per_season=min_months_per_season,
            variable=variable_name,
        )
        seasonal = seasonal.transpose("year", "season", "lat", "lon")
        s_years = np.asarray(seasonal["year"].values)
        s_names = [str(s) for s in np.asarray(seasonal["season"].values).tolist()]
        s_vals = np.asarray(seasonal.values, dtype=float)  # (year, season, lat, lon)
        season_defs = seasonal.attrs.get("season_definitions", seasons_cfg or KENYA_SEASONS)
        seasonal_meta = {
            "aggregation": "seasonal_mean_of_monthly_anomalies",
            "seasons": season_defs,
            "min_months_per_season": min_months_per_season,
        }
        # Precompute per-season trends per cell
        # index by flat cell idx in same order as annual loop
        idx = 0
        for i in range(seasonal.sizes["lat"]):
            for j in range(seasonal.sizes["lon"]):
                cell_seasons: dict[str, Any] = {}
                for si, sname in enumerate(s_names):
                    series = s_vals[:, si, i, j]
                    tr = compute_trend(
                        s_years,
                        series,
                        min_years=min_years,
                        slope_units=(f"{units}/year" if units else "per year"),
                        alpha_ci=alpha_ci,
                    )
                    n_obs = int(np.isfinite(series).sum())
                    completeness = (n_obs / int(seasonal.sizes["year"])) if seasonal.sizes["year"] > 0 else 0.0
                    flags = list(tr.flags)
                    if low_confidence_flag(tr.n_years, ok_years=ok_years) and tr.sufficient:
                        flags.append("low_confidence")
                    # per-season significance without FDR across all cells/seasons for simplicity; mark p-value
                    significant = bool(tr.p_value is not None and tr.p_value < alpha) if tr.sufficient else False
                    classification = classify_cell(
                        sufficient=tr.sufficient,
                        fdr_significant=significant,
                        direction=tr.direction,
                        flags=flags,
                        completeness=completeness,
                        min_completeness=min_completeness,
                    )
                    if not tr.sufficient:
                        significant = False
                    cell_seasons[sname] = {
                        "season": sname,
                        "months": season_defs.get(sname),
                        "n_years": int(tr.n_years),
                        "completeness": float(round(completeness, 6)),
                        "trend_direction": tr.direction if tr.sufficient else None,
                        "sens_slope": {
                            "value": tr.slope_per_year,
                            "units": tr.slope_units,
                            "ci_lower": tr.ci_lower,
                            "ci_upper": tr.ci_upper,
                            "confidence_level": alpha_ci,
                        } if tr.sufficient and tr.slope_per_year is not None else None,
                        "mann_kendall": {
                            "p_value": tr.p_value,
                            "tau": tr.mk_tau,
                            "statistic": tr.mk_statistic,
                            "method": "mann_kendall_hamed_rao",
                        } if tr.sufficient and tr.p_value is not None else None,
                        "p_value": tr.p_value if tr.sufficient else None,
                        "significant": significant,
                        "classification": classification,
                        "flags": sorted(set(flags)),
                    }
                seasonal_results_by_idx[idx] = cell_seasons
                idx += 1

    lats = np.asarray(annual["lat"].values)
    lons = np.asarray(annual["lon"].values)
    values = np.asarray(annual.values, dtype=float)  # (year, lat, lon)

    # pass 1: compute trends per cell
    trend_results = []
    pvals = []
    cell_coords = []
    for i in range(annual.sizes["lat"]):
        for j in range(annual.sizes["lon"]):
            series = values[:, i, j]
            tr = compute_trend(years, series, min_years=min_years, slope_units=(f"{units}/year" if units else "per year"), alpha_ci=alpha_ci)
            trend_results.append(tr)
            pvals.append(tr.p_value if (tr.sufficient and tr.p_value is not None) else np.nan)
            cell_coords.append((i, j, float(lats[i]), float(lons[j]), series))

    pvals_arr = np.asarray(pvals, dtype=float)
    sig_mask = fdr_significance_mask(pvals_arr, alpha=alpha)

    cells = []
    for idx, (tr, (i, j, lat, lon, series)) in enumerate(zip(trend_results, cell_coords)):
        n_obs = int(np.isfinite(series).sum())  # valid annual anomaly observations
        completeness = (n_obs / n_years_total) if n_years_total > 0 else 0.0
        flags = list(tr.flags)
        if low_confidence_flag(tr.n_years, ok_years=ok_years) and tr.sufficient:
            flags.append("low_confidence")
        significant = bool(sig_mask[idx]) if tr.sufficient and tr.p_value is not None and np.isfinite(tr.p_value) else False
        classification = classify_cell(
            sufficient=tr.sufficient,
            fdr_significant=significant,
            direction=tr.direction,
            flags=flags,
            completeness=completeness,
            min_completeness=min_completeness,
        )
        if not tr.sufficient:
            # do not assign detected trend/significance
            significant = False

        mean_val = _finite_mean(series)
        # also provide mean of original monthly observations over selected period per cell if easy
        orig_series = np.asarray(da.transpose("time", "lat", "lon").values[:, i, j], dtype=float) if "time" in da.dims else np.array([])
        mean_obs = _finite_mean(orig_series)

        cell = {
            "cell_id": _cell_id(i, j),
            "lat": lat,
            "lon": lon,
            "n_observations": int(np.isfinite(orig_series).sum()) if orig_series.size else n_obs,
            "n_years": int(tr.n_years),
            "completeness": float(round(completeness, 6)),
            "mean": {"value": mean_obs, "units": units} if mean_obs is not None else {"value": mean_val, "units": (f"{units} (annual anomaly)" if units else "annual anomaly")} if mean_val is not None else None,
            "trend_direction": tr.direction if tr.sufficient else None,
            "sens_slope": {
                "value": tr.slope_per_year,
                "units": tr.slope_units,
                "ci_lower": tr.ci_lower,
                "ci_upper": tr.ci_upper,
                "confidence_level": alpha_ci,
            } if tr.sufficient and tr.slope_per_year is not None else None,
            "mann_kendall": {
                "p_value": tr.p_value,
                "tau": tr.mk_tau,
                "statistic": tr.mk_statistic,
                "method": "mann_kendall_hamed_rao",
            } if tr.sufficient and tr.p_value is not None else None,
            "p_value": tr.p_value if tr.sufficient else None,
            "significant_fdr": significant,
            "classification": classification,
            "flags": sorted(set(flags)),
        }
        if seasonal_results_by_idx:
            cell["seasonal_trends"] = seasonal_results_by_idx.get(idx, {})
        cells.append(cell)

    run_metadata = {
        "contract": "analysis-response",
        "version": "0.1-draft",
        "investigation_id": investigation_id,
        "variable": variable_name,
        "units": units,
        "methods": {
            "aggregation": "monthly_climatology_anomaly_then_annual_mean",
            "seasonal_aggregation": "seasonal_mean_of_monthly_anomalies" if aggregation_mode == "seasonal" else None,
            "trend_test": "mann_kendall_hamed_rao",
            "slope": "theil_sen",
            "multiple_testing": "benjamini_hochberg_fdr",
        },
        "parameters": {
            "min_months": min_months,
            "min_years": min_years,
            "ok_years": ok_years,
            "alpha": alpha,
            "alpha_ci": alpha_ci,
            "min_completeness": min_completeness,
            "aggregation_mode": aggregation_mode,
            "seasons": (seasonal_meta or {}).get("seasons"),
            "min_months_per_season": min_months_per_season,
        },
        "dataset": dataset_meta or {},
        "bounds": bounds,
        "period": period,
        "generated_at": _utc_now(),
        "engine_version": __version__,
        "grid": {
            "n_lat": int(annual.sizes["lat"]),
            "n_lon": int(annual.sizes["lon"]),
            "n_years_total": n_years_total,
        },
    }

    return {
        "status": "completed",
        "cells": cells,
        "run_metadata": run_metadata,
        "summary": {
            "cells_total": len(cells),
            "cells_sufficient": sum(1 for c in cells if c.get("classification") != "insufficient_data"),
            "significant_increase": sum(1 for c in cells if c.get("classification") == "significant_increase"),
            "significant_decrease": sum(1 for c in cells if c.get("classification") == "significant_decrease"),
            "no_significant_trend": sum(1 for c in cells if c.get("classification") == "no_significant_trend"),
            "insufficient_data": sum(1 for c in cells if c.get("classification") == "insufficient_data"),
            "inconclusive": sum(1 for c in cells if c.get("classification") == "inconclusive"),
        },
    }
