# NASA Data Guide: How to Find, Download, Clean, and Analyze the Data

A practical, step-by-step guide for the Global Change Explorer team. It takes you from "I have no data" to "I have trend and significance layers ready for the map."

> **Read this first:** dataset names, versions, variable names, and file formats change over time. Treat every dataset name in this guide as a starting point and **verify it in Earthdata Search** before building on it. Where the guide says "check," it means open one file and look.

---

## Table of Contents

1. [The Workflow at a Glance](#1-the-workflow-at-a-glance)
2. [Accounts and Access](#2-accounts-and-access)
3. [Ways to Get the Data](#3-ways-to-get-the-data)
4. [Finding the Right Dataset](#4-finding-the-right-dataset)
5. [Downloading with earthaccess](#5-downloading-with-earthaccess)
6. [Dataset Cheat Sheet](#6-dataset-cheat-sheet)
7. [Opening the Files](#7-opening-the-files)
8. [Cleaning: Fill Values, Scaling, Units, Coordinates, Time](#8-cleaning-fill-values-scaling-units-coordinates-time)
9. [Putting Everything on a Common Grid](#9-putting-everything-on-a-common-grid)
10. [Anomalies: Removing the Seasonal Cycle](#10-anomalies-removing-the-seasonal-cycle)
11. [Trends and Significance](#11-trends-and-significance)
12. [Saving Layers and Answering a Click](#12-saving-layers-and-answering-a-click)
13. [Validating Against Giovanni](#13-validating-against-giovanni)
14. [Storage and Compute Planning](#14-storage-and-compute-planning)
15. [Troubleshooting](#15-troubleshooting)
16. [Citing and Using NASA Data](#16-citing-and-using-nasa-data)
17. [Team Quick-Start Checklist](#17-team-quick-start-checklist)
18. [Links](#18-links)

---

## 1. The Workflow at a Glance

```
Account → Find dataset → Download/stream → Open → Clean → Regrid → Anomalies → Trend + significance → Save layers → Serve on map
```

| Stage | Output | Who owns it (suggested) |
|---|---|---|
| Access and download | Raw files in `data/raw/` | Data acquisition |
| Clean and regrid | One monthly Zarr per variable in `data/cache/` | Data acquisition |
| Anomalies, trends, significance | Layers in `layers/` | Analysis |
| Point lookup and map | API and frontend | Backend and frontend |

Do the whole chain for **one variable first** (we suggest GPM IMERG precipitation), then repeat for the others.

---

## 2. Accounts and Access

### 2.1 Earthdata Login (required, free)

1. Go to https://urs.earthdata.nasa.gov and register.
2. Log in once and **approve applications** if prompted. Some archives (for example GES DISC) require you to authorize their application on your profile. Missing approval is the most common cause of `401` or `403` errors.
3. Every teammate should have their own account.

### 2.2 Authenticating from Python

```python
import earthaccess

earthaccess.login()                      # tries environment variables, ~/.netrc, then interactive prompt
# earthaccess.login(persist=True)        # saves credentials to ~/.netrc so you are not asked again
```

For scripts and servers, set environment variables instead of typing credentials:

```bash
export EARTHDATA_USERNAME="your_username"
export EARTHDATA_PASSWORD="your_password"
```

**Never commit credentials to Git.** Add `.netrc` and any `.env` file to `.gitignore`.

### 2.3 Install the toolchain

```bash
pip install earthaccess xarray netCDF4 h5netcdf zarr dask rioxarray \
            numpy scipy pandas pymannkendall statsmodels xesmf
```

`xesmf` needs ESMF, which is easiest to install with conda (`conda install -c conda-forge xesmf`). If it gives you trouble, skip it and use the simpler regridding options in section 9.

---

## 3. Ways to Get the Data

Pick the route that fits the job. Mixing routes is normal.

| Route | Best for | Effort | Notes |
|---|---|---|---|
| **earthaccess (Python)** | Scripted, repeatable download or streaming of many files | Low | Our main route |
| **Earthdata Search (web)** | Exploring, confirming dataset names, region and date subsetting | Very low | Can email you download links |
| **Giovanni (web)** | Quick maps, time series, and CSV/NetCDF exports with no code; validating our results | Very low | Limited to the datasets it hosts |
| **Harmony API** | Server-side subsetting and format conversion (for example HDF to NetCDF) | Medium | Reduces download size; useful for awkward formats |
| **OPeNDAP** | Reading just the slice you need without downloading whole files | Medium | Available for many GES DISC and PO.DAAC datasets |
| **Cloud (AWS)** | Fast bulk access when your code runs in AWS region `us-west-2` | Medium | Direct S3 access only works from that region; elsewhere, `earthaccess` streams over HTTPS |
| **Google Earth Engine** | Fast global prototyping with built-in processing | Medium | Not NASA's platform; separate sign-up |

**Hackathon advice:** use Giovanni to explore and sanity-check, earthaccess to build the pipeline, and cache everything locally.

---

## 4. Finding the Right Dataset

### 4.1 In the browser (Earthdata Search)

1. Open https://search.earthdata.nasa.gov.
2. Search by keyword (for example `GPM IMERG monthly`).
3. Open the dataset page and note:
   - **Short name** (for example `GPM_3IMERGM`)
   - **Version** (always use the latest unless there is a reason not to)
   - **Spatial and temporal coverage and resolution**
   - **Variables**
   - **DOI** (for citation)
   - **Archive center** (DAAC)

### 4.2 In Python

```python
import earthaccess
earthaccess.login()

# Search the catalog by keyword
datasets = earthaccess.search_datasets(keyword="GPM IMERG monthly", count=10)
for d in datasets:
    print(d.summary()["short-name"], d.summary()["version"])
```

### 4.3 Checklist before you commit to a dataset

- [ ] Global coverage (or the coverage you need)
- [ ] **Monthly** product exists (avoid daily for 20+ years)
- [ ] Record covers our common period (for example 2002 to 2024)
- [ ] Format we can open (NetCDF is easiest)
- [ ] Resolution suits our grid
- [ ] You know which surface it applies to (land, ocean, ice, atmosphere)

---

## 5. Downloading with earthaccess

### 5.1 Search for granules

```python
import earthaccess
earthaccess.login()

results = earthaccess.search_data(
    short_name="GPM_3IMERGM",             # verify in Earthdata Search
    version="07",                         # latest version at time of writing; verify
    temporal=("2002-01-01", "2024-12-31"),
    # bounding_box=(west, south, east, north),   # omit for global
)
print(f"Found {len(results)} granules")
```

A **granule** is one file (for monthly global products, usually one month per file).

### 5.2 Download

```python
files = earthaccess.download(results, "./data/raw/imerg")
```

Downloads can be interrupted and re-run; `earthaccess` skips files that already exist.

### 5.3 Stream instead of downloading

```python
file_objs = earthaccess.open(results)     # file-like objects, read on demand
```

Streaming is handy for a quick look, but for the hackathon **download and cache** so the demo never depends on the network.

### 5.4 Be kind to the servers

- Download once, process many times.
- Do not loop thousands of tiny requests; search once and download in batch.
- Keep a `data/README.txt` noting dataset, version, and download date.

---

## 6. Dataset Cheat Sheet

> **Verify everything in this table.** Names, versions, and variable names are written from general knowledge and may have changed. "Open one file and check" is always the final authority: run `print(ds)` and read the attributes.

| Variable | Dataset (short name to search) | Surface | DAAC | Typical resolution | Typical format | Things to check |
|---|---|---|---|---|---|---|
| Precipitation | `GPM_3IMERGM` (IMERG monthly) | Land, ocean | GES DISC | 0.1° | NetCDF4/HDF5 | Units are a **rate (mm/hr)**; multiply by hours in the month for mm/month. Lower reliability at high latitudes |
| Vegetation greenness | `MOD13C2` (MODIS Terra monthly, climate-modeling grid) | Land | LP DAAC | 0.05° | HDF4 | Scale factor 0.0001; HDF4 needs special handling (section 7.2) |
| Land surface temperature | `MOD11C3` (MODIS Terra monthly, climate-modeling grid) | Land | LP DAAC | 0.05° | HDF4 | Scale factor 0.02 gives Kelvin; cloud gaps |
| Air temperature, humidity | `M2TMNXSLV` (MERRA-2 monthly single-level) | Global | GES DISC | 0.5° × 0.625° | NetCDF4 | Variable `T2M` is 2 m temperature in Kelvin; model-produced, no gaps |
| Terrestrial water storage | GRACE / GRACE-FO mascon dataset (search `GRACE mascon`) | Land | PO.DAAC | 0.5° grid, effective resolution of hundreds of km | NetCDF | Variable is liquid water equivalent thickness (cm); **gap between GRACE and GRACE-FO (2017 to 2018)**; longitudes are 0 to 360 |
| Sea ice concentration | NSIDC passive microwave sea ice (search `NSIDC-0051`) | Polar oceans | NSIDC DAAC | 25 km | NetCDF / binary | Polar projection; may need reprojection |
| Soil moisture (model) | `GLDAS_NOAH025_M` | Land | GES DISC | 0.25° | NetCDF4 | Multiple soil layers; pick one and document it |
| Soil moisture (satellite) | SMAP Level 3 (search `SMAP L3 soil moisture`) | Land | NSIDC DAAC | 9 to 36 km | HDF5 | Record starts 2015: low trend reliability |
| Night lights | `VNP46A3` (VIIRS Black Marble monthly) | Land | LAADS DAAC | 500 m (tiled) | HDF5 | Record starts 2012; tiled, so more assembly |
| Sea surface temperature | GHRSST (for example MUR) | Ocean | PO.DAAC | 1 to 25 km | NetCDF | Very large; use monthly or coarsened versions |

### Dealing with a dataset you are not sure about

1. Find it in Earthdata Search.
2. Download **one** granule.
3. Run `print(ds)` and read variable names, dimensions, units, and attributes.
4. Record what you learned in `config/datasets.yaml`.

### Suggested `config/datasets.yaml` entry

```yaml
imerg_precip:
  short_name: GPM_3IMERGM
  version: "07"
  variable: precipitation
  units_in: mm/hr
  units_out: mm/month
  surface: [land, ocean]
  period: [2002-01, 2024-12]
  native_resolution_deg: 0.1
  notes: "Multiply by hours in month. Check high-latitude quality."
```

---

## 7. Opening the Files

### 7.1 NetCDF and HDF5 (easy)

```python
import xarray as xr

ds = xr.open_dataset("data/raw/imerg/example.nc4")
print(ds)                        # dimensions, coordinates, variables, attributes
print(ds.data_vars)              # variable names
print(ds["precipitation"].attrs) # units, long_name, fill value
```

Open many monthly files into one time series:

```python
import glob
files = sorted(glob.glob("data/raw/imerg/*.nc4"))
ds = xr.open_mfdataset(files, combine="by_coords", parallel=True)
```

If `combine="by_coords"` fails because files lack a time coordinate, see section 8.5.

### 7.2 HDF4 (MODIS climate-modeling-grid products)

Several MODIS monthly products are HDF4 (`.hdf`). `xarray` cannot open HDF4 by default. Options, from easiest to hardest:

1. **Get NetCDF instead.** Use Earthdata Search or Harmony to request NetCDF output when the service offers it, or use a MODIS product available as NetCDF or cloud-optimized files.
2. **Use rioxarray with GDAL**, which can read many HDF4 files if GDAL was built with HDF4 support:
   ```python
   import rioxarray
   da = rioxarray.open_rasterio('HDF4_EOS:EOS_GRID:"file.hdf":MOD_Grid_monthly_CMG_VI:CMG 0.05 Deg Monthly NDVI')
   ```
   (Subdataset names differ per product; list them with `gdalinfo file.hdf`.)
3. **Use `pyhdf`** (`pip install pyhdf`) for direct access to the datasets.
4. **Use Giovanni or Google Earth Engine** to pull the monthly series as NetCDF or an exported array if the above fails under time pressure.

Do not spend more than an hour fighting a format. Switch routes.

### 7.3 Look at the data before processing

```python
da = ds["precipitation"].isel(time=0)
da.plot()                         # a quick map; the first sanity check
```

If the map looks wrong (flipped, shifted, all one value), fix it before going further.

---

## 8. Cleaning: Fill Values, Scaling, Units, Coordinates, Time

These five issues cause most wrong results. Check each one for every dataset.

### 8.1 Fill values and scaling

Satellite files store "no data" as a special number (for example `-9999`) and compress values using `scale_factor` and `add_offset`. `xarray` handles this automatically when `mask_and_scale=True` (the default) and the attributes are present:

```python
ds = xr.open_dataset(path, mask_and_scale=True)
print(ds["precipitation"].attrs)         # look for _FillValue, scale_factor, add_offset
```

Always confirm that missing areas show as `NaN` and that value ranges are physical:

```python
print(float(da.min()), float(da.max()))  # temperatures should be roughly 180 to 340 K, NDVI -0.2 to 1.0
```

For HDF4 reads through GDAL, you may need to apply the scale factor yourself (for example NDVI × 0.0001, MODIS LST × 0.02).

### 8.2 Units

Convert to units that mean something to users and are consistent across the tool.

| Variable | Convert | Example |
|---|---|---|
| IMERG precipitation | mm/hr to mm/month | `da * 24 * da.time.dt.days_in_month` |
| Temperature | Kelvin to °C | `da - 273.15` |
| GRACE water storage | cm of liquid water equivalent | keep as is, state the unit |
| NDVI | already unitless | keep as is |

Write the final unit and the conversion into `datasets.yaml`.

### 8.3 Longitude convention

Some datasets use −180 to 180, others use 0 to 360. Normalize to −180 to 180 and sort:

```python
ds = ds.assign_coords(lon=(((ds.lon + 180) % 360) - 180)).sortby("lon")
```

### 8.4 Coordinate names and order

Names vary (`lat`/`latitude`, `lon`/`longitude`) and latitude can run north to south. Standardize:

```python
ds = ds.rename({"latitude": "lat", "longitude": "lon"})   # only if needed
ds = ds.sortby("lat")                                     # ascending latitude
```

Also check dimension order. Some IMERG files list `lon` before `lat`; use `.transpose("time", "lat", "lon")`.

### 8.5 Time axis

Monthly products give one file per month, and some files carry no usable time coordinate. Build it from the filename or the file metadata, and set it to the first day of each month for consistency:

```python
import pandas as pd
times = pd.to_datetime([f.split("_")[-1][:6] for f in files], format="%Y%m")  # adapt to your naming
ds = xr.concat([xr.open_dataset(f) for f in files], dim=pd.Index(times, name="time"))
```

(The filename pattern above is only an example. Look at your actual filenames.)

After combining, check for gaps:

```python
expected = pd.date_range(ds.time.min().values, ds.time.max().values, freq="MS")
missing = expected.difference(pd.to_datetime(ds.time.values))
print("Missing months:", missing)
```

Missing months must be reported, never silently filled.

---

## 9. Putting Everything on a Common Grid

The click lookup only works if every variable shares the same grid and time axis.

**Recommended:** monthly, 0.5° for the MVP (fast, about 260,000 cells) or 0.25° if time and compute allow.

### 9.1 Target grid

```python
import numpy as np
res = 0.5
lat = np.arange(-90 + res/2, 90, res)
lon = np.arange(-180 + res/2, 180, res)
```

### 9.2 Regridding options

**Integer factor (cleanest): block averaging.** For example 0.05° to 0.25° is a factor of 5:

```python
coarse = da.coarsen(lat=5, lon=5, boundary="trim").mean()
```

**Quick and acceptable for the hackathon: interpolation.**

```python
regridded = da.interp(lat=lat, lon=lon, method="linear")
```

Interpolation from a much finer grid samples rather than averages, which can add noise. Prefer coarsening first, then interpolating the small remaining difference.

**Best quality: conservative regridding with xESMF.**

```python
import xesmf as xe
target = xe.util.grid_global(res, res)          # check that its lon range matches yours
regridder = xe.Regridder(da, target, "conservative")
regridded = regridder(da)
```

### 9.3 Common period

Clip every variable to the shared period and record any that are shorter:

```python
da = da.sel(time=slice("2002-01-01", "2024-12-31"))
```

### 9.4 Masks by surface type

Make a land/ocean mask once and reuse it so that each click only reports variables valid for that place (vegetation on land only, sea ice in polar oceans only). Store the mask beside your layers.

### 9.5 Save the cleaned cube

```python
regridded.to_dataset(name="precip_mm_month").to_zarr("data/cache/imerg_precip.zarr", mode="w")
```

---

## 10. Anomalies: Removing the Seasonal Cycle

Raw monthly values are dominated by the annual cycle. Trend tests on raw values mostly detect seasonality. Subtract each calendar month's long-term average:

```python
clim = da.groupby("time.month").mean("time")
anom = da.groupby("time.month") - clim
```

Then average anomalies into **annual means** (this reduces autocorrelation and computing cost, and is a sound choice for the MVP):

```python
annual = anom.groupby("time.year").mean("time", skipna=True)
```

Only keep years with enough valid months:

```python
n_valid = anom.notnull().groupby("time.year").sum("time")
annual = annual.where(n_valid >= 9)        # at least 9 of 12 months
```

Alternative for later: run a seasonal Mann-Kendall test on monthly anomalies (see `pymannkendall.seasonal_test`).

---

## 11. Trends and Significance

### 11.1 What to compute per cell

| Quantity | Method | Meaning |
|---|---|---|
| Slope | Theil-Sen | Rate of change per year, robust to outliers |
| p-value | Mann-Kendall with Hamed-Rao autocorrelation correction | Is the monotonic trend real? |
| Corrected significance | Benjamini-Hochberg FDR across all cells | Controls false positives across the map |
| Standardized trend | Slope per decade divided by interannual standard deviation | Used to **rank** variables at a click; comparable across variables with different units |
| Years of data | Count of valid years | Low-confidence flag when short |

### 11.2 Per-cell function

```python
import numpy as np
import pymannkendall as mk
from scipy.stats import theilslopes

MIN_YEARS = 10

def trend_1d(y, x):
    ok = np.isfinite(y)
    if ok.sum() < MIN_YEARS:
        return np.array([np.nan, np.nan, ok.sum()])
    slope = theilslopes(y[ok], x[ok])[0]                 # units per year
    p = mk.hamed_rao_modification_test(y[ok]).p          # autocorrelation-aware p-value
    return np.array([slope, p, ok.sum()])
```

### 11.3 Apply to the whole grid

```python
import xarray as xr

res = xr.apply_ufunc(
    trend_1d, annual, annual["year"],
    input_core_dims=[["year"], ["year"]],
    output_core_dims=[["stat"]],
    vectorize=True,
    dask="parallelized",
    output_dtypes=[float],
    dask_gufunc_kwargs={"output_sizes": {"stat": 3}},
)
layers = xr.Dataset({
    "slope_per_year": res.isel(stat=0),
    "p_value":        res.isel(stat=1),
    "n_years":        res.isel(stat=2),
})
layers["slope_per_decade"] = layers["slope_per_year"] * 10
layers["std_trend"] = layers["slope_per_decade"] / annual.std("year")
```

This runs one test per cell and can take a while. To keep it manageable:

- Use 0.5° for the MVP.
- Skip cells that are masked (ocean for vegetation, and so on) before computing.
- Use Dask chunks (`annual.chunk({"lat": 60, "lon": 60})`) and run on several cores.
- Test on a small region first.

### 11.4 Correct for multiple testing

```python
from statsmodels.stats.multitest import multipletests

p = layers["p_value"].values
valid = np.isfinite(p)
reject, p_adj, _, _ = multipletests(p[valid], alpha=0.05, method="fdr_bh")

sig = np.zeros_like(p, dtype=bool)
sig[valid] = reject
layers["significant"] = (("lat", "lon"), sig)
```

Map layers should draw a cell as **significant** only when `significant` is true after FDR.

### 11.5 Classify each cell

```python
direction = np.sign(layers["slope_per_year"])
layers["class"] = xr.where(layers["significant"] & (direction > 0), 1,
                    xr.where(layers["significant"] & (direction < 0), -1, 0))
# 1 = significant increase, -1 = significant decrease, 0 = no significant change
```

### 11.6 Nearby comparison (divergence)

For a clicked cell, look at cells in a window (for example about 500 km) and report the share that is significantly increasing, significantly decreasing, or not significant:

```python
def neighbors(layers, lat0, lon0, half_width_deg=5):
    win = layers["class"].sel(
        lat=slice(lat0 - half_width_deg, lat0 + half_width_deg),
        lon=slice(lon0 - half_width_deg, lon0 + half_width_deg),
    )
    n = int(win.notnull().sum())
    return {
        "up":   float((win == 1).sum() / n),
        "down": float((win == -1).sum() / n),
        "none": float((win == 0).sum() / n),
    }
```

At high latitudes a degree of longitude covers less distance, so treat the window as approximate or scale it by `cos(lat)`.

---

## 12. Saving Layers and Answering a Click

### 12.1 Save

```python
layers.to_zarr("layers/imerg_precip_trend.zarr", mode="w")
```

Create one layers file per variable using the same grid and the same names for the fields.

### 12.2 Answer a click

```python
def report_for(lat, lon, variables):
    rows = []
    for name, path in variables.items():
        L = xr.open_zarr(path).sel(lat=lat, lon=lon, method="nearest")
        if np.isnan(float(L["slope_per_decade"])):
            continue                                 # variable does not apply here
        rows.append({
            "variable": name,
            "rate_per_decade": float(L["slope_per_decade"]),
            "significant": bool(L["significant"]),
            "standardized": float(L["std_trend"]),
            "n_years": int(L["n_years"]),
        })
    # rank: significant first, then by strength of change
    return sorted(rows, key=lambda r: (not r["significant"], -abs(r["standardized"])))
```

Expose this through a FastAPI route (`GET /report?lat=..&lon=..`) and have the frontend draw the panel from the response. Also serve the annual or monthly anomaly series for the chosen variable so the panel can plot the time series and trend line.

### 12.3 Turn numbers into words

Use a template so wording is predictable and honest:

```
"At this location, {variable} has {increased|decreased} by {rate:.2f} {unit} per decade
 over {n_years} years (significant after correction for testing many locations).
 Nearby, {down:.0%} of surrounding cells trend the opposite way."
```

For non-significant results: *"No statistically significant change detected over {n_years} years."* Never describe a non-significant result as "no change"; it means the data cannot confirm one.

---

## 13. Validating Against Giovanni

Validation is how you prove your pipeline is right and a strong point in the pitch.

1. Pick 2 or 3 test locations (for example one wet, one dry, one polar).
2. In Giovanni (https://giovanni.gsfc.nasa.gov), choose the same dataset, draw a small box or point, set the same dates, and plot a **time series**. Download the result.
3. Compute the same series from your cached data for that location.
4. Compare: they should match closely (small differences can come from regridding).
5. Compare the **direction** of the trend too. If the sign disagrees, investigate before going on.
6. Record the results in `notebooks/validation.ipynb`.

Also useful: **synthetic tests**. Build a fake dataset with a known trend and noise, run it through the pipeline, and confirm that the recovered slope matches and that pure noise is rarely flagged as significant.

---

## 14. Storage and Compute Planning

| Item | Rough size |
|---|---|
| One global monthly field at 0.5° (float32) | about 1 MB |
| One global monthly field at 0.25° (float32) | about 4 MB |
| One variable at 0.25°, 2002 to 2024 (276 months) | about 1.1 GB uncompressed |
| Raw IMERG, MODIS CMG, and similar monthly files | Often tens of GB in total across a few variables |

Practical rules:

- Delete or archive `data/raw/` after the cleaned Zarr is verified. Keep `data/cache/` and `layers/`.
- Add `data/` to `.gitignore`. Share the cache through a drive or object storage, not Git.
- Start at 0.5°. Move to 0.25° only if the pipeline works and time remains.
- Use Dask and several cores for the trend step; test on a region before running globally.
- Compute layers **before** the demo and ship them with the app.

---

## 15. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `401` or `403` on download | Account lacks approval for the archive's application | Log in at urs.earthdata.nasa.gov and approve the app (for example "NASA GESDISC DATA ARCHIVE") |
| `earthaccess.login()` keeps prompting | No saved credentials | Use `login(persist=True)` or set environment variables |
| Search returns zero granules | Wrong short name, version, or dates | Confirm in Earthdata Search; remove filters one at a time |
| Cannot open `.hdf` file | HDF4 format | See section 7.2 |
| Map is shifted by half the globe | Longitude 0 to 360 vs −180 to 180 | Section 8.3 |
| Map is upside down | Latitude order reversed | Sort by `lat` (section 8.4) |
| Values all `NaN` or huge numbers | Fill value or scale factor not applied | Section 8.1; check `attrs` |
| Temperatures around 280 | Data are in Kelvin | Subtract 273.15 |
| Rainfall values look tiny | Units are mm/hr | Section 8.2 |
| `open_mfdataset` fails to combine | No time coordinate or mismatched dimensions | Section 8.5; check dimension names and order |
| Trend step is extremely slow | Too many cells, single core | Lower resolution, mask first, use Dask |
| Almost every cell "significant" | No anomalies, or no multiple-testing correction | Sections 10 and 11.4 |
| Almost no cell significant | Series too short or too noisy | Check `n_years`; consider a longer period |
| GRACE shows a gap | 2017 to 2018 between missions | Leave the gap as missing; report it |
| Memory error | Loading everything at once | Use Dask chunks and process one variable at a time |

---

## 16. Citing and Using NASA Data

- NASA Earth science data is generally open to use, but **each dataset has a DOI and a citation**. Find it on the dataset page in Earthdata Search or on the DAAC's site.
- Add a **Data Sources** section to the README and the pitch listing every dataset, version, and DOI.
- Acknowledge NASA and the relevant DAAC in the app footer.
- Keep a record of the access date and the version number for each dataset you used.
- Model-produced datasets (MERRA-2, GLDAS) are not observations. Label them as model-based in the app.

---

## 17. Team Quick-Start Checklist

**Everyone (first hour)**
- [ ] Earthdata Login account created and applications approved
- [ ] `earthaccess` installed and `earthaccess.login()` works
- [ ] Repo cloned, `data/` in `.gitignore`

**Data acquisition**
- [ ] IMERG short name and version confirmed in Earthdata Search
- [ ] One IMERG granule opened and inspected (`print(ds)`, plotted)
- [ ] All monthly files downloaded for the common period
- [ ] Cleaned, regridded Zarr saved, missing months listed
- [ ] Repeat for NDVI, temperature, and GRACE-FO
- [ ] `config/datasets.yaml` filled in for each

**Analysis**
- [ ] Anomalies and annual means working on IMERG
- [ ] Trend, p-value, FDR, and class layers built for IMERG
- [ ] Synthetic-trend test passes
- [ ] Validated against Giovanni at 2 or 3 locations
- [ ] Layers built for the remaining variables

**Integration**
- [ ] Point lookup function and API route returning a ranked report
- [ ] Neighbor comparison working
- [ ] Layers loaded into the map
- [ ] Data sources and DOIs added to the README

---

## 18. Links

| Resource | URL |
|---|---|
| Earthdata Login | https://urs.earthdata.nasa.gov |
| Earthdata Search | https://search.earthdata.nasa.gov |
| Earthdata main site | https://www.earthdata.nasa.gov |
| earthaccess documentation | https://earthaccess.readthedocs.io |
| Giovanni | https://giovanni.gsfc.nasa.gov |
| Worldview | https://worldview.earthdata.nasa.gov |
| GES DISC | https://disc.gsfc.nasa.gov |
| LP DAAC | https://lpdaac.usgs.gov |
| PO.DAAC | https://podaac.jpl.nasa.gov |
| NSIDC DAAC | https://nsidc.org |
| OB.DAAC | https://oceancolor.gsfc.nasa.gov |
| LAADS DAAC | https://ladsweb.modaps.eosdis.nasa.gov |
| xarray documentation | https://docs.xarray.dev |
| pymannkendall | https://pypi.org/project/pymannkendall |
