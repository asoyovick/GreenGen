"""Grid-cell masks for polygon places.

Masks are stored sparsely as lists of (ilat, ilon, fraction) for cells that
overlap a place. Fractions are estimated by subgrid sampling when shapely is
not available.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Iterable

import numpy as np

from .geojson_utils import bbox_contains, geom_crosses_antimeridian, point_in_geom, shift_geom_lon


@dataclass
class Grid:
    lats: np.ndarray
    lons: np.ndarray
    res: float

    @classmethod
    def from_centers(cls, lats: np.ndarray, lons: np.ndarray) -> "Grid":
        res = float(abs(lats[1] - lats[0])) if len(lats) > 1 else 0.5
        return cls(np.asarray(lats, dtype=float), np.asarray(lons, dtype=float), res)

    @property
    def nlat(self) -> int:
        return len(self.lats)

    @property
    def nlon(self) -> int:
        return len(self.lons)

    def cell_bounds(self, ilat: int, ilon: int) -> tuple[float, float, float, float]:
        lat = self.lats[ilat]
        lon = self.lons[ilon]
        h = self.res / 2
        return lon - h, lat - h, lon + h, lat + h

    def bbox_to_indices(self, bbox: list[float]) -> tuple[range, range]:
        w, s, e, n = bbox
        h = self.res / 2
        i0 = int(np.searchsorted(self.lats, s - h, side="left"))
        i1 = int(np.searchsorted(self.lats, n + h, side="right"))
        j0 = int(np.searchsorted(self.lons, w - h, side="left"))
        j1 = int(np.searchsorted(self.lons, e + h, side="right"))
        i0 = max(0, min(self.nlat, i0))
        i1 = max(0, min(self.nlat, i1))
        j0 = max(0, min(self.nlon, j0))
        j1 = max(0, min(self.nlon, j1))
        return range(i0, i1), range(j0, j1)

    def weights(self) -> np.ndarray:
        # cos(latitude) area weight per row
        return np.cos(np.deg2rad(self.lats))


def _sample_points_in_cell(grid: Grid, ilat: int, ilon: int, n: int = 3) -> list[tuple[float, float]]:
    w, s, e, nlat = grid.cell_bounds(ilat, ilon)
    xs = np.linspace(w, e, n + 2)[1:-1]
    ys = np.linspace(s, nlat, n + 2)[1:-1]
    return [(float(x), float(y)) for y in ys for x in xs]


def covered_fraction(grid: Grid, ilat: int, ilon: int, geom: dict[str, Any], samples: int = 3) -> float:
    pts = _sample_points_in_cell(grid, ilat, ilon, samples)
    inside = 0
    for lon, lat in pts:
        if point_in_geom(lon, lat, geom):
            inside += 1
        elif geom_crosses_antimeridian(geom):
            # try shifted query points
            for delta in (360.0, -360.0):
                if point_in_geom(lon + delta, lat, geom):
                    inside += 1
                    break
    return inside / len(pts) if pts else 0.0


def _cell_center_inside(lon: float, lat: float, geom: dict[str, Any]) -> bool:
    if point_in_geom(lon, lat, geom):
        return True
    if geom_crosses_antimeridian(geom):
        for delta in (360.0, -360.0):
            if point_in_geom(lon + delta, lat, geom):
                return True
    return False


def mask_for_place(
    grid: Grid,
    geom: dict[str, Any],
    bbox: list[float],
    samples: int = 1,
    mode: str = "center",
) -> list[tuple[int, int, float]]:
    """Return sparse [(ilat, ilon, fraction)] for cells overlapping the place.

    mode="center" (default): include cells whose center is inside the polygon,
    fraction 1.0. Fast and adequate for a 0.5° grid.
    mode="subgrid": estimate covered fraction by sampling points per cell.
    """
    geoms = [geom]
    if geom_crosses_antimeridian(geom):
        geoms = [geom, shift_geom_lon(geom, 360.0), shift_geom_lon(geom, -360.0)]
    cells: dict[tuple[int, int], float] = {}
    for g in geoms:
        b = bbox if g is geom else __import__("src.places.geojson_utils", fromlist=["bbox_of_geom"]).bbox_of_geom(g)
        lat_range, lon_range = grid.bbox_to_indices(b)
        for ilat in lat_range:
            lat = float(grid.lats[ilat])
            for ilon in lon_range:
                key = (ilat, ilon)
                if key in cells and cells[key] >= 0.999:
                    continue
                lon = float(grid.lons[ilon])
                if mode == "subgrid":
                    frac = covered_fraction(grid, ilat, ilon, g, samples=samples)
                else:
                    frac = 1.0 if _cell_center_inside(lon, lat, g) else 0.0
                if frac > 0:
                    cells[key] = max(cells.get(key, 0.0), frac)
    out = [(i, j, float(f)) for (i, j), f in cells.items() if f > 0]
    out.sort()
    return out


def mask_to_arrays(mask: list[tuple[int, int, float]], nlat: int, nlon: int):
    ilat = np.array([m[0] for m in mask], dtype=int)
    ilon = np.array([m[1] for m in mask], dtype=int)
    frac = np.array([m[2] for m in mask], dtype=float)
    return ilat, ilon, frac
