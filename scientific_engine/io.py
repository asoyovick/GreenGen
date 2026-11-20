"""Observation input loading.

Loads validated gridded observation data from supported file formats.
Fails explicitly for missing/unsupported inputs; never fabricates data.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import xarray as xr


def _assert_not_synthetic(attrs: dict[str, Any], context: str) -> None:
    syn = attrs.get("synthetic")
    if isinstance(syn, str):
        syn_val = syn.strip().lower() in {"true", "1", "yes"}
    else:
        syn_val = bool(syn)
    if syn_val:
        raise ValueError(f"Synthetic data is not permitted ({context}).")


def load_observation(ref: str, *, variable: str | None = None) -> tuple[xr.DataArray, dict[str, Any]]:
    """Load observation data from a local file reference.

    Supported: .zarr directory, .nc/.nc4 NetCDF.
    Returns (DataArray, dataset_metadata).
    """
    if not ref or not str(ref).strip():
        raise ValueError("observation_ref is required and must point to verified observation data")
    path = Path(ref)
    if not path.exists():
        raise FileNotFoundError(f"Observation data not found: {ref}")

    if path.suffix == ".zarr" or path.is_dir() and (path.suffix == ".zarr" or (path / ".zgroup").exists() or (path / "zarr.json").exists()):
        ds = xr.open_zarr(str(path))
        source_format = "zarr"
    elif path.suffix in {".nc", ".nc4", ".netcdf"}:
        ds = xr.open_dataset(str(path))
        source_format = "netcdf"
    else:
        raise ValueError(f"Unsupported observation format for '{ref}' (expected .zarr or NetCDF)")

    _assert_not_synthetic(dict(ds.attrs), "dataset attributes")
    meta = {
        "source_format": source_format,
        "path": str(path),
        "attrs": {k: (v.item() if hasattr(v, "item") else v) for k, v in list(ds.attrs.items())[:50]},
    }

    if variable is None:
        candidates = list(ds.data_vars)
        if not candidates:
            raise ValueError("Observation dataset contains no data variables")
        variable = candidates[0]
    if variable not in ds:
        raise ValueError(f"Variable '{variable}' not found in observation dataset")
    da = ds[variable]
    _assert_not_synthetic(dict(da.attrs), f"variable '{variable}' attributes")

    # basic coordinate normalization checks (non-destructive)
    if "lat" not in da.coords and "latitude" in da.coords:
        da = da.rename({"latitude": "lat"})
    if "lon" not in da.coords and "longitude" in da.coords:
        da = da.rename({"longitude": "lon"})

    return da, meta
