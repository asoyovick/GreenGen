# Data Sources

**Purpose:** Record NASA datasets, access paths, metadata, provenance, quality, observation handoff contract, and reproducible sample extraction (issues #004, #030-#033, #031).  
**Status:** Living document — update when datasets/access/contracts change.  
**Rule:** Real NASA observations are required for real investigations. **No synthetic data is used or presented as real NASA observations/results.** Synthetic fixtures may appear only in isolated, clearly labeled tests.

## 1. Primary MVP dataset: NASA GPM IMERG

| Field | Value |
|---|---|
| Investigation | INV-001 Precipitation trends (MVP) |
| Program / Mission | NASA Global Precipitation Measurement (GPM) |
| Product family | Integrated Multi-satellitE Retrievals for GPM (IMERG) |
| Recommended MVP product | `GPM_3IMERGM` (IMERG Monthly), **Version 07** (verify in Earthdata Search/CMR before production use) |
| Variable (expected) | `precipitation` / monthly precipitation rate or accumulated monthly precipitation depending on product field; confirm units/variable name from granule metadata before ingestion |
| Units | Document from granule metadata (commonly mm/hr for IMERG rate fields; monthly products may expose mm/month-equivalent fields — **must be confirmed from product metadata and recorded in run metadata**) |
| Spatial resolution | ~0.1° x 0.1° (native IMERG grid) |
| Spatial coverage | Global (60°N-S for IMERG V07 standard products; confirm exact bounds) |
| Temporal coverage | June 2000-present (confirm exact coverage for selected version/product) |
| Temporal resolution | Monthly (for `GPM_3IMERGM`) |
| Format | NetCDF4/HDF5 (confirm per granule) |
| Access | NASA Earthdata (earthaccess/CMR/Harmony/GES DISC OPeNDAP/subsetting as appropriate) |
| Auth | NASA Earthdata Login required for most download/subsetting flows |
| DOI / citation | Record exact DOI from the dataset landing page before publication/demo; do not guess. |
| Quality/flags | Preserve IMERG quality/index/flags as available in selected product; document which fields are used for masking/completeness. |

### 1.1 Access and discovery references

- NASA Earthdata Search: https://search.earthdata.nasa.gov/
- NASA CMR API: https://cmr.earthdata.nasa.gov/search/
- GES DISC IMERG: https://disc.gsfc.nasa.gov/
- earthaccess Python library: https://github.com/nsidc/earthaccess
- Local skill references: `nasa-earthdata-access/SKILL.md`, `docs/nasa-data-guides/`

### 1.2 CMR discovery (Issue #030)

Use NASA CMR to discover collections/granules instead of hard-coding assumptions. Example query pattern (verify before use):

```bash
# Collection metadata (GPM_3IMERGM v07)
curl -s "https://cmr.earthdata.nasa.gov/search/collections.json?short_name=GPM_3IMERGM&version=07" | jq '.feed.entry[0] | {id,title,version_id,time_start,time_end,boxes}'

# Granules for Kenya bbox and period
curl -s "https://cmr.earthdata.nasa.gov/search/granules.json?short_name=GPM_3IMERGM&version=07&bounding_box=33.9,-4.7,41.9,5.5&temporal=2001-01-01T00:00:00Z,2020-12-31T23:59:59Z&page_size=10" | jq '.feed.entry[] | {title,time_start,time_end,links:[.links[]?|select(.rel=="http://esipfed.org/ns/fedsearch/1.1/data#")|.href]}'
```

Programmatic discovery script: `scripts/discover_imerg_cmr.py` (draft utility; requires network access; records query/results metadata). Cache discovery results where sensible and document query parameters for reproducibility.

## 2. Observation handoff contract (Data integration -> Scientific engine)

**Owners:** Member 2 & Member 3. **Status:** Draft contract recorded here and in `docs/API_CONTRACTS.md` (issue #031).  
This contract defines what validated observations look like when passed to the scientific engine.

### 2.1 Required structure

| Field | Type | Required | Description |
|---|---|---:|---|
| `contract` | string | yes | `observation-handoff` |
| `version` | string | yes | Contract version (e.g. `0.1-draft`) |
| `dataset` | object | yes | `short_name`, `version`, `doi?`, `source`, `variable`, `units` |
| `retrieved_at` | ISO8601 UTC string | yes | Retrieval/access timestamp |
| `bounds` | object | yes | `min_lon,min_lat,max_lon,max_lat` (WGS84 decimal degrees) |
| `period` | object | yes | `start,end` ISO dates/timestamps with documented inclusivity |
| `grid` | object | yes | CRS, native resolution, ordering, cell indexing conventions |
| `dimensions` | object/metadata | yes | `time,lat,lon` (and optional cell id mapping) |
| `variables.precipitation` | object | yes | units, fill/missing semantics, description |
| `quality` | object | yes | quality flags/masks, completeness method, exclusion reasons |
| `provenance` | object | yes | query/subsetting parameters, software versions, checksums/manifest refs when available |
| `data_ref` | string/object | yes | path/URI/object reference to actual observation payload; inline arrays only for tiny examples |

### 2.2 Missing/invalid observations

- Missing values are represented explicitly (`NaN`, mask, or documented fill value) and **never silently imputed**.
- Invalid/excluded observations must be traceable by quality flag or reason code.
- Provide observation counts and completeness inputs needed by analysis.
- Missing observations are **not treated as zero**.

### 2.3 Quality/completeness

- Preserve source quality flags/indices.
- Record completeness per cell/series (valid observations / expected observations) using the agreed method.
- Cells/periods below analysis thresholds become `insufficient_data` (not trend/significance outputs).

### 2.4 Example handoff metadata (illustrative shape; values must come from real retrieved data)

```json
{
  "contract": "observation-handoff",
  "version": "0.1-draft",
  "dataset": {
    "short_name": "GPM_3IMERGM",
    "version": "07",
    "source": "NASA GES DISC / Earthdata",
    "variable": "precipitation",
    "units": "mm/month",
    "doi": "TBD-record-from-dataset-landing-page"
  },
  "retrieved_at": "YYYY-MM-DDTHH:MM:SSZ",
  "bounds": {"min_lon": 33.9, "min_lat": -4.7, "max_lon": 41.9, "max_lat": 5.5},
  "period": {"start": "2001-01-01", "end": "2020-12-31"},
  "grid": {"crs": "EPSG:4326", "resolution_deg": 0.1, "ordering": "lat_ascending_lon_ascending"},
  "variables": {
    "precipitation": {
      "units": "mm/month",
      "fill_value": null,
      "missing_representation": "NaN",
      "description": "Monthly precipitation from GPM IMERG"
    }
  },
  "quality": {
    "source_flags": "record actual IMERG quality fields used",
    "completeness_method": "valid_months / expected_months_in_period",
    "exclusions": []
  },
  "provenance": {
    "query": {"short_name": "GPM_3IMERGM", "version": "07", "bbox": [33.9, -4.7, 41.9, 5.5], "temporal": ["2001-01-01", "2020-12-31"]},
    "tool": "earthaccess/cmr/harmony",
    "tool_version": "record-at-runtime"
  },
  "data_ref": "path/or/uri/to/validated-observation-payload"
}
```

## 3. Real sample extraction procedure (Issue #032)

**Requirement:** retrieve a small real Kenya sample (limited area and period) early so other members can build against real observations. Synthetic data must never stand in for this.

### 3.1 Prerequisites

- NASA Earthdata Login account.
- Credentials configured via `~/.netrc`, environment variables, or interactive `earthaccess.login()`.
- Python env with dependencies from `requirements.txt` / `nasa-earthdata-access` skill.

### 3.2 Reproducible extraction command (draft)

```bash
# 1) Authenticate (one-time setup)
# export EARTHDATA_USERNAME=... EARTHDATA_PASSWORD=...

# 2) Dry run discovery
python nasa-earthdata-access/scripts/download_granules.py \
  --short-name GPM_3IMERGM --version 07 \
  --start 2018-01-01 --end 2018-12-31 \
  --bbox 33.9 -4.7 41.9 5.5 \
  --dry-run

# 3) Download small sample (limited period/area)
python nasa-earthdata-access/scripts/download_granules.py \
  --short-name GPM_3IMERGM --version 07 \
  --start 2018-01-01 --end 2018-12-31 \
  --bbox 33.9 -4.7 41.9 5.5 \
  --out data/raw/imerg_kenya_sample

# 4) Record metadata
# - fill DOI in manifest.json
# - record checksums, file sizes, variable names, units, dimensions
# - store small derived metadata summary in docs or data/sample-metadata/
```

### 3.3 Sample documentation checklist

When a real sample is retrieved, record:
- [ ] Exact dataset short name, version, DOI
- [ ] Retrieval date/time and query parameters
- [ ] Bounding box and temporal range
- [ ] File format, dimensions, variables, units, fill values
- [ ] Quality flag fields present
- [ ] File sizes and storage location (repo small file or external link)
- [ ] Checksum/manifest
- [ ] How to regenerate

### 3.4 Current sample status

| Item | Status |
|---|---|
| Reproducible extraction procedure | Documented above |
| Real Kenya sample artifact in repo | **Not committed yet** — requires NASA Earthdata credentials/network access to retrieve; do not substitute synthetic data. |
| Sample metadata schema/example | Documented above (shape only; values must be filled from real retrieval) |

> **Action required:** A team member with Earthdata credentials should run the extraction procedure, verify metadata, and commit a small sample metadata/manifest (and small data file if licensing/size permits) or link an approved storage location. Update this section with actual retrieval date, DOI, checksums, and paths.

## 4. Data quality and limitations

- IMERG is a merged satellite/gauge product; uncertainties vary by region, season, surface type, and latency/product tier.
- Quality flags and completeness must be surfaced to users.
- Missing values are excluded from statistics, never imputed as zero.
- Native 0.1° grid should be preserved where practical; any resampling must be documented and justified.
- Trend results are statistical evidence, not causal attribution.

## 5. Provenance requirements (all investigations)

Every investigation result must record:
- dataset name/version/DOI (when available)
- retrieval date and query parameters
- geographical bounds and period
- processing configuration and thresholds
- statistical methods and software/methodology version
- data quality/completeness summary
- known limitations

## 6. Change log

| Date | Change |
|---|---|
| 2026-11-22 | Created DATA_SOURCES.md with MVP dataset, CMR discovery, observation handoff contract, sample extraction procedure, and provenance/quality rules. |
