# Scientific Methodology (Implementation-Aligned)

**Project:** GreenGen / Global Change Explorer  
**Investigation (MVP):** Precipitation Trends in Kenya (INV-001)  
**Dataset (planned/target):** NASA GPM IMERG (product/version finalized through data integration contracts; no synthetic data used for real results)  
**Status:** Implementation-aligned draft (reconciled with current `scientific_engine/` implementation; pending final team/reviewer sign-off)

> **Scientific integrity:** The engine processes validated observation inputs only. It does not fabricate NASA observations or scientific results, does not treat missing data as zero, and does not present trends as proof of causation. Statistical significance is not equivalent to practical or environmental importance. Uncertainty, assumptions, and limitations must be reported. Non-significant results must not be described as "stable" or "no change."

## 1. Scientific question
How has precipitation changed across different geographical locations in Kenya over a selected historical period, and where are those changes statistically significant at the grid-cell level?

## 2. Data requirements and input contract
- **Source:** Verified NASA Earth observation precipitation data (planned: GPM IMERG monthly precipitation), with dataset name/version, retrieval/provenance metadata, spatial/temporal coverage, CRS/grid definition, units, and quality/completeness information (see `docs/API_CONTRACTS.md` §2).
- **Dimensions:** `time`, `lat`, `lon` (native grid preserved where practical) or an agreed gridded/cell representation.
- **Units:** Explicit (e.g. `mm/month` for monthly precipitation; trend rates reported with derived units such as `mm/month/year` or `mm/year` as documented in outputs).
- **Missing/invalid:** Explicitly represented (NaN/mask/fill + documented semantics). Invalid/excluded observations must be traceable by flags/reasons; never imputed silently and never treated as zero.
- **Completeness:** Observation counts and completeness metrics provided/derived per cell and per aggregation period to determine eligibility.

## 3. Temporal aggregation
Implemented in `scientific_engine/aggregation.py` and used by `scientific_engine/grid_analysis.py`.

1. **Monthly input series:** Use validated monthly precipitation observations per grid cell `x(t, lat, lon)` with documented units and missingness.
2. **Monthly climatology and anomalies:** For each calendar month `m`, compute climatology `c(m) = mean_t(x | month(t)=m)` over valid observations in the analysis period (or agreed baseline, if specified). Monthly anomaly `a(t) = x(t) - c(month(t))`.
3. **Annual aggregation (implemented):** Annual mean anomaly `A(y) = mean_t(a(t) | year(t)=y)` computed only when the year has at least `min_months` valid monthly anomaly values (default `9`). Years not meeting this threshold are excluded (gap), not filled with zero.
4. **Completeness (implemented):** Track valid monthly/annual counts per cell (`n_observations`, `n_years`, `completeness`) for eligibility and reporting.
5. **Seasonal aggregation (implemented, configurable):** Seasonal means of monthly anomalies are computed per configured season month sets. Incomplete seasons are excluded when valid-month thresholds are not met (never treated as zero). Default Kenya seasons are documented as `MAM` (Mar-May, long rains), `JJAS` (Jun-Sep), `OND` (Oct-Dec, short rains), and `JF` (Jan-Feb), with rationale based on Kenya's bimodal rainfall regime; season definitions are configurable in analysis config and recorded in run metadata. Current implementation computes per-season trend statistics (Mann-Kendall Hamed-Rao + Theil-Sen + classification) across years for each season.

**Handling rules:** time coordinates must be monotonic and correctly parsed; units preserved/converted explicitly; incomplete periods excluded; missing observations remain missing.

## 4. Trend detection (Mann–Kendall)
Implemented in `scientific_engine/trend.py` (`compute_trend`).

- **Test (implemented):** Mann–Kendall trend test on the annual anomaly series per eligible cell, using the **Hamed–Rao variance correction** for autocorrelation (`pymannkendall.hamed_rao_modification_test`) to account for serial dependence in environmental time series.
- **Eligibility (implemented):** require at least `min_years` valid annual values (default `10`); cells below threshold are classified `insufficient_data` (no trend/significance assigned).
- **Outputs (implemented):** MK statistic/tau (when available), two-sided `p_value`, and trend direction indicator, plus flags when assumptions/record length or estimation issues limit interpretability.
- **Interpretation:** tests for monotonic trend evidence; non-significant does **not** imply stability/no change.

## 5. Trend magnitude (Sen’s slope)
Implemented in `scientific_engine/trend.py` (`compute_trend`).

- **Estimator (implemented):** Theil–Sen slope on valid annual anomaly values vs year (`scipy.stats.theilslopes`, median pairwise slope).
- **Units (implemented):** slope reported with explicit units (e.g. `mm/month/year` for monthly precipitation anomalies aggregated annually, as configured in outputs/metadata).
- **Uncertainty (implemented):** slope confidence interval reported from Theil–Sen interval at configured confidence level (`alpha_ci`, default `0.95`) when computable; otherwise flagged.
- **Robustness (implemented):** if all valid values are constant, slope is `0`, p-value `1.0`, direction `no_trend`; insufficient data yields no slope/significance estimate. If MK or slope estimation fails, flags are set and classification may become `inconclusive`.

## 6. Statistical reliability, uncertainty, and multiple testing
Implemented in `scientific_engine/reliability.py`.

- **Autocorrelation:** addressed in significance testing via Hamed–Rao modified Mann–Kendall variance correction (primary). Record length/assumption flags reported.
- **Multiple comparisons (grid-level):** apply **Benjamini–Hochberg FDR** correction across tested cells with finite p-values (`statsmodels.stats.multitest.multipletests`, method `fdr_bh`, `alpha` default `0.05`). Cells with insufficient/invalid data are excluded from the tested family (not treated as significant).
- **Uncertainty reporting:** include p-values, FDR-adjusted significance, slope confidence intervals, observation counts, completeness, and `low_confidence`/assumption flags (e.g. `n_years < ok_years`, default `15`).
- **Insufficient/inconclusive:** `insufficient_data` when eligibility/completeness thresholds not met; `inconclusive` when results are highly sensitive to assumptions or required reliability criteria are not satisfied (criteria recorded in metadata).

## 7. Grid-level classification
Implemented in `scientific_engine/grid_analysis.py` and `scientific_engine/reliability.py`, aligned to `docs/API_CONTRACTS.md` semantics.

Per eligible cell:
- `significant_increase`: FDR-significant increasing trend.
- `significant_decrease`: FDR-significant decreasing trend.
- `no_significant_trend`: tested but not FDR-significant (evidence does not establish a significant trend; **not** labeled "stable" or "no change").
- `insufficient_data`: not enough valid observations/years or completeness below threshold.
- `inconclusive`: cannot be interpreted as a clear class given documented criteria/flags (e.g. failed test/slope estimation or sensitivity to assumptions).

No classification/trend is assigned as a valid detected trend for `insufficient_data` cells (slope/significance outputs are withheld).

### Legend wording (for UI/reports)
- **Significant increase:** "Statistically significant increasing trend detected (after multiple-testing correction)." 
- **Significant decrease:** "Statistically significant decreasing trend detected (after multiple-testing correction)."
- **No significant trend:** "No statistically significant trend detected. This does not mean conditions were stable or unchanged."
- **Insufficient data:** "Insufficient valid observations to assess a trend for this cell."
- **Inconclusive:** "Trend evidence is inconclusive given data quality, record length, or methodological assumptions."

Statistical significance, trend magnitude (Sen's slope with uncertainty), and classification are reported separately; p-values alone are never treated as proof.

## 8. Output fields (per cell, where available)
- Identifiers/geometry: `cell_id`, `lat`, `lon` (and/or geometry/indices)
- Data availability: `n_observations`, `n_years`, `completeness`, quality/validity flags
- Descriptive: mean/aggregated precipitation statistics with units (as applicable)
- Trend: `trend_direction`, `sens_slope` `{value, units, ci_lower, ci_upper}`
- Significance: `mann_kendall` `{statistic/tau, p_value}`, FDR-adjusted significance/`p_adjusted` as applicable
- Classification and flags: `classification`, `flags`, `low_confidence`
- Period/coverage: observation period used

**Run metadata:** dataset/version/provenance refs, bounds, period, aggregation config, thresholds (`min_months`, `min_years`, `ok_years`), alpha/FDR method, autocorrelation method, engine/methodology/software versions, timestamps.

## 9. Assumptions and limitations (explicit)

### Assumptions
- Input observations are validated, correctly georeferenced, time-ordered, and use documented units/quality semantics (per data contracts).
- Annual anomaly trend analysis (current implementation) is an appropriate summary for the configured period; monthly climatology is computed over the provided analysis subset unless a different baseline is explicitly defined by upstream contracts/config.
- Mann–Kendall with Hamed–Rao correction addresses serial dependence to a practical extent for monotonic trend testing, but does not remove all dependence/assumption concerns.
- Benjamini–Hochberg FDR controls expected false discovery proportion across tested cells but does not fully model spatial dependence.

### Limitations
- **Methodological:** monotonic-trend framework (Mann–Kendall/Sen’s slope) may miss nonlinear, step-change, or regime-shift behavior.
- **Seasonality:** seasonal aggregation and per-season trend analysis are implemented with configurable season definitions. Default Kenya seasons (MAM/JJAS/OND/JF) are documented; alternative season definitions must be recorded in run metadata. Seasonal significance is currently evaluated per season (p-value threshold) and should be interpreted alongside annual/FDR results and documented assumptions.
- **Data quality/coverage:** missing observations, quality flags, sensor/dataset changes, and subsetting choices affect results; incomplete periods/years are excluded per thresholds.
- **Record length:** `< min_years` (default 10) is insufficient for trend assessment; `< ok_years` (default 15) is flagged low confidence.
- **Spatial dependence and scale:** grid-level FDR does not eliminate spatial autocorrelation effects; regional conclusions require area-appropriate aggregation/interpretation. Native grid and bounds determine representativeness.
- **Interpretation:** statistical significance does not imply causation, practical importance, or future behavior. Non-significant does not imply stability/no change.
- **Integration status:** end-to-end real NASA retrieval/ingestion and final contract sign-off depend on data/backend integration work; this document describes the implemented analysis methodology and its current constraints.

No synthetic data is used for real investigation results. Controlled synthetic fixtures may be used only in isolated tests and must be clearly labeled.

## 10. Plain-language explanations (for user guide/reporting)
- **Trend:** the general direction of change over time in the data we analyzed (increasing, decreasing, or no significant trend detected).
- **Mann–Kendall test:** a statistical test used to check whether there is evidence of a consistent upward or downward trend over time. It is adjusted here (Hamed–Rao) to better handle year-to-year dependence in environmental data.
- **Sen’s slope:** an estimate of how fast values are changing over time (the trend magnitude), reported with units and an uncertainty range (confidence interval) when available.
- **Statistical significance:** indicates that the observed pattern is unlikely to be explained by random variation alone under the test assumptions. It does **not** prove the cause of change and does **not** measure how important the change is.
- **FDR correction:** when many grid cells are tested, some may appear significant by chance. FDR correction reduces this risk across the whole map.
- **No significant trend:** the analysis did not find strong enough statistical evidence for a trend. This does **not** mean conditions stayed the same.
- **Insufficient data / inconclusive:** there was not enough reliable data, or the result is too sensitive to assumptions/issues, to classify a clear trend for that location.

## 11. Reproducibility
Each execution must record inputs/provenance, configuration, methods, thresholds, software versions, and output schema version so results can be audited and reproduced given the same verified observations and contract. The current engine emits run metadata (methods, parameters, dataset/bounds/period, engine version, timestamps, grid info) alongside per-cell results.

## 10. Reproducibility
Each execution must record inputs/provenance, configuration, methods, thresholds, software versions, and output schema version so results can be audited and reproduced given the same verified observations and contract.