#!/usr/bin/env python3
"""Clean monthly gridded files into a (time, lat, lon) Zarr cube on a common grid.

Requires: xarray, numpy, pandas, zarr, netCDF4 (and dask for open_mfdataset).
"""
import argparse
import glob
import re
import sys

import numpy as np
import pandas as pd
import xarray as xr

LAT_NAMES = ("lat", "latitude", "y", "Latitude")
LON_NAMES = ("lon", "longitude", "x", "Longitude")


def standardize_coords(ds):
    """Rename to lat/lon, normalize lon to -180..180, sort ascending."""
    ren = {}
    for n in LAT_NAMES:
        if n in ds.dims and n != "lat":
            ren[n] = "lat"
    for n in LON_NAMES:
        if n in ds.dims and n != "lon":
            ren[n] = "lon"
    if ren:
        ds = ds.rename(ren)
    if "lat" not in ds.dims or "lon" not in ds.dims:
        raise ValueError(f"Could not find lat/lon dims in {list(ds.dims)}")
    ds = ds.assign_coords(lon=(((ds.lon + 180) % 360) - 180)).sortby("lon").sortby("lat")
    return ds


def convert_units(da, op):
    if not op:
        return da
    if op == "k_to_c":
        out = da - 273.15
        out.attrs["units"] = "degC"
    elif op == "mm_per_hr_to_mm_per_month":
        out = da * 24 * da["time"].dt.days_in_month
        out.attrs["units"] = "mm/month"
    elif op.startswith("scale:"):
        out = da * float(op.split(":", 1)[1])
    else:
        raise ValueError(f"Unknown --units op: {op}")
    out.attrs = {**da.attrs, **out.attrs}
    return out


def target_grid(res):
    lat = np.arange(-90 + res / 2, 90, res)
    lon = np.arange(-180 + res / 2, 180, res)
    return lat, lon


def regrid(da, res):
    """Block-average when the factor is an integer, else linear interpolation."""
    native = abs(float(da.lat[1] - da.lat[0]))
    factor = res / native
    method = "interp"
    if factor > 1 and abs(factor - round(factor)) < 1e-6:
        f = int(round(factor))
        da = da.coarsen(lat=f, lon=f, boundary="trim").mean()
        method = f"block-average x{f}"
    lat, lon = target_grid(res)
    out = da.interp(lat=lat, lon=lon, method="linear")
    if method == "interp":
        print("NOTE: used linear interpolation (non-integer factor); it samples rather than averages.")
    return out, method


def open_series(paths, variable, time_regex=None):
    if time_regex:
        pat = re.compile(time_regex)
        parts, times = [], []
        for p in paths:
            m = pat.search(p)
            if not m:
                raise ValueError(f"time regex did not match filename: {p}")
            ym = m.group(1)
            times.append(pd.Timestamp(year=int(ym[:4]), month=int(ym[4:6]), day=1))
            d = standardize_coords(xr.open_dataset(p))
            if "time" in d.dims:
                d = d.isel(time=0, drop=True)
            parts.append(d[[variable]])
        ds = xr.concat(parts, dim=pd.Index(times, name="time"))
    elif len(paths) == 1 and paths[0].endswith(".zarr"):
        # Extension to the skill script: allow an existing Zarr cube (used by the
        # synthetic pipeline) to pass through the same coordinate/regrid/report path.
        ds = standardize_coords(xr.open_zarr(paths[0]))
    elif len(paths) == 1:
        ds = standardize_coords(xr.open_dataset(paths[0]))
    else:
        ds = xr.open_mfdataset(paths, combine="by_coords")
        ds = standardize_coords(ds)
    if "time" not in ds.dims:
        raise ValueError("No time dimension. Use --time-from-filename with a regex capturing YYYYMM.")
    return ds[variable].sortby("time")


def parse_meta(items):
    """Parse repeated key=value attributes; booleans and numbers are converted."""
    out = {}
    for item in items or []:
        if "=" not in item:
            raise ValueError(f"--meta needs key=value, got {item!r}")
        key, value = item.split("=", 1)
        low = value.strip().lower()
        if low in {"true", "false"}:
            parsed = low == "true"
        else:
            try:
                parsed = float(value)
            except ValueError:
                parsed = value
        out[key] = parsed
    return out



def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--inputs", required=True, help='Glob of input files, e.g. "data/raw/*.nc4"')
    ap.add_argument("--variable", required=True)
    ap.add_argument("--out", required=True, help="Output .zarr path")
    ap.add_argument("--res", type=float, default=0.5, help="Target resolution in degrees")
    ap.add_argument("--units", default=None, help="k_to_c | mm_per_hr_to_mm_per_month | scale:<factor>")
    ap.add_argument("--start", default=None, help="YYYY-MM")
    ap.add_argument("--end", default=None, help="YYYY-MM")
    ap.add_argument("--time-from-filename", default=None, help="Regex; group 1 must be YYYYMM")
    ap.add_argument("--meta", action="append", default=[],
                    help="Extra output attribute as key=value (repeatable), e.g. synthetic=true")
    args = ap.parse_args()

    paths = sorted(glob.glob(args.inputs))
    if not paths:
        sys.exit(f"No files match {args.inputs}")
    print(f"Opening {len(paths)} files")
    da = open_series(paths, args.variable, args.time_from_filename)

    if args.start or args.end:
        da = da.sel(time=slice(args.start, args.end))
    da = convert_units(da, args.units)

    expected = pd.date_range(pd.Timestamp(da.time.min().values).to_period("M").to_timestamp(),
                             pd.Timestamp(da.time.max().values), freq="MS")
    have = pd.to_datetime(da.time.values).to_period("M").to_timestamp()
    missing = expected.difference(have)
    print(f"Months present: {len(have)}; missing: {len(missing)}")
    if len(missing):
        print("Missing months (left as gaps, not filled):", [m.strftime("%Y-%m") for m in missing][:24])

    da, method = regrid(da, args.res)
    da = da.transpose("time", "lat", "lon")
    da.attrs["regrid_method"] = method
    da.attrs["target_resolution_deg"] = args.res
    da.attrs["processing"] = "standardized coords, unit conversion, regridded; missing months not filled"
    da.attrs["missing_months"] = ",".join(m.strftime("%Y-%m") for m in missing)
    da.attrs["period_start"] = pd.Timestamp(da.time.min().values).strftime("%Y-%m")
    da.attrs["period_end"] = pd.Timestamp(da.time.max().values).strftime("%Y-%m")
    da.attrs.update(parse_meta(args.meta))

    vmin, vmax = float(da.min()), float(da.max())
    print(f"Value range: {vmin:.4g} to {vmax:.4g} {da.attrs.get('units', '')}  <- check this is physical")
    da.name = args.variable
    # Zarr 3 requires regular chunks; interpolation leaves irregular dask chunks.
    da = da.chunk({"time": -1, "lat": min(180, da.sizes["lat"]), "lon": min(360, da.sizes["lon"])})
    da.to_dataset().to_zarr(args.out, mode="w")
    print(f"Wrote {args.out}  shape={dict(da.sizes)}  regrid={method}")


if __name__ == "__main__":
    main()
