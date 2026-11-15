import { config } from "../config.js";
import { getApiHealth, listInvestigations } from "../api/investigations.js";
import { getLayers, getPointReport, getPointTimeseries, getVariables, validateExecution, submitExecution, getExecutionStatus, getExecutionSummary, refreshExecutionStatus } from "../api/analysis.js";
import { isEndpointMissing, isResultsUnavailable } from "../api/analysis.js";
import { qs, clear, el, getParam } from "../utils/helpers.js";
import { formatNumber, classificationLabel, statusLabel } from "../utils/formatting.js";
import { validateDateRange, summarizeErrors } from "../utils/validation.js";

let map, mapReady = false, selected = null, chart = null, pollTimer = null, pollAbort = null;

function setStatus(msg, type = "info") {
  const box = qs("#execution-status");
  if (!box) return;
  box.className = `notice notice-${type}`;
  box.textContent = msg;
}

function renderLegend() {
  const legend = qs("#map-legend");
  if (!legend) return;
  legend.innerHTML = `<strong style="display:block;margin-bottom:0.35rem;">Trend classification</strong>
  <ul class="legend">
    <li class="legend-item"><span class="swatch" style="background:var(--trend-increase)"></span> Significant increase</li>
    <li class="legend-item"><span class="swatch" style="background:var(--trend-decrease)"></span> Significant decrease</li>
    <li class="legend-item"><span class="swatch" style="background:var(--trend-nonsignificant)"></span> No significant trend detected</li>
    <li class="legend-item"><span class="swatch" style="background:var(--trend-insufficient)"></span> Insufficient data</li>
    <li class="legend-item"><span class="swatch" style="background:var(--trend-unavailable)"></span> Inconclusive / unavailable</li>
  </ul>
  <p class="field-hint" style="margin:0.4rem 0 0;">Classifications shown as returned by backend/scientific results. No frontend statistical calculation.</p>`;
}

async function initMap() {
  const elMap = qs("#map");
  if (!elMap || !window.maplibregl) {
    const ms = qs("#map-status"); if (ms) { ms.hidden = false; ms.className = "map-overlay map-overlay-status notice notice-warning"; ms.textContent = "Map library unavailable. Load MapLibre GL JS to enable interactive mapping."; }
    return;
  }
  try {
    map = new maplibregl.Map({
      container: elMap,
      style: config.map.styleUrl,
      center: config.map.defaultCenter,
      zoom: config.map.defaultZoom,
      attributionControl: true,
    });
    map.addControl(new maplibregl.NavigationControl(), "top-right");
    map.on("load", () => {
      mapReady = true;
      qs("#map-mode").textContent = "Interactive map ready";
      qs("#map-mode").className = "badge badge-available";
      // Try to load prototype overlay layers metadata if present (read-only precomputed view)
      loadPrototypeLayers().catch(() => {});
    });
    map.on("click", (e) => onMapClick(e.lngLat.lat, e.lngLat.lng));
    map.on("error", () => {
      const ms = qs("#map-status"); if (ms) { ms.hidden = false; ms.className = "map-overlay map-overlay-status notice notice-warning"; ms.textContent = "Map style or tiles could not be fully loaded. Check network/style configuration."; }
    });
  } catch (err) {
    const ms = qs("#map-status"); if (ms) { ms.hidden = false; ms.className = "map-overlay map-overlay-status notice notice-error"; ms.textContent = `Map initialization failed: ${err.message}`; }
  }
}

async function loadPrototypeLayers() {
  try {
    const layers = await getLayers();
    const meta = layers?.layers || layers?.overlays || layers;
    if (meta && qs("#map-mode")) {
      qs("#map-mode").textContent = "Precomputed layers available";
    }
    // If a raster/image overlay URL is provided by prototype, show as source when compatible.
    // (Execution-based grid GeoJSON results will be rendered when /executions results are available.)
    return meta;
  } catch { return null; }
}

function selectedVar() {
  const sel = qs("#investigation-select");
  return sel?.value || "";
}

function normInvestigation(inv = {}) {
  const availability = inv.availability || inv.availability_status || inv.status || "";
  const coverage = inv.coverage || {
    spatial: inv.supported_geographical_coverage || inv.spatial,
    temporal: inv.supported_temporal_coverage || inv.temporal || inv.period,
  };
  return {
    ...inv,
    id: inv.id || inv.investigation_id || inv.key,
    title: inv.title || inv.name || inv.display_name || inv.id,
    question: inv.question || inv.scientific_question,
    availability,
    coverage,
    variables: inv.variables || (inv.scientific_variable ? [inv.scientific_variable] : (inv.variable ? [inv.variable] : [])),
    dataset: inv.dataset || (inv.dataset_name ? { name: inv.dataset_name } : null),
  };
}

async function populateInvestigations() {
  const sel = qs("#investigation-select");
  if (!sel) return;
  try {
    const data = await listInvestigations();
    const items = (Array.isArray(data) ? data : (data?.investigations || [])).map(normInvestigation).filter(i => i && i.id);
    clear(sel);
    sel.appendChild(el("option", { value: "", text: "Select an investigation/variable" }));
    if (!items.length) {
      sel.appendChild(el("option", { value: "", disabled: true, text: "No investigations available from backend" }));
      return;
    }
    items.forEach((inv) => {
      const availability = String(inv.availability || "").toLowerCase();
      const available = ["available", "implemented", "active", "available_precomputed"].includes(availability);
      const opt = el("option", { value: inv.id, text: `${inv.title}${available ? "" : ` (${availability || "unavailable"})`}` });
      if (inv.variables?.[0]) opt.dataset.variable = inv.variables[0];
      if (inv.coverage?.temporal) opt.dataset.period = JSON.stringify(inv.coverage.temporal);
      if (inv.coverage?.spatial) opt.dataset.spatial = JSON.stringify(inv.coverage.spatial);
      opt.dataset.availability = availability;
      sel.appendChild(opt);
    });
    const wanted = getParam("investigation");
    if (wanted) sel.value = wanted;
    qs("#period-hint").textContent = data?.note ? String(data.note) : "Select a valid historical period within supported dataset coverage.";
    updateSelectionHints();
  } catch (err) {
    clear(sel);
    sel.appendChild(el("option", { value: "", text: "Unable to load options (backend unavailable)" }));
    qs("#variable-hint").textContent = `Could not load backend capabilities: ${err.message}`;
  }
}

function updateSelectionHints() {
  const sel = qs("#investigation-select");
  const opt = sel?.selectedOptions?.[0];
  if (!opt || !opt.value) return;
  const availability = opt.dataset.availability || "";
  const hint = qs("#variable-hint");
  if (hint) hint.textContent = ["available","implemented","active","available_precomputed"].includes(availability)
    ? "This option is available per backend/prototype metadata. Results are shown only when provided by backend services."
    : "This investigation is not available for execution. You can review details, but submission will be rejected by the backend.";
  if (opt.dataset.period && qs("#period-hint")) {
    try {
      const p = JSON.parse(opt.dataset.period);
      const txt = Array.isArray(p) ? p.join(" to ") : (typeof p === "string" ? p : JSON.stringify(p));
      qs("#period-hint").textContent = `Coverage hint: ${txt}. Dates must be valid and within supported coverage.`;
    } catch {}
  }
}

function updateCellPanel(payload) {
  const root = qs("#cell-content");
  if (!root) return;
  if (!payload) { root.className = "muted"; root.textContent = "No grid cell selected."; return; }
  root.className = "";
  const dl = el("dl", { class: "dl" });
  const add = (k, v) => { dl.append(el("dt", { text: k }), el("dd", { text: v == null || v === "" ? "—" : String(v) })); };
  const c = payload.cell || payload.location || payload;
  add("Grid/cell identifier", c.cell_id || c.id || "Not provided");
  add("Coordinates", (c.lat != null && c.lon != null) ? `${formatNumber(c.lat, {digits:4})}, ${formatNumber(c.lon, {digits:4})}` : "—");
  add("Variable", payload.variable || payload.variable_key || selectedVar() || "—");
  add("Trend direction", c.trend_direction || c.direction || "—");
  add("Trend magnitude", c.sens_slope?.value != null ? `${formatNumber(c.sens_slope.value)} ${c.sens_slope.units || ""}`.trim() : (c.slope != null ? String(c.slope) : "—"));
  add("Statistical significance", c.significant != null ? String(c.significant) : (c.p_value != null ? `p=${formatNumber(c.p_value)}` : "—"));
  add("P-value", c.p_value != null ? formatNumber(c.p_value) : (c.mann_kendall?.p_value != null ? formatNumber(c.mann_kendall.p_value) : "—"));
  add("Confidence interval", c.sens_slope?.ci_lower != null ? `[${formatNumber(c.sens_slope.ci_lower)}, ${formatNumber(c.sens_slope.ci_upper)}] ${c.sens_slope.units || ""}`.trim() : "—");
  add("Data completeness", c.completeness != null ? formatNumber(c.completeness) : "—");
  add("Classification", classificationLabel(c.classification || c.class || c.verdict));
  if (c.flags?.length) add("Flags/uncertainty", c.flags.join(", "));
  clear(root); root.append(dl);
}

async function renderTimeseries(lat, lon, variable) {
  const state = qs("#chart-state");
  const wrap = qs("#chart-wrap");
  const meta = qs("#chart-meta");
  if (!variable) { state.hidden = false; wrap.hidden = true; state.textContent = "Select an available variable to load time-series data."; return; }
  state.hidden = false; wrap.hidden = true; state.innerHTML = '<span class="spinner"></span> Loading time-series data…'; clear(meta);
  try {
    const ts = await getPointTimeseries(lat, lon, variable);
    const series = ts?.series || ts?.timeseries || ts?.annual || ts?.data || [];
    if (!Array.isArray(series) || !series.length) {
      state.textContent = "No time-series data returned for this selection.";
      return;
    }
    const labels = series.map((p) => p.year || p.time || p.date || p.t);
    const values = series.map((p) => p.value ?? p.anomaly ?? p.observation ?? p.y);
    const trend = series.map((p) => p.trend ?? p.trend_line ?? null);
    state.hidden = true; wrap.hidden = false;
    if (!window.Chart) { state.hidden = false; wrap.hidden = true; state.textContent = "Chart library unavailable."; return; }
    const ctx = qs("#timeseries-chart").getContext("2d");
    if (chart) chart.destroy();
    const datasets = [{ label: ts.variable || variable, data: values, borderColor: "#0f766e", backgroundColor: "rgba(15,118,110,0.15)", tension: 0.15, spanGaps: false }];
    if (trend.some((v) => v != null)) datasets.push({ label: "Trend (backend-provided)", data: trend, borderColor: "#b42318", pointRadius: 0, borderDash: [6,4], tension: 0 });
    chart = new Chart(ctx, { type: "line", data: { labels, datasets }, options: { responsive: true, maintainAspectRatio: false, interaction: { mode: "index", intersect: false }, plugins: { legend: { display: true } }, scales: { x: { title: { display: true, text: "Time" } }, y: { title: { display: true, text: ts.units || ts.unit || "Value" } } } } });
    if (ts?.synthetic) {
      state.hidden = false; wrap.hidden = true;
      state.textContent = "Synthetic data is not used. No time-series data available.";
      return;
    }
    meta.textContent = [ts.units ? `Units: ${ts.units}` : null, ts.period ? `Period: ${Array.isArray(ts.period)?ts.period.join("–"):ts.period}` : null, ts.note || null].filter(Boolean).join(" • ");
  } catch (err) {
    state.hidden = false; wrap.hidden = true;
    state.className = "chart-error";
    state.textContent = `Time-series unavailable: ${err.message}`;
  }
}

async function onMapClick(lat, lon) {
  selected = { lat, lon };
  qs("#selection-info").textContent = `Selected location: ${formatNumber(lat,{digits:4})}, ${formatNumber(lon,{digits:4})}. Querying backend results…`;
  const variable = selectedVar();
  updateCellPanel({ location: { lat, lon }, variable });
  try {
    const report = await getPointReport(lat, lon, 5);
    // Normalize prototype report shape if present
    const cell = report?.cell || report?.location || report?.result || report;
    updateCellPanel({ cell, variable: report?.variable || variable, raw: report });
    if (variable || report?.variable) await renderTimeseries(lat, lon, variable || report?.variable);
    qs("#selection-info").textContent = `Selected location: ${formatNumber(lat,{digits:4})}, ${formatNumber(lon,{digits:4})}. Showing backend-returned results where available.`;
  } catch (err) {
    qs("#selection-info").textContent = `Selected location: ${formatNumber(lat,{digits:4})}, ${formatNumber(lon,{digits:4})}. No backend report available (${err.message}).`;
  }
}

async function startPolling(executionId) {
  stopPolling();
  pollAbort = new AbortController();
  const tick = async () => {
    try {
      const res = await getExecutionStatus(executionId, { signal: pollAbort.signal });
      const ex = res?.execution || res;
      const s = ex?.status || ex?.state;
      setStatus(`Execution ${executionId}: ${statusLabel(s)}${ex?.error_message ? ` — ${ex.error_message}` : (res?.message ? ` — ${res.message}` : "")}`, s === "failed" ? "error" : s === "completed" ? "success" : "info");
      const meta = qs("#execution-meta"); clear(meta);
      [["Execution ID", executionId], ["Status", statusLabel(s)], ["Updated", ex?.updated_at || ex?.requested_at || "—"], ex?.error_code ? ["Code", ex.error_code] : null].filter(Boolean).forEach(([k,v]) => { meta.append(el("dt",{text:k}), el("dd",{text:String(v??"—")})); });
      if (["completed", "failed"].includes(s)) { stopPolling(); if (s === "completed") loadExecutionResults(executionId); }
      else if (s === "queued" || s === "running") {
        // best-effort draft refresh (backend endpoint may sync engine status)
        refreshExecutionStatus(executionId, { signal: pollAbort.signal }).catch(() => {});
      }
    } catch (err) {
      if (err?.name === "AbortError" || err?.code === "ABORTED") return;
      setStatus(`Status check failed: ${err.message}`, "error");
      stopPolling();
    }
  };
  await tick();
  pollTimer = setInterval(tick, config.pollIntervalMs);
}
function stopPolling() { if (pollTimer) clearInterval(pollTimer); pollTimer = null; if (pollAbort) pollAbort.abort(); pollAbort = null; }

async function loadExecutionResults(executionId) {
  try {
    const summary = await getExecutionSummary(executionId);
    const meta = qs("#execution-meta");
    if (summary && meta) {
      meta.append(el("dt",{text:"Summary"}), el("dd",{text: typeof summary === "string" ? summary : JSON.stringify(summary)}));
    }
  } catch (err) {
    const meta = qs("#execution-meta");
    if (meta) {
      const msg = isResultsUnavailable(err) ? (err?.data?.error?.message || "No verified summary/results available.") : `Summary unavailable: ${err.message}`;
      meta.append(el("dt",{text:"Results"}), el("dd",{text: msg}));
    }
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  renderLegend();
  await initMap();
  await populateInvestigations();
  try {
    const vars = await getVariables();
    const period = vars?.period || vars?.variables?.[0]?.period;
    if (period) qs("#period-hint").textContent = `Supported/available period (prototype): ${Array.isArray(period)?period.join(" to "):JSON.stringify(period)}. Validate against dataset coverage before submission.`;
  } catch {}

  qs("#clear-btn")?.addEventListener("click", () => {
    selected = null;
    qs("#selection-info").textContent = "Selection cleared.";
    updateCellPanel(null);
    if (chart) { chart.destroy(); chart = null; }
    qs("#chart-wrap").hidden = true; qs("#chart-state").hidden = false; qs("#chart-state").textContent = "Select a location and variable to view time-series data from the backend.";
    setStatus("Ready. Configure and submit an investigation, or inspect precomputed results if available.", "info");
  });

  qs("#investigation-select")?.addEventListener("change", updateSelectionHints);

  qs("#explore-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const form = e.currentTarget;
    const errorsEl = qs("#form-errors"); if (errorsEl) errorsEl.textContent = "";
    const investigation = form.investigation.value;
    const start = form.start.value;
    const end = form.end.value;
    const { valid, errors } = validateDateRange(start, end);
    if (!investigation) errors.unshift({ field: "investigation", message: "Select an investigation." });
    if (!valid || errors.length) { if (errorsEl) errorsEl.textContent = summarizeErrors(errors); return; }

    // Backend contract expects bbox bounds {min_lon,min_lat,max_lon,max_lat}.
    // Use selected point (small bbox) or Kenya default focus; do not claim unsupported coverage.
    const kenyaBounds = { min_lon: 33.9, min_lat: -4.7, max_lon: 41.9, max_lat: 5.5 };
    let bounds = kenyaBounds;
    if (selected && typeof selected.lat === "number" && typeof selected.lon === "number") {
      const d = 0.05;
      bounds = {
        min_lon: Math.max(-180, Number((selected.lon - d).toFixed(6))),
        min_lat: Math.max(-90, Number((selected.lat - d).toFixed(6))),
        max_lon: Math.min(180, Number((selected.lon + d).toFixed(6))),
        max_lat: Math.min(90, Number((selected.lat + d).toFixed(6))),
      };
    } else if (form.region.value === "custom") {
      if (errorsEl) errorsEl.textContent = "Select a point on the map for a custom area, or choose a supported region.";
      return;
    }
    const payload = {
      investigation_id: investigation,
      bounds,
      period: { start, end },
    };

    setStatus("Validating investigation request…", "info");
    const runBtn = qs("#run-btn");
    if (runBtn) runBtn.disabled = true;
    try {
      try {
        const v = await validateExecution(payload);
        if (v && v.valid === false) {
          const issues = v.issues || v.error?.details || [];
          const msg = Array.isArray(issues) && issues.length
            ? issues.map(i => `${i.field || "field"}: ${i.issue || i.message || "invalid"}`).join("; ")
            : (v.error?.message || "Validation failed.");
          if (errorsEl) errorsEl.textContent = msg;
          setStatus(`Request not valid: ${msg}`, "warning");
          return;
        }
      } catch (verr) {
        if (isEndpointMissing(verr)) {
          // validation endpoint unavailable; continue and let submit report issues
        } else if (verr?.status === 422 || verr?.status === 400) {
          const details = verr?.data?.issues || verr?.data?.error?.details || verr?.details || [];
          const msg = Array.isArray(details) && details.length
            ? details.map(i => `${i.field || "field"}: ${i.issue || i.message || "invalid"}`).join("; ")
            : verr.message;
          if (errorsEl) errorsEl.textContent = msg;
          setStatus(`Request not valid: ${msg}`, "warning");
          return;
        } else {
          throw verr;
        }
      }

      setStatus("Submitting investigation to backend…", "info");
      const res = await submitExecution(payload);
      const executionId = res?.execution_id || res?.id || res?.execution?.id;
      if (!executionId) {
        const msg = res?.error?.message || res?.message || "Backend did not return an execution identifier.";
        throw new Error(msg);
      }
      const ex = res?.execution || {};
      const st = ex.status || res.status;
      setStatus(`Execution ${executionId}: ${statusLabel(st)}${res.message ? ` — ${res.message}` : ""}`, st === "failed" ? "error" : "info");
      const meta = qs("#execution-meta"); clear(meta);
      [["Execution ID", executionId], ["Status", statusLabel(st)], ex.error_code ? ["Code", ex.error_code] : null, ex.error_message ? ["Message", ex.error_message] : null].filter(Boolean).forEach(([k,v]) => { meta.append(el("dt",{text:k}), el("dd",{text:String(v??"—")})); });
      const link = el("a", { href: `./results.html?execution=${encodeURIComponent(executionId)}`, text: "Open results view", class: "btn btn-secondary", style: "margin-top:0.5rem;display:inline-block;" });
      meta.append(el("dt",{text:"Results"}), el("dd",{},[link]));
      if (st && !["failed","completed"].includes(st)) startPolling(executionId);
      if (st === "completed") loadExecutionResults(executionId);
    } catch (err) {
      if (isEndpointMissing(err)) {
        setStatus("Execution API is not available on the connected backend. This frontend cannot simulate analysis; connect the Go backend execution endpoints or use available precomputed prototype views.", "warning");
      } else {
        const details = err?.data?.issues || err?.data?.error?.details || err?.details;
        const detailText = Array.isArray(details) && details.length ? ` (${details.map(d=>`${d.field||'field'}: ${d.issue||d.message||''}`).join('; ')})` : "";
        setStatus(`Submission failed: ${err.message}${detailText}`, "error");
        if (errorsEl && Array.isArray(details) && details.length) errorsEl.textContent = details.map(d=>`${d.field||'field'}: ${d.issue||d.message||''}`).join("; ");
      }
    } finally {
      if (runBtn) runBtn.disabled = false;
    }
  });
});
