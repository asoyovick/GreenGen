"""Gazetteer build, search, and point resolution."""
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .geojson_utils import (
    bbox_contains,
    bbox_of_geom,
    centroid_of_geom,
    geom_area_deg2,
    geom_crosses_antimeridian,
    normalize_text,
    point_in_geom,
    shift_geom_lon,
    simplify_geom,
    slugify,
)

LEVEL_ORDER = {"country": 0, "region": 1, "city": 2, "sea": 3}
LEVEL_RANK = {"country": 0, "region": 1, "city": 2, "sea": 3}


def _pick(props: dict, *keys: str, default=None):
    for k in keys:
        if k in props and props[k] not in (None, ""):
            return props[k]
    return default


def _alt_names(props: dict) -> list[str]:
    vals = []
    for k, v in props.items():
        if v in (None, ""):
            continue
        lk = k.lower()
        if lk.startswith("name_") or lk in {"namealt", "name_alt", "nameascii", "namepar", "abbrev", "woe_name", "brk_name", "formal_en"}:
            if isinstance(v, str):
                vals.append(v)
    out, seen = [], set()
    for v in vals:
        n = normalize_text(v)
        if n and n not in seen:
            seen.add(n)
            out.append(v)
    return out


@dataclass
class Place:
    id: str
    name: str
    level: str
    record: dict[str, Any]
    geom: dict[str, Any]
    bbox: list[float]

    def contains(self, lon: float, lat: float) -> bool:
        # antimeridian handling: test shifted copies when bbox is wide
        if not bbox_contains(self.bbox, lon, lat) and not geom_crosses_antimeridian(self.geom):
            return False
        if point_in_geom(lon, lat, self.geom):
            return True
        if geom_crosses_antimeridian(self.geom):
            for delta in (360.0, -360.0):
                g = shift_geom_lon(self.geom, delta)
                b = bbox_of_geom(g)
                if bbox_contains(b, lon, lat) and point_in_geom(lon, lat, g):
                    return True
                # also try shifted query point
                if point_in_geom(lon + delta, lat, self.geom):
                    return True
        return False


def make_id(prefix: str, name: str, source_id: Any) -> str:
    base = slugify(name) or "place"
    sid = re.sub(r"[^a-z0-9]+", "-", str(source_id or "").casefold()).strip("-")
    return f"{prefix}:{sid or base}"


def build_country_records(path: Path) -> list[tuple[dict, dict]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for feat in data.get("features", []):
        props = feat.get("properties") or {}
        geom = feat.get("geometry")
        if not geom:
            continue
        name = _pick(props, "NAME_EN", "NAME_LONG", "NAME", "ADMIN", default="Unknown country")
        source_id = _pick(props, "ADM0_A3", "ISO_A3", "SOV_A3", "NE_ID", default=slugify(name))
        rec = {
            "id": make_id("country", name, source_id),
            "name": name,
            "name_native": _pick(props, "NAME"),
            "alt_names": _alt_names(props),
            "level": "country",
            "parent_ids": [],
            "hierarchy": name,
            "iso_a3": _pick(props, "ADM0_A3", "ISO_A3"),
            "continent": _pick(props, "CONTINENT"),
            "population": _pick(props, "POP_EST"),
            "source_id": source_id,
        }
        out.append((rec, geom))
    return out


def build_region_records(path: Path, countries: list[tuple[dict, dict]]) -> list[tuple[dict, dict]]:
    by_iso = {}
    for rec, _ in countries:
        iso = (rec.get("iso_a3") or "").upper()
        if iso:
            by_iso[iso] = rec
    data = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for feat in data.get("features", []):
        props = feat.get("properties") or {}
        geom = feat.get("geometry")
        if not geom:
            continue
        name = _pick(props, "name_en", "name", "woe_name", "gn_name", default="Unknown region")
        adm0 = (_pick(props, "adm0_a3", "gu_a3", default="") or "").upper()
        source_id = _pick(props, "adm1_code", "diss_me", "ne_id", default=slugify(name))
        country = by_iso.get(adm0)
        parent_ids = [country["id"]] if country else []
        country_name = country["name"] if country else _pick(props, "admin", default=None)
        hierarchy = f"{name} › {country_name}" if country_name else name
        rec = {
            "id": make_id("region", name, source_id),
            "name": name,
            "name_native": _pick(props, "name"),
            "alt_names": _alt_names(props),
            "level": "region",
            "parent_ids": parent_ids,
            "hierarchy": hierarchy,
            "country": country_name,
            "adm0_a3": adm0,
            "population": None,
            "source_id": source_id,
        }
        out.append((rec, geom))
    return out


def build_city_records(path: Path, countries: list[tuple[dict, dict]], regions: list[tuple[dict, dict]]) -> list[tuple[dict, dict]]:
    by_iso = {((r.get("iso_a3") or "").upper()): r for r, _ in countries}
    # simple region lookup by (adm0,name)
    region_lookup = {}
    for rec, _ in regions:
        key = ((rec.get("adm0_a3") or "").upper(), normalize_text(rec.get("name")))
        region_lookup[key] = rec
    data = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for feat in data.get("features", []):
        props = feat.get("properties") or {}
        geom = feat.get("geometry")
        if not geom:
            continue
        name = _pick(props, "name", "nameascii", "name_en", default="Unknown place")
        adm0 = (_pick(props, "adm0_a3", "sov_a3", default="") or "").upper()
        source_id = _pick(props, "ne_id", default=slugify(name))
        country = by_iso.get(adm0)
        adm1 = _pick(props, "adm1name", default=None)
        region = region_lookup.get((adm0, normalize_text(adm1))) if adm1 else None
        parents = []
        if region:
            parents.append(region["id"])
        if country:
            parents.append(country["id"])
        parts = [name]
        if adm1:
            parts.append(adm1)
        elif region:
            parts.append(region["name"])
        if country:
            parts.append(country["name"])
        rec = {
            "id": make_id("city", f"{name}-{adm0}", source_id),
            "name": name,
            "name_native": _pick(props, "name"),
            "alt_names": _alt_names(props),
            "level": "city",
            "parent_ids": parents,
            "hierarchy": " › ".join(parts),
            "country": country["name"] if country else _pick(props, "adm0name"),
            "region_name": adm1,
            "adm0_a3": adm0,
            "population": _pick(props, "pop_max", "pop_min"),
            "source_id": source_id,
        }
        out.append((rec, geom))
    return out


def build_sea_records(path: Path) -> list[tuple[dict, dict]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for feat in data.get("features", []):
        props = feat.get("properties") or {}
        geom = feat.get("geometry")
        if not geom:
            continue
        name = _pick(props, "name_en", "name", "label", default="Unknown sea")
        source_id = _pick(props, "ne_id", default=slugify(name))
        rec = {
            "id": make_id("sea", name, source_id),
            "name": name,
            "name_native": _pick(props, "name"),
            "alt_names": _alt_names(props),
            "level": "sea",
            "parent_ids": [],
            "hierarchy": name,
            "featurecla": _pick(props, "featurecla"),
            "population": None,
            "source_id": source_id,
        }
        out.append((rec, geom))
    return out


def finalize_record(rec: dict, geom: dict, *, simplify_display: float, simplify_mask: float) -> tuple[dict, dict, dict]:
    bbox = bbox_of_geom(geom)
    centroid = centroid_of_geom(geom)
    area = geom_area_deg2(geom)
    rec = dict(rec)
    rec["centroid"] = [round(centroid[0], 6), round(centroid[1], 6)]
    rec["bbox"] = [round(x, 6) for x in bbox]
    rec["area_deg2"] = round(area, 6)
    display_geom = simplify_geom(geom, simplify_display) if rec["level"] != "city" else geom
    mask_geom = simplify_geom(geom, simplify_mask) if rec["level"] != "city" else geom
    # store geometry for resolver/masking separately (can be same for now)
    rec["display_geometry"] = display_geom
    rec["mask_geometry"] = mask_geom
    return rec, display_geom, mask_geom


class Gazetteer:
    def __init__(self, places: list[dict], search_index: list[dict] | None = None):
        self.places = {p["id"]: p for p in places}
        self.by_level: dict[str, list[Place]] = {"country": [], "region": [], "city": [], "sea": []}
        for p in places:
            geom = p.get("mask_geometry") or p.get("display_geometry") or p.get("geometry")
            if not geom:
                continue
            self.by_level.setdefault(p["level"], []).append(
                Place(p["id"], p["name"], p["level"], p, geom, p.get("bbox") or bbox_of_geom(geom))
            )
        self.search_index = search_index or self._build_search_index(places)

    @staticmethod
    def _build_search_index(places: list[dict]) -> list[dict]:
        idx = []
        for p in places:
            names = [p.get("name", ""), p.get("name_native", "")] + list(p.get("alt_names") or [])
            norm = sorted({normalize_text(n) for n in names if normalize_text(n)})
            idx.append({
                "id": p["id"],
                "name": p["name"],
                "level": p["level"],
                "hierarchy": p.get("hierarchy", p["name"]),
                "centroid": p.get("centroid"),
                "bbox": p.get("bbox"),
                "norm": norm,
                "population": p.get("population") or 0,
                "area_deg2": p.get("area_deg2") or 0,
            })
        return idx

    def search(self, q: str, level: str | None = None, limit: int = 10) -> list[dict]:
        nq = normalize_text(q)
        if not nq:
            return []
        results = []
        for item in self.search_index:
            if level and item["level"] != level:
                continue
            score = None
            for name in item["norm"]:
                if name == nq:
                    score = 0
                    break
                if name.startswith(nq):
                    score = min(score if score is not None else 9, 1)
                elif nq in name:
                    score = min(score if score is not None else 9, 2)
            if score is None:
                continue
            rank = LEVEL_RANK.get(item["level"], 9)
            pop = float(item.get("population") or 0)
            area = float(item.get("area_deg2") or 0)
            results.append((score, rank, -pop, -area, item))
        results.sort(key=lambda t: (t[0], t[1], t[2], t[3], t[4]["name"]))
        out = []
        for _, _, _, _, item in results[: max(1, limit)]:
            out.append({k: item[k] for k in ("id", "name", "level", "hierarchy", "centroid", "bbox")})
        return out

    def resolve(self, lat: float, lon: float, level: str) -> dict[str, Any]:
        # normalize lon
        lon = ((lon + 180) % 360) - 180
        if level == "city":
            return self._resolve_city(lat, lon)
        if level == "sea":
            return self._resolve_sea(lat, lon)
        candidates = self.by_level.get(level, [])
        for place in candidates:
            if place.contains(lon, lat):
                return {"place": self.places[place.id], "level": level}
        # fallback for region/country click in open water -> no polygon match
        return {"place": None, "level": level, "open_ocean": level == "sea"}

    def _resolve_sea(self, lat: float, lon: float) -> dict[str, Any]:
        for place in self.by_level.get("sea", []):
            if place.contains(lon, lat):
                return {"place": self.places[place.id], "level": "sea"}
        return {"place": None, "level": "sea", "open_ocean": True, "label": "Open ocean"}

    def _resolve_city(self, lat: float, lon: float, threshold_deg: float = 1.0) -> dict[str, Any]:
        # nearest populated place within threshold
        best = None
        best_d = threshold_deg * threshold_deg
        for place in self.by_level.get("city", []):
            c = place.record.get("centroid") or [0, 0]
            dlat = lat - c[1]
            dlon = (lon - c[0] + 180) % 360 - 180
            d = dlat * dlat + (dlon * math.cos(math.radians(lat))) ** 2
            if d < best_d:
                best_d = d
                best = place
        if best:
            return {"place": self.places[best.id], "level": "city", "nearest": True}
        # fallback to region/country? keep simple
        return {"place": None, "level": "city"}

    def get(self, place_id: str) -> dict | None:
        return self.places.get(place_id)

    def to_feature(self, place_id: str, simplified: bool = True) -> dict | None:
        p = self.get(place_id)
        if not p:
            return None
        geom = p.get("display_geometry") if simplified else p.get("mask_geometry")
        props = {k: v for k, v in p.items() if k not in {"display_geometry", "mask_geometry"}}
        return {"type": "Feature", "properties": props, "geometry": geom}


def save_gazetteer(out_dir: Path, places: list[dict], search_index: list[dict], meta: dict) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "places.json").write_text(
        json.dumps({"meta": meta, "places": places}, ensure_ascii=False), encoding="utf-8"
    )
    (out_dir / "search_index.json").write_text(
        json.dumps({"meta": meta, "index": search_index}, ensure_ascii=False), encoding="utf-8"
    )
    # per-level display geojson
    by_level: dict[str, list[dict]] = {}
    for p in places:
        geom = p.get("display_geometry")
        if not geom:
            continue
        props = {k: v for k, v in p.items() if k not in {"display_geometry", "mask_geometry"}}
        by_level.setdefault(p["level"], []).append({"type": "Feature", "properties": props, "geometry": geom})
    for level, feats in by_level.items():
        (out_dir / f"{level}.geojson").write_text(
            json.dumps({"type": "FeatureCollection", "features": feats}, ensure_ascii=False),
            encoding="utf-8",
        )


def load_gazetteer(path: Path | str) -> Gazetteer:
    path = Path(path)
    if path.is_dir():
        data = json.loads((path / "places.json").read_text(encoding="utf-8"))
        idx = json.loads((path / "search_index.json").read_text(encoding="utf-8")).get("index", [])
        return Gazetteer(data["places"], idx)
    data = json.loads(path.read_text(encoding="utf-8"))
    if "places" in data:
        return Gazetteer(data["places"], data.get("index"))
    raise ValueError(f"Unrecognized gazetteer format: {path}")
