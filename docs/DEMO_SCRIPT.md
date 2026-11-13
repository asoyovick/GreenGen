# Demo Script

A short, reliable walkthrough for Global Change Explorer. The default demo uses
**synthetic** precomputed layers so it works offline and deterministically.

## Before the demo (once)

```bash
make install          # first time only
make synthetic
make pipeline         # prep + trends + overlays (~minutes on full global grid)
make demo             # builds frontend and serves API+UI on :8000
# or: make api and, in another terminal, make frontend
```

Open: <http://127.0.0.1:8000> (or the Vite dev URL when using `make frontend`).

**Check:** the persistent banner reads **“SYNTHETIC DEMO DATA, not real
observations.”** If it does not, stop and confirm you are not mixing modes.

## 2–4 minute walkthrough

### 1. Orient (15–20s)

- “This is a map-first change explorer. Every layer is precomputed — the API
  only does lookups, it never downloads NASA data or runs trend tests on click.”
- Point out the synthetic banner, the layer switcher, and the footer note:
  **observed change only, not a forecast**.

### 2. Click a planted increasing land point (30–45s)

- Click around **55°N, 55°E** (or search/enter coordinates).
- Show the report: ranked variables, **significant** verdicts, rate per decade,
  years used, and that vegetation applies on land.
- Emphasise: significance means **FDR-corrected** Mann–Kendall (Hamed–Rao), not
  a raw p-value. Non-significant would mean “not detected”, not “no change”.

### 3. Show opposite trends / divergence (30–45s)

- Move east to around **55°N, 85°E**.
- Show that planted variables flip direction (e.g. vegetation/precipitation
  decrease) and the nearby comparison highlights opposite directions within the
  window.
- Message: the same variable can trend different ways in neighbouring regions;
  a single point is not the whole story.

### 4. Show an ocean / non-applicable case (20–30s)

- Click open ocean, e.g. **0°, -150°**.
- Vegetation is absent because it does not apply over ocean; remaining
  variables are still reported with the same statistical framing.

### 5. Inspect a time series and provenance (30–45s)

- Select a variable and show the annual-anomaly chart with the Theil–Sen trend
  line reconstructed from stored values.
- Open provenance/details: grid, period, surface, model-based label (temperature
  is model-based in this config), synthetic/source metadata.

### 6. Export (15–20s)

- Use **Export Markdown/JSON** or **Copy link** to show the report is shareable
  and the URL encodes the selected location/layer.

## If something goes wrong

- **API not reachable / 503:** run `make pipeline` then `make api`; `/api/health`
  should report loaded variables and `synthetic: true`.
- **Blank/broken UI:** reload (error boundary), then check browser console and
  `/api/health`.
- **Need to prove it’s not live-computed:** show that clicking is instant and
  mention `layers/synthetic/*_trend.zarr` and `layers/overlays/synthetic/*` are
  read-only inputs.

## Honest caveats to say out loud

- Synthetic demo data is fake by design; it proves the pipeline, statistics, and
  UX, not Earth science conclusions.
- Real NASA mode is scripted and CMR-verified for dataset IDs/versions/counts,
  but real downloads were **not** run here because Earthdata credentials were
  unavailable.
- NDVI real data is HDF4 and needs conversion before prep; water storage has a
  known mission gap and coarse effective resolution.
- DOIs are TODO until confirmed on dataset landing pages — do not invent them.

## Optional: real-data dry-run (if asked)

```bash
python scripts/run_pipeline.py --real --dry-run
```

Expected (verified 2026-11-13): IMERG 276, MOD13C2 299, M2TMNXSLV 276,
TELLUS_GRAC-GRFO_MASCON_GRID_RL06.3_V4 1 granule. This searches CMR only and
writes nothing.
