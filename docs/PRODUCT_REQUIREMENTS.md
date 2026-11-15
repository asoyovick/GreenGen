# Product Requirements Document (PRD)

**Project:** Earth System Trend Detective  
**Challenge:** NASA Space Apps Challenge 2026 — *Be an Earth System Trend Detective!*  
**Status:** Draft (living document)  
**Last updated:** 2026-11-14

## 1. Problem statement

NASA provides extensive Earth observation datasets (precipitation, temperature, vegetation, soil moisture, and more), but turning those datasets into reliable, place-based conclusions often requires users to discover appropriate products, understand metadata and quality, retrieve and subset observations, process large scientific files, handle missing data, run statistical trend analysis, and communicate findings accurately.

**Central question:** How can we make the identification, measurement, and interpretation of significant Earth system changes geographically accessible, scientifically reliable, and understandable to different categories of users?

## 2. Target users

| Audience | Primary needs |
|---|---|
| Scientists | Statistical evidence, methodology, uncertainty, detailed and reproducible results. |
| Researchers | Historical observations, geographical comparisons, reproducible analysis. |
| Students | Guided investigations and understandable scientific explanations. |
| Journalists | Credible findings, geographical context, accessible summaries. |
| Educators | Demonstrations, teaching resources, investigation exercises. |

One scientific analysis engine produces the results; presentation levels may differ by audience but must never change the scientific conclusion.

## 3. Proposed solution

A guided scientific investigation platform where a user selects a predefined investigation, chooses a geographical area and historical period, and runs an analysis. The system:

1. Retrieves relevant NASA observations.
2. Validates observations and quality information.
3. Processes data into appropriate temporal form.
4. Performs grid-level geographical analysis (preserving native grid where practical).
5. Tests for statistically significant trends and estimates magnitude/uncertainty.
6. Generates interactive visualizations and scientific reports with provenance.

## 4. Core capabilities and priorities

| Capability | Description | Priority |
|---|---|---|
| Investigation catalogue | Predefined scientific investigations with questions, datasets, variables, outputs. | Critical |
| Investigation configuration | Select geography and historical period. | Critical |
| NASA data integration | Retrieve actual observations from NASA datasets/services. | Critical |
| Data validation | Missing observations, quality flags, completeness. | Critical |
| Grid-level analysis | Analyse eligible grid cells independently. | Critical |
| Trend detection | Increasing/decreasing monotonic trends. | Critical |
| Statistical significance | Evidence supporting detected trends (with documented assumptions). | Critical |
| Trend magnitude | Estimated rate of change (e.g. Sen's slope) with units. | Critical |
| Interactive maps | Geographical trend classifications and cell inspection. | High |
| Time-series visualization | Historical observations and fitted trend context. | High |
| Scientific reports | Methodology, findings, limitations, provenance, export. | High |
| AI explanations | Explain verified findings in understandable language. | Later |

## 5. MVP scope

**In scope (MVP):** one complete, scientifically reliable investigation:
- **Investigation 001 — Precipitation trends** (Kenya, user-selected supported period within dataset coverage, NASA **GPM IMERG** monthly precipitation as the primary product; exact product/version finalized in data research issues #004/#030).

**Out of scope for MVP implementation (documented as future):** temperature, soil moisture, vegetation investigations as fully functional analyses; AI-generated explanations as a source of facts; global coverage beyond what is validated.

**Scope-reduction rule:** if the Day 3 checkpoint (real NASA observations passing through the scientific analysis pipeline) is missed, reduce scope/polish rather than adding unfinished features (see integration checkpoints in `docs/SYSTEM_ARCHITECTURE.md`).

## 6. Project-wide acceptance criteria

### Data
- System retrieves actual NASA GPM IMERG observations for supported investigations.
- User can select a supported geographical area and historical period.
- Dataset metadata, version, and quality information are preserved.

### Scientific analysis
- Observations processed correctly with transparent handling of missing/incomplete periods.
- Eligible grid cells analysed independently; native grid preserved where practical.
- Trend direction and magnitude calculated with units and confidence/uncertainty reported.
- Statistical significance evaluated appropriately; multiple testing addressed for grid analyses.
- Insufficient or inconclusive results are identified and not mislabelled (e.g. non-significant ≠ stable).

### User experience
- Users browse predefined investigations and distinguish implemented vs planned.
- Users configure area/period, execute, and explore grid-level results and time series.
- Users can understand findings, limitations, and how results were produced.

### Reproducibility
Every investigation result records: dataset name/version, retrieval date, period, geographical bounds, processing configuration, statistical methods, software/methodology version, and data quality information.

## 7. Project rules

1. **No fabricated scientific results.** Real investigations use actual NASA observations; synthetic fixtures must be clearly labelled and never presented as real results.
2. **No unsupported environmental claims.** A detected trend does not establish cause.
3. **No premature feature expansion.** Complete precipitation MVP before implementing all investigations.
4. **No unreviewed scientific calculations.** Statistical methods independently validated and reviewed (scientific owner required).
5. **No disconnected development.** Agree on API/data contracts before dependent implementation.
6. **No direct commits to `main`.** Use branches and pull requests with review.
7. **No hidden uncertainty.** Surface incomplete data, inconclusive results, and methodological limits.
8. **No AI-generated scientific facts.** Analysis engine computes results; AI may only explain verified outputs (future).

## 8. Related documents

- `docs/CONTRIBUTION.md` — team handbook and backlog context
- `docs/INVESTIGATION_CATALOGUE.md` — investigation definitions (#002)
- `docs/SYSTEM_ARCHITECTURE.md` — architecture and integration plan (#026)
- `docs/API_CONTRACTS.md` — cross-team contracts (#026)
- `docs/TESTING_STRATEGY.md` — testing and validation (#050)
- `docs/DATA_SOURCES.md` — datasets and provenance notes
- `README.md` — current prototype status and run instructions
