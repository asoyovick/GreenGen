# Scientific Methodology (Draft)

**Project:** GreenGen / Global Change Explorer  
**Investigation (MVP):** Precipitation Trends in Kenya (INV-001)  
**Dataset (planned):** NASA GPM IMERG (product/version to be finalized by data integration; no synthetic data used)  
**Status:** Draft for implementation and team review (issues #008, #009, #010, #011, #012, #013, #026, #031, #034)

> **Scientific integrity:** This engine processes validated observation inputs only. It does not fabricate NASA observations or scientific results, does not treat missing data as zero, and does not present trends as proof of causation. Statistical significance is not equivalent to practical/environmental importance. Uncertainty and limitations must be reported.

## 1. Scientific question
How has precipitation changed across different geographical locations in Kenya over a selected historical period, and where are those changes statistically significant at the grid-cell level?

## 2. Data requirements and input contract
- **Source:** Verified NASA Earth observation precipitation data (planned: GPM IMERG monthly precipitation), with dataset name/version, retrieval/provenance metadata, spatial/temporal coverage, CRS/grid definition, units, and quality/completeness information (see `docs/API_CONTRACTS.md` §2).
- **Dimensions:** `time`, `lat`, `lon` (native grid preserved where practical) or an agreed gridded/cell representation.
- **Units:** Explicit (e.g. `mm/month` for monthly precipitation; trend rates reported with derived units such as `mm/month/year` or `mm/year` as documented in outputs).
- **Missing/invalid:** Explicitly represented (NaN/mask/fill + documented semantics). Invalid/excluded observations must be traceable by flags/reasons; never imputed silently and never treated as zero.
- **Completeness:** Observation counts and completeness metrics provided/derived per cell and per aggregation period to determine eligibility.

## 3. Temporal aggregation
Implemented in `scientific_engine/aggregation.py` (and aligned with `src/skills/compute_trends.py`).

1. **Monthly input series:** Use validated monthly precipitation observations per grid cell `x(t, lat, lon)` with documented units and missingness.
2. **Monthly climatology and anomalies:** For each calendar month `m`, compute climatology `c(m) = mean_t(x | month(t)=m)` over valid observations in the analysis period (or agreed baseline, if specified). Monthly anomaly `a(t) = x(t) - c(month(t))`.
3. **Annual aggregation:** Annual mean anomaly `A(y) = mean_t(a(t) | year(t)=y)` computed only when the year has at least `min_months` valid monthly anomaly values (default `9`). Years not meeting this threshold are excluded (gap), not filled with zero.
4. **Completeness:** Track valid monthly/annual counts per cell (`n_months_valid`, `n_years`, `completeness`) for eligibility and reporting.
5. **Seasonal aggregation (optional/configured):** When requested, seasonal means/totals are computed from valid observations within defined season month sets; incomplete seasons are excluded per configured thresholds (documented in run metadata). MVP default is annual anomaly trend analysis.

**Handling rules:** time coordinates must be monotonic and correctly parsed; units preserved/converted explicitly; incomplete periods excluded; missing observations remain missing.

## 4. Trend detection (Mann–Kendall)
Implemented in `scientific_engine/trend_tests.py`.

- **Test:** Mann–Kendall trend test on the annual anomaly series per eligible cell, using the **Hamed–Rao variance correction** for autocorrelation (`pymannkendall.hamed_rao_modification_test`) to account for serial dependence in environmental time series.
- **Eligibility:** require at least `min_years` valid annual values (default `10`); cells below threshold are classified `insufficient_data` (no trend/significance assigned).
- **Outputs:** MK statistic/tau as available, two-sided `p_value`, and trend direction indicator (from sign of slope/statistic), plus flags when assumptions/record length limit interpretability.
- **Interpretation:** tests for monotonic trend evidence; non-significant does **not** imply stability/no change.

## 5. Trend magnitude (Sen’s slope)
Implemented in `scientific_engine/slope.py`.

- **Estimator:** Theil–Sen slope on valid annual anomaly values vs year (`scipy.stats.theilslopes` median pairwise slope).
- **Units:** slope reported in observation anomaly units per year (e.g. `mm/month/year` for monthly precipitation anomalies aggregated annually) and may also be reported per decade for convenience; units must be explicit in outputs.
- **Uncertainty:** report confidence interval for slope (e.g. from Theil–Sen interval at configured confidence level, default 95%) when computable; otherwise flag uncertainty unavailable.
- **Robustness:** if all valid values are constant, slope is 0 and significance handled accordingly; insufficient data yields no slope estimate.

## 6. Statistical reliability, uncertainty, and multiple testing
Implemented in `scientific_engine/reliability.py`.

- **Autocorrelation:** addressed in significance testing via Hamed–Rao modified Mann–Kendall variance correction (primary). Record length/assumption flags reported.
- **Multiple comparisons (grid-level):** apply **Benjamini–Hochberg FDR** correction across tested cells with finite p-values (`statsmodels.stats.multitest.multipletests`, method `fdr_bh`, `alpha` default `0.05`). Cells with insufficient/invalid data are excluded from the tested family (not treated as significant).
- **Uncertainty reporting:** include p-values, FDR-adjusted significance, slope confidence intervals, observation counts, completeness, and `low_confidence`/assumption flags (e.g. `n_years < ok_years`, default `15`).
- **Insufficient/inconclusive:** `insufficient_data` when eligibility/completeness thresholds not met; `inconclusive` when results are highly sensitive to assumptions or required reliability criteria are not satisfied (criteria recorded in metadata).

## 7. Grid-level classification
Implemented in `scientific_engine/grid_analysis.py`, aligned to `docs/API_CONTRACTS.md` legend semantics.

Per eligible cell:
- `significant_increase`: FDR-significant increasing trend.
- `significant_decrease`: FDR-significant decreasing trend.
- `no_significant_trend`: tested but not FDR-significant (not labeled “stable”).
- `insufficient_data`: not enough valid observations/years or completeness below threshold.
- `inconclusive`: cannot be interpreted as a clear class given documented criteria/flags.

No classification/trend assigned as a valid detected trend for `insufficient_data` cells.

## 8. Output fields (per cell, where available)
- Identifiers/geometry: `cell_id`, `lat`, `lon` (and/or geometry/indices)
- Data availability: `n_observations`, `n_years`, `completeness`, quality/validity flags
- Descriptive: mean/aggregated precipitation statistics with units (as applicable)
- Trend: `trend_direction`, `sens_slope` `{value, units, ci_lower, ci_upper}`
- Significance: `mann_kendall` `{statistic/tau, p_value}`, FDR-adjusted significance/`p_adjusted` as applicable
- Classification and flags: `classification`, `flags`, `low_confidence`
- Period/coverage: observation period used

**Run metadata:** dataset/version/provenance refs, bounds, period, aggregation config, thresholds (`min_months`, `min_years`, `ok_years`), alpha/FDR method, autocorrelation method, engine/methodology/software versions, timestamps.

## 9. Assumptions and limitations
- Monotonic-trend framework (Mann–Kendall/Sen’s slope) may not capture nonlinear/abrupt changes.
- FDR controls expected false discovery proportion among tested cells but does not fully resolve spatial dependence; regional claims require area-aggregated analysis.
- Short records reduce reliability (`< 10` years generally unreliable; `< 15` flagged low confidence).
- Results depend on input data quality, retrieval/subsetting, native grid/resolution, and chosen aggregation/thresholds.
- Observed statistical trends do not establish causation and may reflect variability or dataset artifacts; dataset version/processing changes must be considered.
- No synthetic data is used for real investigation results.

## 10. Reproducibility
Each execution must record inputs/provenance, configuration, methods, thresholds, software versions, and output schema version so results can be audited and reproduced given the same verified observations and contract.