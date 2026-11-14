# Investigation Catalogue

**Purpose:** Define the predefined scientific investigations supported by the platform (issue #002).  
**Status:** Draft — MVP investigation defined; future investigations documented but **not implemented**.

## Catalogue overview

| ID | Investigation | Dataset (planned/selected) | MVP status |
|---|---|---|---|
| INV-001 | Precipitation trends | NASA GPM IMERG (monthly product, version per #004/#030) | **Implemented target for MVP** |
| INV-002 | Temperature trends | TBD (e.g. land/air temperature products) | Planned (future) |
| INV-003 | Soil moisture trends | TBD | Planned (future) |
| INV-004 | Vegetation trends | TBD (e.g. NDVI/EVI products) | Planned (future) |

**Rule:** An investigation must not appear as fully functional until dataset integration, processing configuration, and scientific methodology have been implemented and validated.

---

## INV-001: Precipitation trends (MVP)

### Scientific question
How has precipitation changed across different geographical locations in the selected study area (initial focus: **Kenya**) over a selected historical period, and where are those changes statistically significant?

### Dataset and source
- **Primary dataset:** NASA Global Precipitation Measurement (GPM) Integrated Multi-satellitE Retrievals for GPM (**IMERG**).
- **Product/version/variable:** to be finalized and recorded in `docs/DATA_SOURCES.md` per issues #004/#030 (including monthly precipitation variable name, units, spatial/temporal coverage, quality fields, and access method).
- **Notes:** preserve source metadata, quality information, and native grid where practical (IMERG ~0.1°). Do not resample to imply false precision.

### Variables (supported in MVP design)
- Monthly precipitation (derived/aggregated as appropriate from source resolution)
- Annual precipitation
- Seasonal precipitation (season definitions documented in methodology; e.g. Kenya rainy seasons, to be agreed in #008/#035)

### Geographical and temporal scope
- **Initial geography:** Kenya (supported bounds/presets defined by implementation; user selection within supported area).
- **Historical period:** user-selectable within the validated coverage of the selected IMERG product; UI and API must reject unsupported periods.

### Expected outputs (per eligible grid cell and aggregated summaries)
- Observation count and data completeness
- Mean precipitation over selected period (with units)
- Trend direction (increasing/decreasing) where applicable
- Sen's slope (rate of change) with units and confidence interval
- Mann–Kendall (or approved variant) test statistic and p-value
- Appropriately corrected significance/multiple-testing results (e.g. FDR) as defined by methodology
- Classification: **Significant increase**, **Significant decrease**, **No significant trend detected**, **Insufficient data**, or **Inconclusive** (definitions per #036; non-significant must not be labelled "stable")
- Quality/limitation flags and provenance (dataset/version, retrieval date, bounds, period, methods, config)

### Visualizations and reports
- Interactive grid-level trend map with legend and cell inspection
- Historical time series (observations vs trend context) for selected cells/areas
- Scientific report/export including methodology summary, uncertainty, and limitations

### Investigation-specific scientific requirements
- Document temporal aggregation, seasonality, autocorrelation handling, significance thresholds, and multiple-testing correction (#008).
- Validate against independent calculations/reference cases (#021/#038/#053).
- Record all assumptions and limitations alongside results.

---

## INV-002: Temperature trends (future)

### Scientific question
How have temperature conditions changed geographically over time in the selected area and period?

### Potential dataset/variables (to be confirmed)
- Land surface temperature, atmospheric/reanalysis temperature, or temperature anomalies (product selection must be evidence-based and documented before implementation).

### Expected outputs
Analogous to INV-001 (grid-level trends, magnitude, significance, uncertainty, classifications) with temperature-appropriate units and quality considerations.

**Status:** Future investigation — not available in MVP.

---

## INV-003: Soil moisture trends (future)

### Scientific question
How has soil moisture changed across geographical locations over the selected period?

### Potential findings
Increasing soil moisture, decreasing soil moisture, no statistically significant trend detected, insufficient/inconclusive results.

**Status:** Future investigation — not available in MVP.

---

## INV-004: Vegetation trends (future)

### Scientific question
How has vegetation greenness changed geographically over the selected period?

### Potential variables (to be confirmed)
- Normalized Difference Vegetation Index (NDVI)
- Enhanced Vegetation Index (EVI)

**Status:** Future investigation — not available in MVP.

---

## Change log

| Date | Change |
|---|---|
| 2026-11-14 | Initial catalogue: INV-001 MVP defined; INV-002–004 documented as future. |
