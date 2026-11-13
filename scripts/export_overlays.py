#!/usr/bin/env python3
"""Turn trend layers into Web-Mercator PNG overlays for the map.

Outputs per mode (never mixed):
  change_score.png        number of variables with a significant change
  <var>_class.png         blue = significant increase, orange = significant decrease,
                          transparent = no significant change or no applicable data
  <var>_std_trend.png     continuous diverging strength view

Plus metadata.json with bounds, legends, units, and provenance for the API.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np
import xarray as xr
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.common.config import load_app_config  # noqa: E402

# Colour-blind-safe blue/orange pair; never red/green.
BLUE = np.array([31, 119, 180], dtype=float)
ORANGE = np.array([255, 127, 14], dtype=float)
SCORE_COLORS = np.array([
    [255, 255, 204],   # 1 variable
    [161, 218, 180],   # 2
    [65, 182, 196],    # 3
    [34, 94, 168],     # 4
    [37, 52, 148],     # 5+
], dtype=float)


def mercator_y(lat_deg: np.ndarray | float) -> np.ndarray | float:
    return np.log(np.tan(np.pi / 4 + np.deg2rad(lat_deg) / 2))


def inverse_mercator_y(y: np.ndarray | float) -> np.ndarray | float:
    return np.rad2deg(2 * np.arctan(np.exp(y)) - np.pi / 2)


def mercator_lat_grid(lat_limit: float, height: int) -> np.ndarray:
    """Evenly spaced rows in Web Mercator, returned as latitudes (north to south)."""
    y_top, y_bottom = mercator_y(lat_limit), mercator_y(-lat_limit)
    ys = np.linspace(y_top, y_bottom, height)
    return inverse_mercator_y(ys)


def resample_to_mercator(data: np.ndarray, lat: np.ndarray, height: int, lat_limit: float = 85.0) -> np.ndarray:
    """Nearest-row resampling from regular latitude rows to even Mercator rows."""
    out_lat = mercator_lat_grid(lat_limit, height)
    idx = np.abs(lat[None, :] - out_lat[:, None]).argmin(axis=1)
    return data[idx, :]


def class_rgba(classes: np.ndarray) -> np.ndarray:
    rgba = np.zeros(classes.shape + (4,), dtype=np.uint8)
    inc = classes == 1
    dec = classes == -1
    rgba[inc, :3] = BLUE.astype(np.uint8)
    rgba[inc, 3] = 225
    rgba[dec, :3] = ORANGE.astype(np.uint8)
    rgba[dec, 3] = 225
    return rgba


def std_trend_rgba(std: np.ndarray, vmax: float = 3.0) -> np.ndarray:
    """Diverging orange (decrease) - transparent zero - blue (increase)."""
    rgba = np.zeros(std.shape + (4,), dtype=np.uint8)
    finite = np.isfinite(std)
    if not finite.any():
        return rgba
    clipped = np.clip(std, -vmax, vmax)
    frac = np.abs(clipped) / vmax
    base = np.where(clipped[..., None] >= 0, BLUE[None, None, :], ORANGE[None, None, :])
    rgba[..., :3] = np.clip(base, 0, 255).astype(np.uint8)
    alpha = np.where(finite & (clipped != 0), np.clip(20 + 235 * frac, 0, 255), 0)
    rgba[..., 3] = alpha.astype(np.uint8)
    return rgba


def score_rgba(score: np.ndarray, max_count: int) -> np.ndarray:
    rgba = np.zeros(score.shape + (4,), dtype=np.uint8)
    for count in range(1, max_count + 1):
        color = SCORE_COLORS[min(count - 1, len(SCORE_COLORS) - 1)]
        sel = score == count
        rgba[sel, :3] = color.astype(np.uint8)
        rgba[sel, 3] = 230
    return rgba


def save_png(path: Path, rgba: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgba, mode="RGBA").save(path, optimize=True)


def class_legend() -> list[dict]:
    return [
        {"label": "Significant increase", "color": "#1f77b4", "opacity": 0.9, "symbol": "up"},
        {"label": "Significant decrease", "color": "#ff7f0e", "opacity": 0.9, "symbol": "down"},
        {"label": "No significant change or no data", "color": "transparent", "opacity": 0.0},
    ]


def std_legend(unit: str) -> dict:
    return {
        "type": "gradient",
        "label": f"Standardized trend (slope per decade / interannual variability), {unit}",
        "stops": [
            {"value": -3, "color": "#ff7f0e", "label": "strong decrease"},
            {"value": -1.5, "color": "#ffb366", "label": ""},
            {"value": 0, "color": "transparent", "label": "0"},
            {"value": 1.5, "color": "#66b3d9", "label": ""},
            {"value": 3, "color": "#1f77b4", "label": "strong increase"},
        ],
        "note": "Values are clipped at +/-3; faint cells have weak trends.",
    }


def score_legend(max_count: int) -> list[dict]:
    labels = {1: "1 variable", 2: "2 variables", 3: "3 variables", 4: "4 variables", 5: "5+ variables"}
    out = [{"label": "No significant change or no data", "color": "transparent", "opacity": 0.0, "count": 0}]
    for count in range(1, max_count + 1):
        color = SCORE_COLORS[min(count - 1, len(SCORE_COLORS) - 1)]
        out.append({
            "label": labels.get(count, f"{count} variables"),
            "color": "#{:02x}{:02x}{:02x}".format(*[int(c) for c in color]),
            "opacity": 0.9,
            "count": count,
        })
    return out


def export_mode(cfg, *, layers_dir: Path, out_dir: Path, only: set[str] | None = None) -> dict:
    variables = [v for v in cfg.mode_variables() if not only or v in only]
    present = []
    for var in variables:
        path = layers_dir / f"{var}_trend.zarr"
        if path.exists():
            present.append((var, path))
        else:
            print(f"WARNING: missing layer {path}; skipping {var}")
    if not present:
        raise SystemExit(f"No trend layers found in {layers_dir}")

    reference = xr.open_zarr(present[0][1])
    lat = reference["lat"].values
    lon = reference["lon"].values
    for var, path in present[1:]:
        other = xr.open_zarr(path)
        if not (np.allclose(other["lat"].values, lat) and np.allclose(other["lon"].values, lon)):
            raise SystemExit(f"Grid mismatch: {var} does not share the reference grid")

    lat_limit = float(cfg.raw["grid"]["mercator_lat_limit"])
    height = int(cfg.raw["grid"]["overlay_height_px"])
    width = len(lon)
    bounds = [-180.0, -lat_limit, 180.0, lat_limit]
    out_dir.mkdir(parents=True, exist_ok=True)

    layers: dict[str, dict] = {}
    score = np.zeros((len(lat), len(lon)), dtype=np.int16)
    std_available = np.zeros_like(score, dtype=bool)
    any_synthetic = False
    variable_meta = []
    for var, path in present:
        ds = xr.open_zarr(path)
        classes = ds["class"].values.astype(float)
        std = ds["std_trend"].values.astype(float)
        sig = np.isfinite(classes) & (classes != 0)
        score[sig] = score[sig] + 1
        std_available |= np.isfinite(std)
        attrs = ds.attrs
        synthetic = bool(attrs.get("synthetic", False))
        any_synthetic = any_synthetic or synthetic
        meta = cfg.variables[var]
        unit = attrs.get("units", meta["unit"])
        display = attrs.get("display_name", meta["display_name"])

        class_png = out_dir / f"{var}_class.png"
        save_png(class_png, class_rgba(resample_to_mercator(classes, lat, height, lat_limit)))
        layers[f"{var}_class"] = {
            "id": f"{var}_class",
            "variable": var,
            "display_name": display,
            "kind": "class",
            "url": f"/overlays/{cfg.mode}/{class_png.name}",
            "bounds": bounds,
            "units": unit,
            "model_based": bool(attrs.get("model_based", meta["model_based"])),
            "synthetic": synthetic,
            "legend": class_legend(),
            "meaning": "Blue: statistically significant increase after FDR; orange: significant decrease; transparent: not significant or no data.",
        }

        std_png = out_dir / f"{var}_std_trend.png"
        save_png(std_png, std_trend_rgba(resample_to_mercator(std, lat, height, lat_limit)))
        layers[f"{var}_std_trend"] = {
            "id": f"{var}_std_trend",
            "variable": var,
            "display_name": f"{display} (strength)",
            "kind": "std_trend",
            "url": f"/overlays/{cfg.mode}/{std_png.name}",
            "bounds": bounds,
            "units": unit,
            "model_based": bool(attrs.get("model_based", meta["model_based"])),
            "synthetic": synthetic,
            "legend": std_legend(unit),
            "meaning": "Continuous standardized trend: slope per decade divided by the variable's interannual variability. Weak trends are faint; values clipped at +/-3.",
        }
        variable_meta.append({
            "key": var,
            "display_name": display,
            "unit": unit,
            "model_based": bool(attrs.get("model_based", meta["model_based"])),
            "synthetic": synthetic,
            "period": [attrs.get("period_start"), attrs.get("period_end")],
            "min_years": attrs.get("min_years"),
            "ok_years": attrs.get("ok_years"),
            "alpha": attrs.get("alpha"),
            "n_cells_with_trend": attrs.get("n_cells_with_trend"),
            "n_cells_significant": attrs.get("n_cells_significant"),
            "missing_months": attrs.get("missing_months", ""),
            "source": attrs.get("source", ""),
            "source_dataset": attrs.get("source_dataset", ""),
            "dataset_version": attrs.get("dataset_version", ""),
            "doi": attrs.get("doi", ""),
        })

    max_count = max(1, len(present))
    resampled_score = resample_to_mercator(score.astype(float), lat, height, lat_limit).astype(np.int16)
    score_png = out_dir / "change_score.png"
    save_png(score_png, score_rgba(resampled_score, max_count))
    layers = {
        "change_score": {
            "id": "change_score",
            "kind": "change_score",
            "display_name": "Change score",
            "url": f"/overlays/{cfg.mode}/{score_png.name}",
            "bounds": bounds,
            "units": f"number of variables (of {len(present)}) with a significant change",
            "synthetic": any_synthetic,
            "legend": score_legend(max_count),
            "meaning": "Count of variables with a statistically significant change (after FDR) in each cell. Transparent means none or no applicable data.",
        },
        **layers,
    }
    metadata = {
        "mode": cfg.mode,
        "synthetic": any_synthetic,
        "warning": "SYNTHETIC DEMO DATA, not real observations." if any_synthetic else None,
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "projection": "Web Mercator rows; image bounds are west/south/east/north in EPSG:4326",
        "bounds": bounds,
        "image": {"width": int(width), "height": int(height), "mercator_lat_limit": lat_limit},
        "grid": {"resolution_deg": cfg.resolution, "n_lat_native": int(len(lat)), "n_lon": int(len(lon))},
        "period": list(cfg.period),
        "variables": variable_meta,
        "layers": layers,
        "default_layer": "change_score",
        "attribution": "Trend statistics: Theil-Sen + Hamed-Rao Mann-Kendall + BH-FDR. Base geography: Natural Earth.",
    }
    (out_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"Wrote {len(layers)} overlays to {out_dir}")
    return metadata


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mode", choices=["synthetic", "real"], default=None)
    ap.add_argument("--config", default=str(REPO_ROOT / "config" / "app.yaml"))
    ap.add_argument("--layers-dir", default=None)
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--only", default=None, help="Comma-separated variable keys")
    args = ap.parse_args()

    cfg = load_app_config(args.config)
    if args.mode:
        cfg = type(cfg)(raw=cfg.raw, mode=args.mode)
    layers_dir = Path(args.layers_dir) if args.layers_dir else cfg.layers_dir
    out_dir = Path(args.out_dir) if args.out_dir else cfg.overlays_dir / cfg.mode
    only = {v.strip() for v in args.only.split(",") if v.strip()} if args.only else None
    meta = export_mode(cfg, layers_dir=layers_dir, out_dir=out_dir, only=only)
    if meta["synthetic"]:
        print("SYNTHETIC DEMO DATA, not real observations.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
