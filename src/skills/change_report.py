#!/usr/bin/env python3
"""Build a ranked change report for a clicked location from precomputed trend layers.

Requires: xarray, numpy, zarr.
"""
import argparse
import json
import sys

import numpy as np
import xarray as xr


def _sig(x, digits=2):
    if x == 0 or not np.isfinite(x):
        return x
    return float(f"{x:.{digits}g}")


def _as_bool(value) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes"}
    return bool(value)


def neighbor_shares(cls, lat0, lon0, half_width):
    win = cls.sel(lat=slice(lat0 - half_width, lat0 + half_width),
                  lon=slice(lon0 - half_width, lon0 + half_width))
    n = int(win.notnull().sum())
    if n == 0:
        return None
    return {"n_cells": n,
            "up": float((win == 1).sum()) / n,
            "down": float((win == -1).sum()) / n,
            "none": float((win == 0).sum()) / n}


def sentence(row, unit):
    n = row["n_years"]
    if row["significant"]:
        verb = "increased" if row["rate_per_decade"] > 0 else "decreased"
        s = (f"At this location, {row['variable']} has {verb} by about "
             f"{abs(row['rate_per_decade']):.2g} {unit} per decade over {n} years "
             f"(statistically significant after correcting for testing many locations).")
    else:
        s = f"No statistically significant change in {row['variable']} was detected over {n} years."
    if row["low_confidence"]:
        s += f" The record is short ({n} years), so treat this result with caution."
    return s


def nearby_sentence(nb):
    if not nb:
        return ""
    up, down, none = nb["up"], nb["down"], nb["none"]
    if up > 0.15 and down > 0.15:
        return (f"Nearby, {up:.0%} of cells increase and {down:.0%} decrease significantly, "
                f"so this variable is moving in opposite directions within the region.")
    if none >= 0.7:
        return "Most surrounding cells show no significant change."
    same = max(up, down)
    return f"Nearby, {same:.0%} of surrounding cells show a significant change in the same direction."


def build_report(lat, lon, layers, window=5.0, datasets=None):
    """layers: dict of display name -> path to a layers Zarr. Returns a report dict.

    datasets: optional dict of display name -> already-open xarray Dataset. The
    API loads layers once at startup and passes them here; when omitted, paths
    are opened exactly as the skill documents.
    """
    datasets = datasets or {}
    rows = []
    for name, path in layers.items():
        L = datasets.get(name)
        if L is None:
            L = xr.open_zarr(path)
        pt = L.sel(lat=lat, lon=lon, method="nearest")
        slope = float(pt["slope_per_decade"])
        if not np.isfinite(slope):
            continue  # variable does not apply at this location
        unit = L.attrs.get("units", "")
        display = L.attrs.get("display_name", name)
        row = {
            "variable": display,
            "key": L.attrs.get("variable", name),
            "unit": unit,
            "rate_per_decade": _sig(slope),
            "significant": bool(pt["significant"]),
            "class": int(pt["class"]) if np.isfinite(float(pt["class"])) else 0,
            "standardized": _sig(float(pt["std_trend"])) if np.isfinite(float(pt["std_trend"])) else 0.0,
            "n_years": int(pt["n_years"]),
            "low_confidence": bool(pt["low_confidence"]),
            "model_based": _as_bool(L.attrs.get("model_based", False)),
            "synthetic": _as_bool(L.attrs.get("synthetic", False)),
            "surface": L.attrs.get("surface", "unknown"),
            "period": [L.attrs.get("period_start"), L.attrs.get("period_end")],
            "source_dataset": L.attrs.get("source_dataset", ""),
            "dataset_version": L.attrs.get("dataset_version", ""),
            "cell": {"lat": float(pt["lat"]), "lon": float(pt["lon"])},
        }
        row["summary"] = sentence(row, unit)
        row["nearby"] = neighbor_shares(L["class"], float(pt["lat"]), float(pt["lon"]), window)
        row["nearby_summary"] = nearby_sentence(row["nearby"])
        rows.append(row)
    rows.sort(key=lambda r: (not r["significant"], r["low_confidence"], -abs(r["standardized"])))

    diverging = [r for r in rows if r["nearby"] and r["nearby"]["up"] > 0.15 and r["nearby"]["down"] > 0.15]
    if not rows:
        summary = "No variables apply at this location."
    else:
        summary = rows[0]["summary"]
        if diverging:
            summary += (
                f" Within about {window:g} degrees, {len(diverging)} of {len(rows)} variable(s) "
                "show both significant increases and decreases, so neighboring areas are moving "
                "in opposite directions."
            )
        elif rows[0]["nearby_summary"]:
            summary += " " + rows[0]["nearby_summary"]
    return {
        "query": {"lat": lat, "lon": lon, "window_deg": window},
        "variables": rows,
        "summary": summary,
        "divergence_detected": bool(diverging),
        "not_a_forecast": "Observed change only; not a forecast. Non-significant means no significant change was detected, not that nothing changed.",
    }


def to_text(rep):
    q = rep["query"]
    out = [f"Change report for ({q['lat']}, {q['lon']})"]
    if not rep["variables"]:
        out.append("No variables apply at this location.")
    for r in rep["variables"]:
        arrow = "-" if not r["significant"] else ("up" if r["rate_per_decade"] > 0 else "down")
        out.append(f"\n[{arrow}] {r['variable']}")
        out.append("  " + r["summary"])
        if r["nearby_summary"]:
            out.append("  " + r["nearby_summary"])
    out.append("\nObserved change only; not a forecast.")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--lat", type=float, required=True)
    ap.add_argument("--lon", type=float, required=True)
    ap.add_argument("--layer", action="append", required=True, help='"Display name=path/to/layers.zarr" (repeatable)')
    ap.add_argument("--window", type=float, default=5.0, help="Half-width in degrees for the nearby comparison")
    ap.add_argument("--format", choices=["json", "text", "both"], default="both")
    args = ap.parse_args()

    layers = {}
    for item in args.layer:
        if "=" not in item:
            sys.exit(f"--layer needs 'Name=path', got: {item}")
        name, path = item.split("=", 1)
        layers[name] = path
    rep = build_report(args.lat, args.lon, layers, args.window)
    if args.format in ("text", "both"):
        print(to_text(rep))
    if args.format in ("json", "both"):
        print(json.dumps(rep, indent=2))


if __name__ == "__main__":
    main()
