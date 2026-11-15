"""Load gazetteer and precomputed place results for API lookups."""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from src.api.layer_store import LayerStore
from src.common.config import REPO_ROOT
from src.places.analysis import build_place_report_from_results, inside_place_sentence
from src.places.gazetteer import Gazetteer, load_gazetteer
from src.skills.change_report import _as_bool


class PlaceStore:
    def __init__(self, layer_store: LayerStore, *, gazetteer_dir: Path | None = None, results_dir: Path | None = None):
        self.layer_store = layer_store
        self.gazetteer_dir = Path(gazetteer_dir) if gazetteer_dir else REPO_ROOT / "data/places/gazetteer"
        self.results_dir = Path(results_dir) if results_dir else REPO_ROOT / "layers/places" / layer_store.cfg.mode
        self.gazetteer: Gazetteer | None = None
        self.results: dict[str, dict] = {}
        self.meta: dict[str, Any] = {}
        self.errors: list[str] = []
        self.loaded = False

    def load(self) -> "PlaceStore":
        self.errors.clear()
        self.results.clear()
        self.gazetteer = None
        try:
            if self.gazetteer_dir.exists():
                self.gazetteer = load_gazetteer(self.gazetteer_dir)
            else:
                self.errors.append(f"missing gazetteer: {self.gazetteer_dir}")
        except Exception as exc:
            self.errors.append(f"could not load gazetteer: {type(exc).__name__}: {exc}")
            self.gazetteer = None
        path = self.results_dir / "place_results.json"
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                self.meta = data.get("meta", {})
                self.results = data.get("places", {})
            except Exception as exc:
                self.errors.append(f"could not load {path}: {exc}")
        else:
            self.errors.append(f"missing place results: {path}")
        self.loaded = True
        return self

    @property
    def available(self) -> bool:
        return self.gazetteer is not None

    def search(self, q: str, level: str | None = None, limit: int = 10) -> list[dict]:
        if not self.gazetteer:
            return []
        limit = max(1, min(limit, 50))
        return self.gazetteer.search(q, level=level, limit=limit)

    def resolve(self, lat: float, lon: float, level: str) -> dict[str, Any]:
        if not self.gazetteer:
            return {"place": None, "level": level, "error": "gazetteer not loaded"}
        return self.gazetteer.resolve(lat, lon, level)

    def place_detail(self, place_id: str) -> dict[str, Any] | None:
        if not self.gazetteer:
            return None
        feat = self.gazetteer.to_feature(place_id, simplified=True)
        if not feat:
            return None
        props = feat["properties"]
        has_results = place_id in self.results
        return {
            "place": {k: props.get(k) for k in ("id", "name", "level", "hierarchy", "centroid", "bbox", "parent_ids", "alt_names", "name_native")},
            "geometry": feat["geometry"],
            "has_results": has_results,
        }

    def report(self, place_id: str) -> dict[str, Any] | None:
        if not self.gazetteer:
            return None
        place = self.gazetteer.get(place_id)
        if not place:
            return None
        pres = self.results.get(place_id)
        if not pres:
            # fallback: grid-cell report at centroid for point-ish lookup
            c = place.get("centroid") or [0, 0]
            rep = self.layer_store.report(c[1], c[0], window=float(self.layer_store.cfg.analysis.get("nearby_window_deg", 5.0)))
            rep["place"] = {k: place.get(k) for k in ("id", "name", "level", "hierarchy", "centroid", "bbox")}
            rep["scale"] = "grid_cell"
            rep["fallback"] = "point_lookup_at_centroid"
            rep["inside_place"] = None
            rep["divergent"] = False
            rep["neighbors"] = []
            rep["neighbor_summary"] = ""
            if self.layer_store.synthetic:
                rep["synthetic"] = True
                rep["synthetic_banner"] = "SYNTHETIC DEMO DATA, not real observations."
            return rep

        datasets = self.layer_store.datasets
        results_by_var = pres.get("variables", {})
        rep = build_place_report_from_results(place, results_by_var, datasets=datasets, neighbors=[])
        rep["mode"] = self.layer_store.cfg.mode
        rep["synthetic"] = self.layer_store.synthetic or bool(pres.get("synthetic"))
        if rep["synthetic"]:
            rep["synthetic_banner"] = "SYNTHETIC DEMO DATA, not real observations."
        rep["coverage_note"] = "Regional values are area-weighted averages of precomputed grid-cell trends."
        return rep

    def timeseries(self, place_id: str, variable: str) -> dict[str, Any] | None:
        if not self.gazetteer:
            return None
        place = self.gazetteer.get(place_id)
        if not place:
            return None
        pres = self.results.get(place_id)
        ds = self.layer_store.datasets.get(variable)
        if ds is None:
            raise KeyError(variable)
        display = ds.attrs.get("display_name", variable)
        unit = ds.attrs.get("units", "")
        if not pres or variable not in pres.get("variables", {}):
            c = place.get("centroid") or [0, 0]
            ts = self.layer_store.timeseries(variable, c[1], c[0])
            ts["place"] = {k: place.get(k) for k in ("id", "name", "level", "hierarchy")}
            ts["scale"] = "grid_cell"
            ts["fallback"] = "point_lookup_at_centroid"
            return ts
        res = pres["variables"][variable]
        years = [int(y) for y in (res.get("years") or [])]
        series_vals = res.get("series") or []
        values = [None if v is None or (isinstance(v, float) and not math.isfinite(v)) else float(v) for v in series_vals]
        slope_year = res.get("slope_per_year")
        slope_decade = res.get("slope_per_decade")
        applies = bool(res.get("applies", True)) and slope_year is not None and math.isfinite(float(slope_year))
        if not applies:
            return {
                "key": variable, "variable": display, "unit": unit,
                "place": {k: place.get(k) for k in ("id", "name", "level", "hierarchy")},
                "applies": False, "years": [], "annual_anomaly": [], "trend_line": [],
                "slope_per_year": None, "slope_per_decade": None, "standardized_trend": None,
                "significant": False, "class": None, "verdict": "no data for this variable in this place",
                "n_years": int(res.get("n_years", 0)), "low_confidence": bool(res.get("low_confidence", False)),
                "alpha": ds.attrs.get("alpha"), "fdr_corrected": True,
                "model_based": _as_bool(ds.attrs.get("model_based", False)),
                "synthetic": _as_bool(ds.attrs.get("synthetic", False)) or self.layer_store.synthetic,
                "period": [ds.attrs.get("period_start"), ds.attrs.get("period_end")],
                "scale": res.get("scale", "region_average"),
                "summary": f"{display} does not apply in this place; no data are available in this layer.",
                "not_a_forecast": "Observed change only, not a forecast.",
            }
        finite = [(y, v) for y, v in zip(years, values) if v is not None]
        line = [None] * len(years)
        if finite:
            med_y = float(np.median([y for y, _ in finite]))
            med_v = float(np.median([v for _, v in finite]))
            line = [med_v + float(slope_year) * (y - med_y) for y in years]
        significant = bool(res.get("significant", False))
        cls = 1 if float(slope_decade) > 0 else -1 if float(slope_decade) < 0 else 0
        if significant and cls > 0:
            verdict = "significant increase"
        elif significant and cls < 0:
            verdict = "significant decrease"
        else:
            verdict = "no statistically significant change detected"
        return {
            "key": variable, "variable": display, "unit": unit,
            "place": {k: place.get(k) for k in ("id", "name", "level", "hierarchy")},
            "applies": True, "years": years, "annual_anomaly": values, "trend_line": line,
            "trend_line_note": "Theil–Sen line reconstructed from the stored regional slope and the median of the regional annual anomalies.",
            "slope_per_year": float(slope_year), "slope_per_decade": float(slope_decade),
            "standardized_trend": float(res.get("std_trend")) if res.get("std_trend") is not None else None,
            "significant": significant, "class": cls if significant else 0,
            "verdict": verdict, "n_years": int(res.get("n_years", 0)),
            "low_confidence": bool(res.get("low_confidence", False)),
            "alpha": ds.attrs.get("alpha"), "fdr_corrected": True,
            "model_based": _as_bool(ds.attrs.get("model_based", False)),
            "synthetic": _as_bool(ds.attrs.get("synthetic", False)) or self.layer_store.synthetic,
            "period": [ds.attrs.get("period_start"), ds.attrs.get("period_end")],
            "scale": res.get("scale", "region_average"),
            "n_cells": res.get("n_cells"), "coverage": res.get("coverage"),
            "summary": f"Regional series for {place.get('name')}: {verdict}.",
            "not_a_forecast": "Observed change only, not a forecast.",
        }
