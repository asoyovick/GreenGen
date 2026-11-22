# Demo Narrative and Challenge Alignment

**Purpose:** Verify the MVP against the NASA Space Apps Challenge "Be an Earth System Trend Detective" and provide a clear demo story (issue #029).  
**Status:** Draft — update with actual demo evidence/screenshots before presentation.

## 1. Challenge-to-evidence checklist

| Challenge requirement | GreenGen response | Evidence | Status |
|---|---|---|---|
| Identify Earth science variables that indicate environmental change | INV-001 precipitation investigation; catalogue documents future variables | `docs/INVESTIGATION_CATALOGUE.md`, backend seeded investigations | Partial |
| Visualize how variables change over time | Time series and trend context in prototype/frontend; report outputs in engine/backend contracts | `frontend/src/components/TrendChart.jsx`, `scientific_engine/grid_analysis.py`, API contracts | Partial |
| Determine where changes are occurring | Grid-cell analysis over selected bounds; map overlays/prototype map | `scientific_engine/grid_analysis.py`, `src/api/main.py`, frontend map components | Partial |
| Quantify magnitude and direction of changes | Theil-Sen slope per year with CI; direction/classification | `scientific_engine/trend.py`, `tests/test_scientific_engine.py` | Pass (controlled tests) |
| Establish statistical significance | Mann-Kendall with Hamed-Rao correction + BH FDR | `scientific_engine/trend.py`, `scientific_engine/reliability.py` | Pass (controlled tests) |
| Explain why same variable may behave differently across regions | Grid-level analysis preserves spatial variation; demo narrative compares regions/cells; no single global average claim | `docs/SCIENTIFIC_METHODOLOGY.md`, demo script below | Partial (needs live demo evidence) |

## 2. Demo script (Kenya precipitation question)

### Setup (before demo)
- Confirm environment is running and data source/provenance are visible.
- If using real NASA data, have retrieval manifest/provenance ready. If not, clearly state that controlled fixtures are for math validation only and do not represent real NASA observations.

### Narrative
1. **Problem:** "Earth observation data is abundant, but identifying meaningful local trends is hard. A global average can hide regional differences."
2. **Question:** "How has precipitation changed across Kenya over a selected historical period, and where are those changes statistically significant?"
3. **Select investigation:** Show INV-001 Precipitation Trends. Point out dataset (NASA GPM IMERG), bounds, period, and methodology summary.
4. **Run analysis:** Submit execution; show status transitions (queued/running/completed/failed) coming from backend.
5. **Show map:** Display grid-cell classifications: significant increase, significant decrease, no significant trend detected, insufficient data, inconclusive.
6. **Inspect a cell:** Open a cell detail with n observations, completeness, mean, Sen's slope + CI, Mann-Kendall p-value, FDR-significant flag, classification, and quality flags.
7. **Show time series:** Observed values over time; explain trend context and uncertainty. Missing values are excluded, not treated as zero.
8. **Compare neighbors:** Highlight that nearby cells can show different directions/magnitudes - same variable, different regional behavior.
9. **Report/export:** Show provenance (dataset/version, retrieval date, bounds, period, methods, config), limitations, and "not causal" disclaimer.
10. **Close with integrity:** State what is validated, what is pending real-data confirmation, and known limitations.

## 3. Claims guardrails (must say / must not say)

| Must say | Must not say |
|---|---|
| "Statistically significant trend detected" (with alpha/FDR/method) | "Proves climate change caused X" |
| "No statistically significant trend detected" | "Stable" (unless separately defined and justified) |
| "Based on selected dataset/version/bounds/period" | "This is true everywhere/always" |
| "Insufficient data/inconclusive" when applicable | Hide uncertainty or fabricate missing results |
| "Observed change, not a forecast" | "Will continue at same rate" |

## 4. Presentation readiness checklist

- [ ] Requirements-to-evidence checklist reviewed and updated with actual demo artifacts.
- [ ] Demo uses real NASA observations or clearly labels any controlled test fixture as non-real.
- [ ] Provenance visible in UI/report.
- [ ] Known limitations slide/section included.
- [ ] No causal claims in script/slides.
- [ ] Backup screenshots/video for network/API failure scenarios.

## 5. Change log

| Date | Change |
|---|---|
| 2026-11-22 | Initial demo narrative and challenge-evidence checklist created. |
