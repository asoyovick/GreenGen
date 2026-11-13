"""Place-level (regional) trend analysis built on per-cell layers.

Reuses the same trend test as trend-significance: Theil-Sen slope and
Hamed-Rao-modified Mann-Kendall p-value on a regional annual anomaly series.
Significance for place reports is assigned by Benjamini-Hochberg FDR across
places of the same level for each variable.
"""
from __future__ import annotations

import math
from typing import Any, Iterable

import numpy as np
import pymannkendall as mk
from scipy.stats import theilslopes
from statsmodels.stats.multitest import multipletests

from src.skills.compute_trends import fdr_significant


def _sig(x, digits=2):
    if x == 0 or not np.isfinite(x):
        return x
    return float(f"{x:.{digits}g}")


def _as_bool(value) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes"}
    return bool(value)


def regional_annual_series(
    annual_anomaly: np.ndarray,
    ilat: np.ndarray,
    ilon: np.ndarray,
    fractions: np.ndarray,
    lat_weights: np.ndarray,
    *,
    valid_cells: np.ndarray | None = None,
    min_coverage: float = 0.7,
) -> tuple[np.ndarray, np.ndarray, float]:
    """Area-weighted regional annual mean.

    annual_anomaly: (year, lat, lon)
    returns (series[year] with NaN where coverage insufficient, n_cells_used_per_year, overall_coverage)
    """
    if len(ilat) == 0:
        years = annual_anomaly.shape[0]
        return np.full(years, np.nan), np.zeros(years, dtype=int), 0.0
    vals = annual_anomaly[:, ilat, ilon]  # (year, cells)
    w = lat_weights[ilat] * fractions
    if valid_cells is not None:
        ok_cell = np.asarray(valid_cells, dtype=bool)
        w = np.where(ok_cell, w, 0.0)
    total_w = float(np.sum(w))
    years = vals.shape[0]
    series = np.full(years, np.nan, dtype=float)
    used = np.zeros(years, dtype=int)
    if total_w <= 0:
        return series, used, 0.0
    for t in range(years):
        v = vals[t]
        ok = np.isfinite(v) & (w > 0)
        ww = np.sum(w[ok])
        used[t] = int(np.sum(ok))
        if ww / total_w >= min_coverage and ww > 0:
            series[t] = float(np.sum(v[ok] * w[ok]) / ww)
    finite_years = np.isfinite(series)
    coverage = float(np.sum(w[np.any(np.isfinite(vals), axis=0) & (w > 0)]) / total_w) if total_w else 0.0
    return series, used, coverage


def trend_from_series(series: np.ndarray, years: np.ndarray, min_years: int) -> tuple[float, float, int]:
    ok = np.isfinite(series)
    n = int(np.sum(ok))
    if n < min_years:
        return np.nan, np.nan, n
    yy = np.asarray(series[ok], dtype=float)
    xx = np.asarray(years[ok], dtype=float)
    if np.ptp(yy) == 0:
        return 0.0, 1.0, n
    try:
        slope = float(theilslopes(yy, xx)[0])
        p = float(mk.hamed_rao_modification_test(yy).p)
    except Exception:
        return np.nan, np.nan, n
    return slope, p, n


def inside_place_shares(
    cls: np.ndarray, ilat: np.ndarray, ilon: np.ndarray, fractions: np.ndarray, lat_weights: np.ndarray
) -> dict[str, Any] | None:
    if len(ilat) == 0:
        return None
    c = cls[ilat, ilon]
    w = lat_weights[ilat] * fractions
    valid = np.isfinite(c) & (w > 0)
    total = float(np.sum(w[valid]))
    if total <= 0:
        return None
    up = float(np.sum(w[valid & (c == 1)]) / total)
    down = float(np.sum(w[valid & (c == -1)]) / total)
    none = float(np.sum(w[valid & (c == 0)]) / total)
    return {"n_cells": int(np.sum(valid)), "up": up, "down": down, "none": none}


def is_divergent(shares: dict[str, Any] | None, threshold: float = 0.15) -> bool:
    if not shares:
        return False
    return shares["up"] > threshold and shares["down"] > threshold


def sentence_place(row: dict, unit: str, place_name: str) -> str:
    n = row["n_years"]
    scale = "across this place (region average)" if row.get("scale") == "region_average" else "for the grid cell covering this place"
    if row["significant"]:
        verb = "increased" if row["rate_per_decade"] > 0 else "decreased"
        s = (
            f"{scale.capitalize()}, {row['variable']} has {verb} by about "
            f"{abs(row['rate_per_decade']):.2g} {unit} per decade over {n} years "
            f"in {place_name} (statistically significant after correcting for testing many places)."
        )
    else:
        s = f"No statistically significant change in {row['variable']} was detected over {n} years in {place_name}."
    if row.get("low_confidence"):
        s += f" The record is short ({n} years), so treat this result with caution."
    return s


def inside_place_sentence(shares: dict | None) -> str:
    if not shares:
        return ""
    up, down = shares["up"], shares["down"]
    if up > 0.15 and down > 0.15:
        return (
            f"Inside this place, {up:.0%} of valid area increases and {down:.0%} decreases significantly, "
            "so areas within this place are moving in opposite directions."
        )
    if shares["none"] >= 0.7:
        return "Most of this place shows no significant change."
    same = max(up, down)
    direction = "increase" if up >= down else "decrease"
    return f"Inside this place, {same:.0%} of valid area shows a significant {direction}."


def build_place_report_from_results(
    place: dict,
    results_by_var: dict[str, dict],
    *,
    datasets: dict[str, Any],
    neighbors: list[dict] | None = None,
) -> dict[str, Any]:
    rows = []
    for key, res in results_by_var.items():
        if not res.get("applies", True):
            continue
        ds = datasets.get(key)
        if ds is None:
            continue
        unit = ds.attrs.get("units", "")
        display = ds.attrs.get("display_name", key)
        slope_dec = float(res.get("slope_per_decade", np.nan))
        if not math.isfinite(slope_dec):
            continue
        row = {
            "variable": display,
            "key": key,
            "unit": unit,
            "rate_per_decade": _sig(slope_dec),
            "significant": bool(res.get("significant", False)),
            "class": int(np.sign(slope_dec)) if res.get("significant") else 0,
            "standardized": _sig(float(res.get("std_trend", 0.0))) if math.isfinite(float(res.get("std_trend", np.nan))) else 0.0,
            "n_years": int(res.get("n_years", 0)),
            "n_cells": int(res.get("n_cells", 0)),
            "coverage": float(res.get("coverage", 0.0)),
            "low_confidence": bool(res.get("low_confidence", False)),
            "model_based": _as_bool(ds.attrs.get("model_based", False)),
            "synthetic": _as_bool(ds.attrs.get("synthetic", False)),
            "surface": ds.attrs.get("surface", "unknown"),
            "period": [ds.attrs.get("period_start"), ds.attrs.get("period_end")],
            "source_dataset": ds.attrs.get("source_dataset", ""),
            "dataset_version": ds.attrs.get("dataset_version", ""),
            "scale": res.get("scale", "region_average"),
            "inside_place": res.get("inside_place"),
            "divergent": bool(res.get("divergent", False)),
        }
        row["summary"] = sentence_place(row, unit, place.get("name", "this place"))
        row["inside_place_summary"] = inside_place_sentence(row["inside_place"])
        rows.append(row)

    rows.sort(key=lambda r: (not r["significant"], r["low_confidence"], -abs(r["standardized"])))
    diverging = [r for r in rows if r.get("divergent")]
    if not rows:
        summary = "No variables apply at this location."
    else:
        summary = rows[0]["summary"]
        if diverging:
            summary += (
                f" Within this place, {len(diverging)} of {len(rows)} variable(s) show both significant "
                "increases and decreases across different areas."
            )
        elif rows[0].get("inside_place_summary"):
            summary += " " + rows[0]["inside_place_summary"]

    neighbor_summary = ""
    if neighbors:
        same = sum(1 for n in neighbors if n.get("direction") == (1 if rows and rows[0]["rate_per_decade"] > 0 else -1) and n.get("significant"))
        neighbor_summary = f"{same} of {len(neighbors)} neighboring place(s) show a significant change in the same direction as the top variable." if rows else ""

    return {
        "place": {
            "id": place.get("id"),
            "name": place.get("name"),
            "level": place.get("level"),
            "hierarchy": place.get("hierarchy"),
            "centroid": place.get("centroid"),
            "bbox": place.get("bbox"),
        },
        "variables": rows,
        "summary": summary,
        "divergence_detected": bool(diverging),
        "neighbors": neighbors or [],
        "neighbor_summary": neighbor_summary,
        "not_a_forecast": "Observed change only; not a forecast. Non-significant means no significant change was detected, not that nothing changed.",
    }


def compute_place_result_for_variable(
    ds, mask: list[tuple[int, int, float]], *, min_years: int, ok_years: int, alpha: float, min_coverage: float = 0.7
) -> dict[str, Any]:
    """Compute regional trend result for one variable (before cross-place FDR)."""
    lats = ds["lat"].values
    lat_weights = np.cos(np.deg2rad(lats))
    if not mask:
        return {"applies": False, "reason": "no_cells"}
    ilat = np.array([m[0] for m in mask], dtype=int)
    ilon = np.array([m[1] for m in mask], dtype=int)
    frac = np.array([m[2] for m in mask], dtype=float)

    annual = ds["annual_anomaly"].values  # (year, lat, lon)
    years = ds["year"].values.astype(float)
    # applicability per included cell: has any finite annual anomaly
    cell_vals = annual[:, ilat, ilon]
    valid_cells = np.any(np.isfinite(cell_vals), axis=0)
    if not np.any(valid_cells):
        return {"applies": False, "reason": "no_valid_data"}

    series, used, coverage = regional_annual_series(
        annual, ilat, ilon, frac, lat_weights, valid_cells=valid_cells, min_coverage=min_coverage
    )
    slope, p, n = trend_from_series(series, years, min_years)
    cls = ds["class"].values
    shares = inside_place_shares(cls, ilat, ilon, frac, lat_weights)
    if not math.isfinite(slope):
        return {
            "applies": True, "slope_per_year": None, "slope_per_decade": None, "p_value": None,
            "significant": False, "n_years": n, "n_cells": int(np.sum(valid_cells)),
            "coverage": coverage, "low_confidence": False, "std_trend": None,
            "inside_place": shares, "divergent": is_divergent(shares), "series": series, "years": years,
        }
    std = float(np.nanstd(series))
    std_trend = float((slope * 10) / std) if std > 0 and math.isfinite(std) else 0.0
    return {
        "applies": True,
        "slope_per_year": float(slope),
        "slope_per_decade": float(slope * 10),
        "p_value": float(p) if math.isfinite(p) else None,
        "significant": False,  # filled after FDR across places
        "n_years": int(n),
        "n_cells": int(np.sum(valid_cells)),
        "coverage": float(coverage),
        "low_confidence": bool(n < ok_years),
        "std_trend": std_trend,
        "inside_place": shares,
        "divergent": is_divergent(shares),
        "scale": "region_average",
        "series": series,
        "years": years,
    }
