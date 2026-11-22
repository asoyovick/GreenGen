# Bug Triage and Reporting

**Purpose:** Keep defects visible and resolved before demonstration (issue #055).

## 1. Reporting

- Use the GitHub bug report template: `.github/ISSUE_TEMPLATE/bug_report.md`.
- Every bug report must include severity, area, reproduction steps, expected/actual behavior, and evidence.
- Scientific-validity bugs must be labeled `science` and `bug`, and marked as demo-blocking until resolved or explicitly documented.

## 2. Severity levels

| Severity | Meaning | Target response |
|---|---|---|
| Critical | Scientific validity/data integrity/security/demo-blocking | Triage immediately; block demo/release until fixed or documented |
| High | Major feature broken or incorrect user-visible behavior | Fix before next milestone/demo |
| Medium | Degraded behavior with workaround | Schedule and track |
| Low | Cosmetic/minor | Backlog |

## 3. Triage cadence

- Review new bugs at daily check-in (or earliest team sync).
- Confirm reproducibility and severity.
- Assign owner and milestone.
- Track status: `new -> triaged -> in_progress -> fixed -> verified -> closed`.
- Retest fixes; add regression test where feasible.

## 4. Scientific validity bug handling

Any bug affecting statistical results, data quality handling, provenance, or user-facing scientific claims is treated as high/critical until reviewed.

Required actions:
- record affected executions/datasets/configs
- assess impact on reported results
- fix or clearly document limitation
- add regression/validation test
- obtain scientific owner review for methodology-related fixes

## 5. Current known issues (track in GitHub Issues)

Use GitHub Issues as the source of truth. This document defines process; do not duplicate stale bug lists here.

## 6. Change log

| Date | Change |
|---|---|
| 2026-11-22 | Initial bug triage process and severity definitions added. |
