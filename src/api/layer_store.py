"""Load precomputed trend layers once and answer point lookups from them.

Nothing here downloads from NASA or computes a trend on demand.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import xarray as xr

from src.common.config import AppConfig, variable_meta
from src.skills.change_report import build_report, sentence, _as_bool


REQUIRED_LAYER_FIELDS = {
    "slope_per_year", "slope_per_decade", "p_value", "significant",
    "class", "std_trend", "n_years", "low_confidence", "annual_anomaly",
}


class LayerStore:
    """In-memory layer set for exactly one mode (synthetic or real)."""

    def __init__(self, cfg: AppConfig, *, layers_dir: Path | None = None,
                 overlays_dir: Path | None = None) -> None:
        self.cfg = cfg
        self.layers_dir = Path(layers_dir) if layers_dir else cfg.layers_dir
        self.overlays_dir = Path(overlays_dir) if overlays_dir else cfg.overlays_dir / cfg.mode
        self.datasets: dict[str, xr.Dataset] = {}
        self.overlay_metadata: dict[str, Any] | None = None
        self.errors: list[str] = []
        self.loaded = False

    # ------------------------------------------------------------------ loading
    def load(self) -> "LayerStore":
        self.datasets.clear()
        self.errors.clear()
        for key in self.cfg.mode_variables():
            path = self.layers_dir / f"{key}_trend.zarr"
            if not path.exists():
                self.errors.append(f"missing trend layer: {path}")
                continue
            try:
                ds = xr.open_zarr(path).load()
                missing = REQUIRED_LAYER_FIELDS - set(ds.data_vars)
                if missing:
                    raise ValueError(f"layer {path} lacks fields {sorted(missing)}")
                ds.attrs["variable"] = key
                self.datasets[key] = ds
            except Exception as exc:
                self.errors.append(f"could not load {path}: {type(exc).__name__}: {exc}")
        meta_path = self.overlays_dir / "metadata.json"
        if meta_path.exists():
            try:
                self.overlay_metadata = json.loads(meta_path.read_text(encoding="utf-8"))
            except Exception as exc:
                self.errors.append(f"could not read {meta_path}: {exc}")
        else:
            self.errors.append(f"missing overlay metadata: {meta_path}")
        self.loaded = True
        return self

    @property
    def available(self) -> bool:
        return bool(self.datasets)

    @property
    def synthetic(self) -> bool:
        return self.cfg.mode == "synthetic" or any(
            _as_bool(ds.attrs.get("synthetic", False)) for ds in self.datasets.values()
        )

    @property
    def grid(self) -> dict[str, Any] | None:
        if not self.datasets:
            return None
        ds = next(iter(self.datasets.values()))
        return {
            "resolution_deg": self.cfg.resolution,
            "n_lat": int(ds.sizes["lat"]),
            "n_lon": int(ds.sizes["lon"]),
            "lat_range": [float(ds["lat"].min()), float(ds["lat"].max())],
            "lon_range": [float(ds["lon"].min()), float(ds["lon"].max())],
        }

    # --------------------------------------------------------------- metadata
    def variables_payload(self) -> dict[str, Any]:
        variables = []
        for key, ds in self.datasets.items():
            meta = variable_meta(self.cfg, key)
            valid = ds["slope_per_year"].notnull()
            n_valid = int(valid.sum())
            low_share = (
                float(ds["low_confidence"].where(valid).mean()) if n_valid else None
            )
            variables.append({
                "key": key,
                "display_name": ds.attrs.get("display_name", meta["display_name"]),
                "unit": ds.attrs.get("units", meta["unit"]),
                "surface": meta["surface"],
                "model_based": _as_bool(ds.attrs.get("model_based", meta["model_based"])),
                "model_note": "Model-based reanalysis, not a direct observation." if _as_bool(ds.attrs.get("model_based", meta["model_based"])) else None,
                "synthetic": _as_bool(ds.attrs.get("synthetic", False)),
                "period": [ds.attrs.get("period_start"), ds.attrs.get("period_end")],
                "requested_period": list(self.cfg.period),
                "min_years": ds.attrs.get("min_years"),
                "ok_years": ds.attrs.get("ok_years"),
                "alpha": ds.attrs.get("alpha"),
                "low_confidence_share": low_share,
                "missing_months": [m for m in str(ds.attrs.get("missing_months", "")).split(",") if m],
                "source_dataset": ds.attrs.get("source_dataset", ""),
                "dataset_version": ds.attrs.get("dataset_version", ""),
                "doi": ds.attrs.get("doi", ""),
                "record_note": ds.attrs.get("model_note", ""),
                "n_cells_with_trend": ds.attrs.get("n_cells_with_trend"),
                "n_cells_significant": ds.attrs.get("n_cells_significant"),
            })
        return {
            "mode": self.cfg.mode,
            "synthetic": self.synthetic,
            "synthetic_banner": "SYNTHETIC DEMO DATA, not real observations." if self.synthetic else None,
            "grid": self.grid,
            "period": list(self.cfg.period),
            "analysis": self.cfg.analysis,
            "variables": variables,
            "not_a_forecast": "Observed change only, not a forecast.",
        }

    def layers_payload(self) -> dict[str, Any]:
        if not self.overlay_metadata:
            raise FileNotFoundError(
                "Overlay metadata is missing. Run `make pipeline` (or "
                "`python scripts/export_overlays.py`) before starting the API."
            )
        return self.overlay_metadata

    # ----------------------------------------------------------------- queries
    def _nearest_cell(self, lat: float, lon: float) -> dict[str, float] | None:
        if not self.datasets:
            return None
        ds = next(iter(self.datasets.values()))
        pt = ds.sel(lat=lat, lon=lon, method="nearest")
        return {"lat": float(pt["lat"]), "lon": float(pt["lon"])}

    def report(self, lat: float, lon: float, window: float) -> dict[str, Any]:
        layers = {key: str(self.layers_dir / f"{key}_trend.zarr") for key in self.datasets}
        rep = build_report(lat, lon, layers, window=window, datasets=self.datasets)
        cell = rep["variables"][0]["cell"] if rep["variables"] else self._nearest_cell(lat, lon)
        rep["cell"] = cell
        rep["surface_inferred"] = self._infer_surface(rep["variables"])
        rep["mode"] = self.cfg.mode
        rep["synthetic"] = self.synthetic
        if self.synthetic:
            rep["synthetic_banner"] = "SYNTHETIC DEMO DATA, not real observations."
        return rep

    def _infer_surface(self, rows: list[dict[str, Any]]) -> dict[str, str]:
        if not rows:
            return {
                "value": "unknown",
                "explanation": "No variable in this layer set applies at this location.",
            }
        land_only = [r for r in rows if r.get("surface") == "land"]
        if land_only:
            return {
                "value": "land",
                "explanation": "At least one land-only variable (vegetation or water storage) applies here.",
            }
        return {
            "value": "ocean_or_ice_or_no_land_data",
            "explanation": "Only variables that cover both land and ocean apply here; the surface type is not independently verified.",
        }

    def timeseries(self, key: str, lat: float, lon: float) -> dict[str, Any]:
        if key not in self.datasets:
            raise KeyError(key)
        ds = self.datasets[key]
        pt = ds.sel(lat=lat, lon=lon, method="nearest")
        annual = pt["annual_anomaly"]
        years = [int(y) for y in annual["year"].values]
        values = [None if not np.isfinite(float(v)) else float(v) for v in annual.values]
        slope_year = float(pt["slope_per_year"])
        slope_decade = float(pt["slope_per_decade"])
        unit = ds.attrs.get("units", "")
        display = ds.attrs.get("display_name", key)
        if not math.isfinite(slope_year):
            return {
                "key": key,
                "variable": display,
                "unit": unit,
                "cell": {"lat": float(pt["lat"]), "lon": float(pt["lon"])},
                "applies": False,
                "years": [],
                "annual_anomaly": [],
                "trend_line": [],
                "slope_per_year": None,
                "slope_per_decade": None,
                "standardized_trend": None,
                "significant": False,
                "class": None,
                "verdict": "no data for this variable at this location",
                "n_years": int(pt["n_years"]),
                "low_confidence": False,
                "alpha": ds.attrs.get("alpha"),
                "fdr_corrected": True,
                "model_based": _as_bool(ds.attrs.get("model_based", False)),
                "synthetic": _as_bool(ds.attrs.get("synthetic", False)),
                "period": [ds.attrs.get("period_start"), ds.attrs.get("period_end")],
                "summary": f"{display} does not apply at this location; no data are available in this layer.",
                "not_a_forecast": "Observed change only, not a forecast.",
            }
        finite = [(y, v) for y, v in zip(years, values) if v is not None]
        line: list[float | None] = [None] * len(years)
        if finite:
            med_y = float(np.median([y for y, _ in finite]))
            med_v = float(np.median([v for _, v in finite]))
            line = [med_v + slope_year * (y - med_y) for y in years]
        significant = bool(pt["significant"])
        cls = float(pt["class"])
        if significant and cls > 0:
            verdict = "significant increase"
        elif significant and cls < 0:
            verdict = "significant decrease"
        else:
            verdict = "no statistically significant change detected"
        row = {
            "variable": display,
            "rate_per_decade": slope_decade,
            "n_years": int(pt["n_years"]),
            "significant": significant,
            "low_confidence": bool(pt["low_confidence"]),
        }
        return {
            "key": key,
            "variable": display,
            "unit": unit,
            "cell": {"lat": float(pt["lat"]), "lon": float(pt["lon"])},
            "applies": True,
            "years": years,
            "annual_anomaly": values,
            "trend_line": line,
            "trend_line_note": "Theil-Sen line reconstructed from the stored slope and the median of the annual anomalies.",
            "slope_per_year": slope_year,
            "slope_per_decade": slope_decade,
            "standardized_trend": float(pt["std_trend"]) if math.isfinite(float(pt["std_trend"])) else None,
            "significant": significant,
            "class": int(cls) if math.isfinite(cls) else None,
            "verdict": verdict,
            "n_years": int(pt["n_years"]),
            "low_confidence": bool(pt["low_confidence"]),
            "alpha": ds.attrs.get("alpha"),
            "fdr_corrected": True,
            "model_based": _as_bool(ds.attrs.get("model_based", False)),
            "synthetic": _as_bool(ds.attrs.get("synthetic", False)),
            "period": [ds.attrs.get("period_start"), ds.attrs.get("period_end")],
            "summary": sentence(row, unit),
            "not_a_forecast": "Observed change only, not a forecast.",
        }
