"""Lightweight GeoJSON geometry helpers.

Uses shapely when available for robust predicates/simplification; otherwise
falls back to pure-Python implementations sufficient for 1:50m Natural Earth
data on a 0.5-degree analysis grid.
"""
from __future__ import annotations

import math
import re
import unicodedata
from typing import Any, Iterable, Iterator

try:  # optional but preferred
    from shapely.geometry import mapping, shape
    from shapely.ops import unary_union

    HAVE_SHAPELY = True
except Exception:  # pragma: no cover - environment dependent
    HAVE_SHAPELY = False


def normalize_text(text: str | None) -> str:
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", str(text))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.casefold()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def slugify(text: str) -> str:
    norm = normalize_text(text)
    return norm.replace(" ", "-") or "place"


def iter_positions(geom: dict[str, Any]) -> Iterator[tuple[float, float]]:
    t = geom.get("type")
    coords = geom.get("coordinates")
    if coords is None:
        return
    if t == "Point":
        yield float(coords[0]), float(coords[1])
    elif t in {"MultiPoint", "LineString"}:
        for p in coords:
            yield float(p[0]), float(p[1])
    elif t in {"MultiLineString", "Polygon"}:
        for part in coords:
            for p in part:
                yield float(p[0]), float(p[1])
    elif t == "MultiPolygon":
        for poly in coords:
            for part in poly:
                for p in part:
                    yield float(p[0]), float(p[1])
    elif t == "GeometryCollection":
        for g in geom.get("geometries", []):
            yield from iter_positions(g)


def bbox_of_geom(geom: dict[str, Any]) -> list[float]:
    xs, ys = [], []
    for x, y in iter_positions(geom):
        xs.append(x)
        ys.append(y)
    if not xs:
        return [0.0, 0.0, 0.0, 0.0]
    return [min(xs), min(ys), max(xs), max(ys)]


def _ring_area_centroid(ring: list[list[float]]) -> tuple[float, float, float]:
    # planar area/centroid in lon/lat degrees; adequate for labeling/bounds and
    # fine for small/medium polygons. For antimeridian-spanning features callers
    # should use shifted geometries.
    if len(ring) < 4:
        xs = [p[0] for p in ring] or [0.0]
        ys = [p[1] for p in ring] or [0.0]
        return 0.0, sum(xs) / len(xs), sum(ys) / len(ys)
    a = cx = cy = 0.0
    for i in range(len(ring) - 1):
        x0, y0 = ring[i][0], ring[i][1]
        x1, y1 = ring[i + 1][0], ring[i + 1][1]
        cross = x0 * y1 - x1 * y0
        a += cross
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross
    a *= 0.5
    if abs(a) < 1e-12:
        xs = [p[0] for p in ring]
        ys = [p[1] for p in ring]
        return 0.0, sum(xs) / len(xs), sum(ys) / len(ys)
    return a, cx / (6 * a), cy / (6 * a)


def centroid_of_geom(geom: dict[str, Any]) -> list[float]:
    t = geom.get("type")
    if t == "Point":
        c = geom["coordinates"]
        return [float(c[0]), float(c[1])]
    if HAVE_SHAPELY:
        try:
            c = shape(geom).representative_point()
            return [float(c.x), float(c.y)]
        except Exception:
            pass
    areas = []
    if t == "Polygon":
        polys = [geom.get("coordinates", [])]
    elif t == "MultiPolygon":
        polys = geom.get("coordinates", [])
    else:
        b = bbox_of_geom(geom)
        return [(b[0] + b[2]) / 2, (b[1] + b[3]) / 2]
    total = 0.0
    sx = sy = 0.0
    for poly in polys:
        if not poly:
            continue
        a, x, y = _ring_area_centroid(poly[0])
        # subtract holes approximately
        hole_a = 0.0
        hx = hy = 0.0
        for hole in poly[1:]:
            ha, hcx, hcy = _ring_area_centroid(hole)
            hole_a += abs(ha)
            hx += hcx * abs(ha)
            hy += hcy * abs(ha)
        aa = abs(a) - hole_a
        if aa <= 0:
            aa = abs(a) or 1e-12
            cx, cy = x, y
        else:
            cx = (x * abs(a) - hx) / aa if abs(a) else x
            cy = (y * abs(a) - hy) / aa if abs(a) else y
        total += aa
        sx += cx * aa
        sy += cy * aa
    if total <= 0:
        b = bbox_of_geom(geom)
        return [(b[0] + b[2]) / 2, (b[1] + b[3]) / 2]
    return [sx / total, sy / total]


def _point_in_ring(lon: float, lat: float, ring: list[list[float]]) -> bool:
    inside = False
    n = len(ring)
    if n < 3:
        return False
    j = n - 1
    for i in range(n):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        intersects = ((yi > lat) != (yj > lat)) and (
            lon < (xj - xi) * (lat - yi) / ((yj - yi) or 1e-30) + xi
        )
        if intersects:
            inside = not inside
        j = i
    return inside


def point_in_polygon_coords(lon: float, lat: float, poly: list[list[list[float]]]) -> bool:
    if not poly or not _point_in_ring(lon, lat, poly[0]):
        return False
    for hole in poly[1:]:
        if _point_in_ring(lon, lat, hole):
            return False
    return True


def point_in_geom(lon: float, lat: float, geom: dict[str, Any]) -> bool:
    if HAVE_SHAPELY:
        try:
            from shapely.geometry import Point

            return bool(shape(geom).covers(Point(lon, lat)))
        except Exception:
            pass
    t = geom.get("type")
    if t == "Polygon":
        return point_in_polygon_coords(lon, lat, geom.get("coordinates", []))
    if t == "MultiPolygon":
        return any(point_in_polygon_coords(lon, lat, p) for p in geom.get("coordinates", []))
    if t == "Point":
        c = geom["coordinates"]
        return abs(c[0] - lon) < 1e-9 and abs(c[1] - lat) < 1e-9
    return False


def bbox_contains(b: list[float], lon: float, lat: float) -> bool:
    return b[0] <= lon <= b[2] and b[1] <= lat <= b[3]


def geom_crosses_antimeridian(geom: dict[str, Any]) -> bool:
    xs = [x for x, _ in iter_positions(geom)]
    return bool(xs) and (max(xs) - min(xs) > 180)


def shift_geom_lon(geom: dict[str, Any], delta: float) -> dict[str, Any]:
    def shift_coords(c: Any) -> Any:
        if isinstance(c, (list, tuple)) and c and isinstance(c[0], (int, float)):
            return [c[0] + delta, c[1]]
        return [shift_coords(x) for x in c]

    return {"type": geom["type"], "coordinates": shift_coords(geom.get("coordinates"))}


def simplify_geom(geom: dict[str, Any], tolerance_deg: float) -> dict[str, Any]:
    if tolerance_deg <= 0:
        return geom
    if HAVE_SHAPELY:
        try:
            g = shape(geom).simplify(tolerance_deg, preserve_topology=True)
            if g.is_empty:
                return geom
            return mapping(g)
        except Exception:
            return geom
    # pure-python fallback: keep geometry as-is (safe, just larger)
    return geom


def geom_area_deg2(geom: dict[str, Any]) -> float:
    if HAVE_SHAPELY:
        try:
            return abs(shape(geom).area)
        except Exception:
            pass
    t = geom.get("type")
    polys = geom.get("coordinates", []) if t == "Polygon" else geom.get("coordinates", []) if t == "MultiPolygon" else []
    if t == "Polygon":
        polys = [polys]
    total = 0.0
    for poly in polys:
        if not poly:
            continue
        a, _, _ = _ring_area_centroid(poly[0])
        area = abs(a)
        for hole in poly[1:]:
            ha, _, _ = _ring_area_centroid(hole)
            area -= abs(ha)
        total += max(area, 0.0)
    return total
