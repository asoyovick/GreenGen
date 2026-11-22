# Scientific Validation Report

**Purpose:** Collect evidence that scientific results can be trusted (issue #053).  
**Status:** Draft/in-progress — based on implemented tests and documented methods; real NASA end-to-end validation requires credentialed data access and independent review.  
**Rule:** Do not claim results are scientifically validated beyond the evidence recorded here.

## 1. Scope

This report covers the current GreenGen scientific engine and analysis workflow, primarily the MVP precipitation investigation (INV-001, GPM IMERG design target).

## 2. Methods under validation

| Method | Implementation | Reference/expectation | Evidence |
|---|---|---|---|
| Monthly climatology anomaly + annual aggregation | `scientific_engine/aggregation.py` | Exclude incomplete years; missing != zero | `tests/test_scientific_engine.py::test_annual_aggregation_excludes_incomplete_years`, `test_missing_data_not_treated_as_zero` |
| Mann-Kendall trend test (Hamed-Rao autocorrelation correction) | `scientific_engine/trend.py` via `pymannkendall.hamed_rao_modification_test` | Independent reference: `pymannkendall` direct call on same series | `test_trend_statistics_match_independent_reference_implementations` |
| Theil-Sen slope + CI | `scientific_engine/trend.py` via `scipy.stats.theilslopes` | Independent reference: `scipy.stats.theilslopes` direct call | `test_trend_statistics_match_independent_reference_implementations` |
| Benjamini-Hochberg FDR | `scientific_engine/reliability.py` via `statsmodels.stats.multitest.multipletests` | Non-finite p-values excluded; finite p-values corrected | `test_fdr_excludes_nonfinite_pvalues` |
| Classification semantics | `scientific_engine/reliability.py` | Required classes: significant increase/decrease, no significant trend, insufficient data, inconclusive | `test_classify_cell_covers_all_required_classes` |
| Insufficient data handling | `scientific_engine/trend.py`, `grid_analysis.py` | No trend/significance assigned below min years | `test_insufficient_data_no_trend_assigned` |
| Determinism/provenance metadata | `scientific_engine/grid_analysis.py` | Same inputs/config => same outputs except timestamp | `test_analysis_output_includes_reproducibility_metadata_and_is_deterministic` |

## 3. Controlled test cases (synthetic fixtures, clearly labeled)

> All fixtures in `tests/test_scientific_engine.py` are programmatically generated for isolated mathematical validation. They are **not** NASA observations.

| Case | Expected | Result | Status |
|---|---|---|---|
| Strong increasing signal | increasing, positive slope, significant_increase | Pass | Evidence in test suite |
| Strong decreasing signal | decreasing, negative slope, significant_decrease | Pass | Evidence in test suite |
| Noise/no trend | no_significant_trend or inconclusive (not significant) | Pass | Evidence in test suite |
| Insufficient years | insufficient_data, no slope/p-value/direction | Pass | Evidence in test suite |
| Missing data scattered | missing excluded, not treated as zero; observations < total | Pass | Evidence in test suite |
| Ties/missing handling | finite outputs, no zero-imputation artifact | Pass | Evidence in test suite |
| Constant series | no_trend, slope 0, p=1 | Pass | Evidence in test suite |

## 4. Independent/reference comparisons

- **Theil-Sen:** compared against `scipy.stats.theilslopes` on identical series; slope and CI matched within `atol=1e-12`.
- **Mann-Kendall (Hamed-Rao):** compared against `pymannkendall.hamed_rao_modification_test` on identical series; p-value and Tau matched within `atol=1e-12`.
- **FDR:** uses `statsmodels` BH implementation; test confirms non-finite p-values are excluded before correction.

## 5. Real-data validation status

| Check | Status | Notes |
|---|---|---|
| Real GPM IMERG retrieval for Kenya sample | Pending credentials/network | Procedure documented in `docs/DATA_SOURCES.md` and `docs/REPRODUCIBILITY.md` |
| Grid alignment against native 0.1° IMERG | Pending real sample | Must verify cell centers/ordering/resolution against source granule metadata |
| Subsetting correctness vs source | Pending real sample | Compare subset to source values/coords |
| Missing-data/quality flag behavior on real product | Pending real sample | Validate fill values, quality flags, completeness |
| End-to-end investigation with real NASA observations | Pending integration run | Requires engine + backend + real observation_ref |

## 6. Discrepancies and resolutions

| Discrepancy | Impact | Resolution/status |
|---|---|---|
| No real NASA sample artifact committed | Cannot claim real-data E2E validation complete | Documented procedure; requires credentialed retrieval (issue #032) |
| Python test deps not installed in all environments | Validation not reproducible without env setup | Documented in `requirements.txt`/REPRODUCIBILITY.md; CI should install deps |
| Seasonal analysis coverage limited | Seasonal INV-001 requirement partially addressed | Seasonal aggregation/analysis to be implemented/extended (issue #35) |

## 7. Limitations

- Controlled synthetic fixtures validate math/logic, not real-world NASA data quality issues.
- Statistical significance does not imply causation.
- Autocorrelation correction and FDR reduce but do not eliminate false inference risk.
- Results depend on dataset version, quality masking, period, bounds, and thresholds.
- Real-data validation and independent scientific review (Member 3/Member 1) are still required before claiming full scientific defensibility.

## 8. Review and sign-off

- **Scientific analysis owner (Member 3):** review required.
- **Product/scientific coordination (Member 1):** review required.
- **QA/documentation (Member 6):** draft prepared; evidence linked to tests/docs.

## 9. Change log

| Date | Change |
|---|---|
| 2026-11-22 | Initial draft validation report based on existing engine tests and documented gaps. |
