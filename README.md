# Global Change Explorer

> Click anywhere on Earth and see what has changed there, by how much, and whether the change is statistically significant.

Built for a hackathon challenge on detecting change in NASA Earth science data.

---

## Table of Contents

1. [The Challenge](#1-the-challenge)
2. [Problem Statement](#2-problem-statement)
3. [Our Solution](#3-our-solution)
4. [Scope: Change Detection, Not Forecasting](#4-scope-change-detection-not-forecasting)
5. [NASA Resources You Need](#5-nasa-resources-you-need)
6. [Getting Access to the Data](#6-getting-access-to-the-data)
7. [Methodology](#7-methodology)
8. [Architecture](#8-architecture)
9. [Tech Stack](#9-tech-stack)
10. [Project Structure](#10-project-structure)
11. [Setup and Installation](#11-setup-and-installation)
12. [Usage](#12-usage)
13. [Roadmap: MVP and Stretch Goals](#13-roadmap-mvp-and-stretch-goals)
14. [Pitfalls and Scientific Caveats](#14-pitfalls-and-scientific-caveats)
15. [Team](#15-team)
16. [References](#16-references)
17. [License](#17-license)

---

## 1. The Challenge

### Official brief (summarized)

Change is always occurring in the Earth's interconnected environmental system. When change runs in a consistent direction (rising or falling, increasing or decreasing, thickening or thinning), measured variables reflect it. But a measured Earth science variable can trend one way in one region and the opposite way in another, even when the same process drives both.

The large number of Earth science variables makes it hard to:

- **select** variables that could indicate change, and
- **analyze** the selected variables properly.

### What we are asked to build

A tool that can:

1. **Select** variables measured by Earth science missions or produced by Earth science models.
2. **Visualize** how those variables change over time.
3. **Determine**:
   - **What** is changing
   - **Where** it is changing
   - **How much** it is changing
   - Whether the change is what scientists call **"significant"**

### What the brief is really testing

| Theme | What judges will look for |
|---|---|
| Variable selection | Help navigating many variables, not a hard-coded list |
| Visualization | Clear maps and time series |
| Quantification | Rates with units (for example mm/yr, °C/decade) |
| Statistical rigor | Proper significance testing, not just a fitted line |
| Regional contradiction | Handling places where the same variable moves in opposite directions |

The word "significant" is in quotes in the brief on purpose. It signals that a valid statistical treatment is expected.

---

## 2. Problem Statement

Earth science data is abundant but hard to navigate. There are too many variables to choose from, and once one is chosen, it is hard to tell what is actually changing, where, by how much, and whether the change is statistically meaningful, especially when the same variable trends in opposite directions in different regions.

**Goal:** build an accessible tool where anyone can pick a location on a world map and immediately learn which variables have changed there, how much, and whether the change is significant.

**Target users:** students, researchers, journalists, and decision-makers who are not statistics or remote-sensing experts.

---

## 3. Our Solution

**Global Change Explorer** is an interactive web map. Instead of asking the user to pick a variable first, it flips the workflow: **pick a place, and the tool tells you what changed there.**

### User flow

1. **Browse the world map.** Choose a layer: a combined **change score** (where many variables are changing significantly) or a single variable such as precipitation.
2. **Click a location** (or search for a place).
3. **Read the change report** for that location:
   - Variables ranked by how strongly and significantly they have changed
   - Rate of change with units, and a significant or not significant verdict
   - A time series with the trend line for any selected variable
   - A **nearby comparison**: do surrounding areas trend the same way or the opposite way?
   - A plain-language summary
4. **Export** the report.

### Key features

- Click-to-explore global map with trend and significance layers
- Automatic variable selection per location, which directly addresses "too many variables to choose from"
- Rigorous significance testing (seasonality, autocorrelation, and multiple comparisons handled)
- Divergence view that shows where neighbors move in opposite directions
- Honest caveats for short records, coarse resolution, and missing data

Design mockups of the app screen and the pipeline are in the project's design file.

### Key idea: precompute globally, answer instantly

Running trend statistics over millions of grid cells on every click would be too slow. The tool therefore **precomputes** trend and significance for every grid cell and every variable ahead of time, stores them as map layers and arrays, and answers each click with a fast lookup.

---

## 4. Scope: Change Detection, Not Forecasting

This project analyzes **observed** past and present data. It does **not** predict the future.

| | This project | Forecasting (out of scope) |
|---|---|---|
| Question | What has been changing, where, how much, is it real? | What will happen in 2035? |
| Method | Trend detection and significance testing | Machine learning or physical simulation |
| Output | "Precipitation decreased X mm/yr, p < 0.01" | "Precipitation will fall by Y by 2040" |

"Earth science models" in the brief refers to datasets **produced by** models (for example MERRA-2 reanalysis) that we analyze as inputs. We do not need to build our own models.

If a forward-looking view is added, it must be labeled "if the current rate continues," with wide uncertainty bands, and never presented as a forecast.

---

## 5. NASA Resources You Need

NASA data is split across archive centers called **DAACs** (Distributed Active Archive Centers). Dataset names and versions change over time, so **confirm the exact short name and latest version in Earthdata Search** before running any download script.

### 5.1 Core datasets (recommended for the MVP)

Choose one variable per surface type so that every click returns something useful on land, ocean, or ice.

| Variable | Dataset | Surface | Archive (DAAC) | Notes |
|---|---|---|---|---|
| Precipitation | **GPM IMERG** (monthly) | Land and ocean | GES DISC | 0.1° grid; reliability drops at high latitudes |
| Vegetation greenness | **MODIS MOD13 (NDVI/EVI)** | Land | LP DAAC | Long record from 2000; aggregate from 1 km |
| Land surface temperature | **MODIS MOD11** | Land | LP DAAC | Fine resolution; gaps under cloud |
| Air temperature and humidity | **MERRA-2** reanalysis | Global | GES DISC | Model-produced; gap-free; satisfies the "produced by models" part of the brief |
| Terrestrial water storage | **GRACE / GRACE-FO mascons** | Land | PO.DAAC | Coarse (hundreds of km); gap between missions in 2017 to 2018 |
| Sea ice concentration | **NSIDC passive microwave sea ice** | Polar oceans | NSIDC DAAC | Long, consistent record |

### 5.2 Supporting datasets (stretch)

| Variable | Dataset | Surface | Archive (DAAC) | Notes |
|---|---|---|---|---|
| Soil moisture and land model outputs | **GLDAS / FLDAS** | Land | GES DISC | Model-based, long record |
| Soil moisture (satellite) | **SMAP** | Land | NSIDC DAAC | Record since 2015; low trend reliability |
| Evapotranspiration | **MODIS MOD16** | Land | LP DAAC | Water loss from vegetation and irrigation |
| Snow cover | **MODIS snow cover products** | Land | NSIDC DAAC | Seasonal snow trends |
| Sea surface temperature | **GHRSST products (for example MUR)** | Ocean | PO.DAAC | Ocean warming |
| Sea surface height | **Gridded sea surface height anomaly** | Ocean | PO.DAAC | Sea level change |
| Ocean chlorophyll | **MODIS-Aqua ocean color** | Ocean | OB.DAAC | Marine productivity |
| Nitrogen dioxide (air quality) | **OMI NO2** | Atmosphere | GES DISC | Air pollution trends |
| Night lights | **VIIRS Black Marble** | Land | LAADS DAAC | Urban expansion; record from 2012 |
| Ice sheet and glacier elevation | **ICESat-2 land ice products** | Ice | NSIDC DAAC | Sparse sampling; short record |

### 5.3 Archive centers

| DAAC | Website | Holds |
|---|---|---|
| GES DISC | https://disc.gsfc.nasa.gov | IMERG, MERRA-2, GLDAS, FLDAS, OMI |
| LP DAAC | https://lpdaac.usgs.gov | MODIS and VIIRS land products |
| PO.DAAC | https://podaac.jpl.nasa.gov | GRACE and GRACE-FO, sea surface temperature and height |
| NSIDC DAAC | https://nsidc.org | Sea ice, snow, SMAP, ICESat-2 |
| OB.DAAC | https://oceancolor.gsfc.nasa.gov | Ocean color |
| LAADS DAAC | https://ladsweb.modaps.eosdis.nasa.gov | VIIRS Black Marble |

### 5.4 NASA tools and services

| Tool | URL | What it is for |
|---|---|---|
| **Earthdata Login** | https://urs.earthdata.nasa.gov | Free account required for almost all NASA data |
| **Earthdata Search** | https://search.earthdata.nasa.gov | Find datasets, subset by region and date, get exact dataset names |
| **earthaccess** (Python) | https://github.com/nsidc/earthaccess | Log in, search, download, or stream NASA data from code |
| **Giovanni** | https://giovanni.gsfc.nasa.gov | No-code time series and maps; use to validate your own results |
| **Worldview** | https://worldview.earthdata.nasa.gov | Imagery browsing, useful for demo visuals |
| **Common Metadata Repository (CMR) API** | https://cmr.earthdata.nasa.gov | Programmatic catalog search behind Earthdata Search |

### 5.5 Optional non-NASA platform

**Google Earth Engine** (https://earthengine.google.com) hosts many NASA datasets with built-in processing and can be much faster for prototyping a global pipeline, but requires separate sign-up.

---

## 6. Getting Access to the Data

### One-time setup (every team member)

1. Register for a free **Earthdata Login** account.
2. Install the client: `pip install earthaccess`
3. Log in from Python: `earthaccess.login()`

### Global data strategy

Global data is large, so be deliberate:

- **Use monthly products only.** Daily data over 20+ years is unnecessary for trends.
- **Regrid everything to one common grid**, for example 0.25° (about 25 km), so layers line up and a click can query all variables at once.
- **Pick a common period**, for example 2002 to 2024, so variables are comparable, and note shorter records separately.
- **Pre-fetch, process, and cache** as Zarr or NetCDF. Never rely on live downloads in the demo.
- **Start with one variable** end to end (IMERG), then add others.
- **Check the hackathon's resource page** for recommended datasets or ready-made data links.

### Example: download monthly IMERG

```python
import earthaccess

earthaccess.login()

results = earthaccess.search_data(
    short_name="GPM_3IMERGM",          # confirm in Earthdata Search
    temporal=("2002-01-01", "2024-12-31"),
)
files = earthaccess.download(results, "./data/raw")
```

---

## 7. Methodology

Run once per variable, offline:

```
Load → Regrid → Anomalies → Trend per cell → Significance → Store layers
```

On each click, online:

```
Click → Look up all variables at the cell → Rank → Compare with neighbors → Summary
```

| Step | What happens | Method / tool |
|---|---|---|
| **Load and regrid** | Read gridded data and put every variable on one grid | xarray, xESMF or similar |
| **Anomalies** | Gaps handled and the **seasonal cycle removed** | xarray, NumPy |
| **Trend** | Rate of change per cell, with units | **Theil-Sen slope** (robust to outliers) |
| **Significance** | Test whether the trend is real | **Mann-Kendall** with autocorrelation correction (Hamed-Rao) |
| **Multiple testing** | Avoid false positives across millions of cells | False Discovery Rate (Benjamini-Hochberg) |
| **Record-length check** | Flag unreliable short records | Minimum years threshold |
| **Ranking at a click** | Order variables by trend relative to normal variability, then by significance | Standardized trend (trend divided by interannual spread) |
| **Nearby comparison** | Share of cells within about 500 km trending the same or the opposite way | Neighborhood statistics |
| **Summary** | Plain-language text | Templates (or an LLM that only phrases results, never computes them) |

### Why not a plain linear regression?

Raw satellite series are dominated by the seasonal cycle and are autocorrelated. A plain regression p-value is overconfident in that case. Hence anomalies, a non-parametric test, and an autocorrelation-aware correction.

---

## 8. Architecture

| Layer | Responsibility | Tools |
|---|---|---|
| **Data layer** | Cached, regridded monthly data for each variable | earthaccess, xarray, Zarr/NetCDF |
| **Analysis engine (offline)** | Anomalies, trend, significance, and FDR for every cell | NumPy, SciPy, pymannkendall |
| **Layer store** | Trend, p-value, and record length per variable | Zarr, Cloud Optimized GeoTIFF, or map tiles |
| **API** | Point lookup (all variables at a click), time series, neighbor stats | FastAPI |
| **Frontend** | World map, layer switcher, change report panel | React + MapLibre + Plotly (or Streamlit) |
| **Optional AI layer** | Natural-language questions and explanations | LLM API calling the analysis functions |

Design principle: **the statistics are always deterministic.** If an LLM is used, it only explains the results.

---

## 9. Tech Stack

- **Language:** Python 3.10+
- **Data:** xarray, NumPy, pandas, netCDF4, zarr, dask, earthaccess
- **Statistics:** SciPy, pymannkendall, statsmodels
- **Backend:** FastAPI, Uvicorn
- **Frontend:** React, MapLibre GL JS, Plotly (alternative: Streamlit or Dash for speed)
- **Tooling:** Git, Jupyter for exploration

---

## 10. Project Structure

Suggested layout (adjust to your repo):

```
global-change-explorer/
├── README.md
├── config/
│   └── datasets.yaml        # dataset names, variables, units, surface type, record length
├── data/
│   ├── raw/                 # downloaded NASA files (git-ignored)
│   └── cache/               # regridded monthly Zarr per variable
├── layers/                  # precomputed trend, p-value, and record-length layers
├── notebooks/               # exploration and validation against Giovanni
├── src/
│   ├── ingest/              # earthaccess download
│   ├── preprocess/          # regrid, anomalies, gap handling
│   ├── analysis/            # Theil-Sen, Mann-Kendall, FDR, ranking, neighbors
│   ├── summary/             # plain-language report generation
│   └── api/                 # FastAPI routes
├── frontend/                # React app (or streamlit_app.py)
├── tests/                   # unit tests on synthetic data with known trends
└── docs/                    # design mockups and pitch material
```

---

## 11. Setup and Installation

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd global-change-explorer

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install earthaccess xarray netCDF4 zarr dask numpy scipy pandas \
            pymannkendall statsmodels fastapi uvicorn

# 4. Authenticate with NASA Earthdata
python -c "import earthaccess; earthaccess.login()"

# 5. Download, regrid, and compute global trend layers
python -m src.ingest.download --config config/datasets.yaml
python -m src.analysis.build_layers --config config/datasets.yaml

# 6. Run the API
uvicorn src.api.main:app --reload

# 7. Run the frontend (separate terminal)
cd frontend && npm install && npm run dev
```

Commands are a template; update module names to match your actual code.

---

## 12. Usage

1. Open the app and choose a **map layer** (change score or a single variable).
2. **Click a location** or search for a place.
3. Read the **change report**:
   - **Ranked variables:** arrows show direction, with rate per decade and a significant or not significant verdict.
   - **Time series:** monthly anomalies with the trend line for the selected variable.
   - **Nearby comparison:** whether surrounding areas agree or trend in the opposite direction.
4. **Export** the report for that location.

### Example output format

> "At this location, [variable] has [increased/decreased] by [rate] per decade since [year] (p = [value], significant after correction). Nearby, [share]% of surrounding cells trend the opposite way."

(Format only; real values come from the data.)

---

## 13. Roadmap: MVP and Stretch Goals

### MVP

- [ ] Earthdata access working for every teammate
- [ ] 3 to 4 global variables cached on a common grid (IMERG, MODIS NDVI, MODIS LST or MERRA-2 temperature, GRACE-FO)
- [ ] Anomalies, Theil-Sen slope, Mann-Kendall significance, FDR correction
- [ ] Global trend layer with significance marking
- [ ] Click-to-report panel with ranked variables and a time series
- [ ] Plain-language summary
- [ ] Validation of at least one location against Giovanni

### Stretch

- [ ] Combined "change score" layer
- [ ] Nearby comparison and divergence highlighting
- [ ] Sea ice, sea surface temperature, and ocean variables for ocean clicks
- [ ] Place search
- [ ] Natural-language questions ("what changed near Lake Chad?")
- [ ] Cross-variable lagged correlation view
- [ ] Exportable report or shareable link
- [ ] Clearly labeled "if the current rate continues" extrapolation

---

## 14. Pitfalls and Scientific Caveats

| Pitfall | How we handle it |
|---|---|
| Seasonal cycle masquerading as a trend | Always analyze anomalies |
| Overconfident p-values on autocorrelated data | Hamed-Rao modified Mann-Kendall |
| False positives across millions of cells | FDR correction |
| Variables that do not apply to a location (vegetation over ocean) | Show only variables valid for that surface type |
| Short records (SMAP, ICESat-2, night lights) | Flag as low confidence |
| Coarse resolution (GRACE) | State the effective resolution in the report |
| Cloud gaps and mission gaps | Flag and report; do not silently interpolate |
| Different periods across variables | Use a common period and label exceptions |
| Correlation read as causation | Word relationships as association only |
| Slow global computation | Precompute layers offline |
| Live-demo failures | Pre-cache all data |

---

## 15. Team

| Name | Role | Responsibility |
|---|---|---|
| [NAME] | Data acquisition | Earthdata access, downloads, regridding |
| [NAME] | Analysis | Anomalies, trends, significance |
| [NAME] | Frontend | Map, change report panel |
| [NAME] | Backend / integration | API, layers, deployment |
| [NAME] | Pitch and documentation | Story, slides, validation write-up |

---

## 16. References

- NASA Earthdata: https://www.earthdata.nasa.gov
- Earthdata Search: https://search.earthdata.nasa.gov
- earthaccess documentation: https://earthaccess.readthedocs.io
- Giovanni: https://giovanni.gsfc.nasa.gov
- Mann, H. B. (1945) and Kendall, M. G. (1975): the Mann-Kendall trend test
- Sen, P. K. (1968): Estimates of the regression coefficient based on Kendall's tau (Theil-Sen estimator)
- Hamed, K. H. and Rao, A. R. (1998): A modified Mann-Kendall trend test for autocorrelated data
- Benjamini, Y. and Hochberg, Y. (1995): Controlling the false discovery rate

---

## 17. License

[Choose a license, for example MIT] and credit NASA for all source data. NASA Earth science data is generally open, but check the terms for each dataset.
