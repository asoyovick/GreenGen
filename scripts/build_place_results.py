#!/usr/bin/env python3
"""Precompute place-level change results from per-cell trend layers.

Builds sparse cell masks for polygon places, computes regional annual series and
trends, applies BH-FDR across places of the same level per variable, and writes
compact JSON results for API lookup. Synthetic and real outputs are kept
separate.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import sys
from pathlib import Path

import numpy as np
import xarray as xr

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.common.config import load_app_config  # noqa: E402
from src.places.analysis import compute_place_result_for_variable  # noqa: E402
from src.places.gazetteer import load_gazetteer  # noqa: E402
from src.places.masks import Grid, mask_for_place  # noqa: E402
from src.skills.compute_trends import fdr_significant  # noqa: E402

POLYGON_LEVELS = {"country", "region", "sea"}


def to_jsonable(obj):
    if isinstance(obj, np.ndarray):
        return [None if (isinstance(x, float) and not math.isfinite(x)) else (x.item() if hasattr(x, "item") else x) for x in obj.tolist()]
    if isinstance(obj, (np.floating,)):
        v = float(obj)
        return v if math.isfinite(v) else None
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    return obj


def serialize_result(res: dict) -> dict:
    out = {}
    for k, v in res.items():
        if k in {"series", "years"}:
            out[k] = to_jsonable(np.asarray(v))
        elif isinstance(v, dict):
            out[k] = v
        elif isinstance(v, (np.floating, float)):
            out[k] = float(v) if math.isfinite(float(v)) else None
        elif isinstance(v, (np.integer, int)):
            out[k] = int(v)
        elif isinstance(v, np.ndarray):
            out[k] = to_jsonable(v)
        else:
            out[k] = v
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default=str(REPO_ROOT / "config/app.yaml"))
    ap.add_argument("--gazetteer", default=str(REPO_ROOT / "data/places/gazetteer"))
    ap.add_argument("--layers-dir", default=None)
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--levels", default="country,region,sea,city", help="Comma-separated levels to include")
    ap.add_argument("--limit", type=int, default=None, help="Limit places per level (for testing)")
    ap.add_argument("--min-coverage", type=float, default=0.7)
    args = ap.parse_args()

    cfg = load_app_config(args.config)
    layers_dir = Path(args.layers_dir) if args.layers_dir else cfg.layers_dir
    out_dir = Path(args.out_dir) if args.out_dir else (REPO_ROOT / "layers" / "places" / cfg.mode)
    out_dir.mkdir(parents=True, exist_ok=True)
    levels = [l.strip() for l in args.levels.split(",") if l.strip()]

    gaz = load_gazetteer(args.gazetteer)
    datasets = {}
    for key in cfg.mode_variables():
        path = layers_dir / f"{key}_trend.zarr"
        if path.exists():
            datasets[key] = xr.open_zarr(path).load()
            print(f"loaded {key} from {path}")
    if not datasets:
        print(f"No trend layers found in {layers_dir}", file=sys.stderr)
        return 1

    sample = next(iter(datasets.values()))
    grid = Grid.from_centers(sample["lat"].values, sample["lon"].values)
    analysis = cfg.analysis
    min_years = int(analysis.get("min_years", 10))
    ok_years = int(analysis.get("ok_years", 15))
    alpha = float(analysis.get("alpha", 0.05))

    all_results: dict[str, dict] = {}
    by_level_var_p: dict[tuple[str, str], list[tuple[str, float | None]]] = {}

    for level in levels:
        places = list(gaz.by_level.get(level, []))
        if args.limit:
            places = places[: args.limit]
        print(f"\n[{level}] {len(places)} places")
        for idx, place in enumerate(places, 1):
            pid = place.id
            rec = gaz.get(pid)
            if rec is None:
                continue
            place_result = {
                "place_id": pid,
                "name": rec["name"],
                "level": level,
                "hierarchy": rec.get("hierarchy"),
                "centroid": rec.get("centroid"),
                "bbox": rec.get("bbox"),
                "variables": {},
            }
            if level in POLYGON_LEVELS:
                geom = rec.get("mask_geometry") or rec.get("display_geometry")
                bbox = rec.get("bbox") or [0, 0, 0, 0]
                mask = mask_for_place(grid, geom, bbox, mode="center") if geom else []
                place_result["n_mask_cells"] = len(mask)
                place_result["scale"] = "region_average"
                for var, ds in datasets.items():
                    res = compute_place_result_for_variable(
                        ds, mask, min_years=min_years, ok_years=ok_years, alpha=alpha, min_coverage=args.min_coverage
                    )
                    if mask:
                        res["scale"] = "grid_cell" if len(mask) < 4 else "region_average"
                    else:
                        res["scale"] = "region_average"
                    place_result["variables"][var] = res
                    by_level_var_p.setdefault((level, var), []).append((pid, res.get("p_value")))
            else:
                # city: grid-cell scale at centroid
                lat, lon = (rec.get("centroid") or [0, 0])[1], (rec.get("centroid") or [0, 0])[0]
                place_result["scale"] = "grid_cell"
                for var, ds in datasets.items():
                    pt = ds.sel(lat=lat, lon=lon, method="nearest")
                    annual = pt["annual_anomaly"]
                    series = annual.values.astype(float)
                    years = annual["year"].values.astype(float)
                    from src.places.analysis import trend_from_series, inside_place_shares, is_divergent
                    slope, p, n = trend_from_series(series, years, min_years)
                    ilat = int(np.argmin(np.abs(ds["lat"].values - lat)))
                    ilon = int(np.argmin(np.abs(ds["lon"].values - lon)))
                    shares = {"n_cells": 1, "up": 1.0 if slope > 0 and math.isfinite(slope) else 0.0,
                              "down": 1.0 if slope < 0 and math.isfinite(slope) else 0.0,
                              "none": 1.0 if not math.isfinite(slope) or slope == 0 else 0.0}
                    if math.isfinite(slope):
                        cls_val = float(pt["class"]) if math.isfinite(float(pt["class"])) else 0.0
                        shares = {"n_cells": 1, "up": 1.0 if cls_val > 0 else 0.0, "down": 1.0 if cls_val < 0 else 0.0, "none": 1.0 if cls_val == 0 else 0.0}
                    if not math.isfinite(slope):
                        res = {"applies": math.isfinite(float(pt["slope_per_decade"])) or np.any(np.isfinite(series)),
                               "slope_per_year": None, "slope_per_decade": None, "p_value": None,
                               "significant": False, "n_years": n, "n_cells": 1, "coverage": 1.0,
                               "low_confidence": False, "std_trend": None, "inside_place": shares,
                               "divergent": False, "scale": "grid_cell", "series": series, "years": years}
                        if not res["applies"]:
                            res["reason"] = "no_valid_data"
                    else:
                        std = float(np.nanstd(series))
                        std_trend = float((slope * 10) / std) if std > 0 and math.isfinite(std) else 0.0
                        res = {
                            "applies": True, "slope_per_year": float(slope), "slope_per_decade": float(slope * 10),
                            "p_value": float(p) if math.isfinite(p) else None, "significant": False,
                            "n_years": int(n), "n_cells": 1, "coverage": 1.0,
                            "low_confidence": bool(n < ok_years), "std_trend": std_trend,
                            "inside_place": shares, "divergent": False, "scale": "grid_cell",
                            "series": series, "years": years,
                        }
                    place_result["variables"][var] = res
                    by_level_var_p.setdefault((level, var), []).append((pid, res.get("p_value")))
            all_results[pid] = place_result
            if idx % 25 == 0 or idx == len(places):
                print(f"  {idx}/{len(places)}")

    # FDR across places per level/variable
    for (level, var), items in by_level_var_p.items():
        pvals = np.array([p if p is not None and math.isfinite(p) else np.nan for _, p in items], dtype=float)
        sig = fdr_significant(pvals, alpha=alpha)
        for (pid, _), is_sig in zip(items, sig):
            if pid in all_results and var in all_results[pid]["variables"]:
                all_results[pid]["variables"][var]["significant"] = bool(is_sig)
                all_results[pid]["variables"][var]["fdr_corrected"] = True

    # serialize (drop heavy intermediates kept only as arrays? keep series for charts)
    serial = {}
    for pid, pres in all_results.items():
        out = {k: v for k, v in pres.items() if k != "variables"}
        out["variables"] = {var: serialize_result(res) for var, res in pres["variables"].items()}
        out["synthetic"] = cfg.mode == "synthetic"
        serial[pid] = out

    meta = {
        "mode": cfg.mode,
        "synthetic": cfg.mode == "synthetic",
        "built_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "levels": levels,
        "variables": list(datasets.keys()),
        "min_years": min_years,
        "ok_years": ok_years,
        "alpha": alpha,
        "min_coverage": args.min_coverage,
        "n_places": len(serial),
    }
    (out_dir / "place_results.json").write_text(json.dumps({"meta": meta, "places": serial}, ensure_ascii=False), encoding="utf-8")
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"\nWrote {len(serial)} place results to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
