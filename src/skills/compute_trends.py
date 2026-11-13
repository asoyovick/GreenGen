#!/usr/bin/env python3
"""Compute per-cell trend and significance layers from a monthly (time, lat, lon) cube.

Requires: xarray, numpy, scipy, pymannkendall, statsmodels, zarr (dask optional).
"""
import argparse
import sys

import numpy as np
import xarray as xr
import pymannkendall as mk
from scipy.stats import theilslopes
from statsmodels.stats.multitest import multipletests


def make_trend_fn(min_years):
    def trend_1d(y, x):
        ok = np.isfinite(y)
        n = int(ok.sum())
        if n < min_years:
            return np.array([np.nan, np.nan, float(n)])
        yy, xx = y[ok], x[ok].astype(float)
        if np.ptp(yy) == 0:
            return np.array([0.0, 1.0, float(n)])
        try:
            slope = theilslopes(yy, xx)[0]
            p = mk.hamed_rao_modification_test(yy).p
        except Exception:
            return np.array([np.nan, np.nan, float(n)])
        return np.array([slope, p, float(n)])
    return trend_1d


def anomalies_annual(da, min_months):
    clim = da.groupby("time.month").mean("time")
    anom = da.groupby("time.month") - clim
    annual = anom.groupby("time.year").mean("time", skipna=True)
    n_valid = anom.notnull().groupby("time.year").sum("time")
    return annual.where(n_valid >= min_months)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cube", required=True, help="Input Zarr or NetCDF with (time, lat, lon)")
    ap.add_argument("--variable", required=True)
    ap.add_argument("--out", required=True, help="Output .zarr")
    ap.add_argument("--min-months", type=int, default=9, help="Valid months needed for an annual mean")
    ap.add_argument("--min-years", type=int, default=10, help="Valid years needed to compute a trend")
    ap.add_argument("--ok-years", type=int, default=15, help="Years needed to avoid the low_confidence flag")
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--lat-range", nargs=2, type=float, default=None)
    ap.add_argument("--lon-range", nargs=2, type=float, default=None)
    ap.add_argument("--chunk", type=int, default=None, help="Dask chunk size in cells (enables parallel)")
    args = ap.parse_args()

    ds = xr.open_zarr(args.cube) if args.cube.endswith(".zarr") else xr.open_dataset(args.cube)
    da = ds[args.variable]
    units = da.attrs.get("units", "")
    if args.lat_range:
        da = da.sel(lat=slice(*args.lat_range))
    if args.lon_range:
        da = da.sel(lon=slice(*args.lon_range))

    annual = anomalies_annual(da, args.min_months)
    if args.chunk:
        annual = annual.chunk({"lat": args.chunk, "lon": args.chunk, "year": -1})
    else:
        annual = annual.load()
    years = annual["year"]

    res = xr.apply_ufunc(
        make_trend_fn(args.min_years), annual, years,
        input_core_dims=[["year"], ["year"]], output_core_dims=[["stat"]],
        vectorize=True, dask="parallelized", output_dtypes=[float],
        dask_gufunc_kwargs={"output_sizes": {"stat": 3}},
    ).compute()

    out = xr.Dataset()
    out["slope_per_year"] = res.isel(stat=0)
    out["p_value"] = res.isel(stat=1)
    out["n_years"] = res.isel(stat=2)
    out["slope_per_decade"] = out["slope_per_year"] * 10
    out["std_trend"] = out["slope_per_decade"] / annual.std("year").where(lambda s: s > 0)

    p = out["p_value"].values
    valid = np.isfinite(p)
    sig = np.zeros(p.shape, dtype=bool)
    if valid.any():
        reject, _, _, _ = multipletests(p[valid], alpha=args.alpha, method="fdr_bh")
        sig[valid] = reject
    out["significant"] = (("lat", "lon"), sig)
    direction = np.sign(out["slope_per_year"])
    cls = xr.where(out["significant"] & (direction > 0), 1.0,
                   xr.where(out["significant"] & (direction < 0), -1.0, 0.0))
    out["class"] = cls.where(out["slope_per_year"].notnull())
    out["low_confidence"] = (out["n_years"] < args.ok_years) & out["slope_per_year"].notnull()
    out["annual_anomaly"] = annual
    out.attrs.update(variable=args.variable, units=units, alpha=args.alpha,
                     method="anomalies; annual means; Theil-Sen; Hamed-Rao Mann-Kendall; BH-FDR",
                     min_years=args.min_years, ok_years=args.ok_years)

    n_cells = int(out["slope_per_year"].notnull().sum())
    print(f"Cells with a trend: {n_cells}")
    if n_cells:
        print(f"Significant after FDR: {100 * float(out['significant'].sum()) / n_cells:.1f}%")
        print(f"  increasing: {100 * float((out['class'] == 1).sum()) / n_cells:.1f}%   "
              f"decreasing: {100 * float((out['class'] == -1).sum()) / n_cells:.1f}%")
        print(f"Low-confidence cells: {100 * float(out['low_confidence'].sum()) / n_cells:.1f}%")
    out.to_zarr(args.out, mode="w")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
