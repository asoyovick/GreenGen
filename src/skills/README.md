# Vendored skill scripts and references

These files are copies of the hackathon skill bundles supplied with the project,
kept here so the pipeline and API can call the documented logic without the
skill directories being part of the application tree.

| File | Source | Purpose |
|---|---|---|
| `download_granules.py` | `nasa-earthdata-access/scripts/` | Verify, dry-run, download granules, write provenance manifest |
| `prep_cube.py` | `earth-data-prep/scripts/` | Standardize coords/units, regrid, write monthly Zarr cube |
| `compute_trends.py` | `trend-significance/scripts/` | Anomalies, Theil-Sen, Hamed-Rao Mann-Kendall, BH-FDR layers |
| `change_report.py` | `change-report/scripts/` | Ranked point report and plain-language wording |
| `wording_rules.md` | `change-report/references/` | Wording rules |
| `trend_method.md` | `trend-significance/references/` | Method notes |
| `dataset_cheatsheet.md` | `nasa-earthdata-access/references/` | Dataset starting points |

## Documented modifications

We extend, rather than fork, the skill logic:

1. `prep_cube.py`: adds `--synthetic` / metadata propagation so the cube carries
   `synthetic`, `model_based`, `surface`, and `display_name` attributes to the
   trend step. The cleaning, unit conversion, regridding and missing-month logic
   is unchanged. It also accepts `--mode` only to choose an output label.
2. `compute_trends.py`: propagates provenance attributes from the cube to the
   layer, and records `missing_months` in layer attributes. Statistical logic is
   unchanged.
3. `change_report.py`: `build_report` accepts an optional pre-opened `datasets`
   mapping so the API can load layers once at startup. Calling it with only
   paths behaves exactly as the skill documents.

The scripts are called as subprocesses by `scripts/run_pipeline.py`; their
original CLI interfaces remain usable.
