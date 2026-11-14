import { config } from "../config.js";
import { getApiHealth, listInvestigations } from "../api/investigations.js";
import { getLayers, getPointReport, getPointTimeseries, getVariables, submitExecution, getExecutionStatus, getExecutionSummary } from "../api/analysis.js";
import { isEndpointMissing } from "../api/analysis.js";
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

async function populateInvestigations() {
  const sel = qs("#investigation-select");
  if (!sel) return;
  try {
    const data = await listInvestigations();
    const items = Array.isArray(data) ? data : (data?.investigations || []);
    clear(sel);
    sel.appendChild(el("option", { value: "", text: "Select an available variable/investigation" }));
    if (!items.length) {
      sel.appendChild(el("option", { value: "", disabled: true, text: "No investigations available from backend" }));
      return;
    }
    items.forEach((inv) => {
      const id = inv.id || inv.key || inv.title;
      const label = inv.title || inv.display_name || id;
      const available = ["available", "implemented", "active", "available_precomputed"].includes(String(inv.availability || inv.status || "").toLowerCase());
      const opt = el("option", { value: id, text: `${label}${available ? "" : " (unavailable/planned)"}` });
      if (inv.variables?.[0]) opt.dataset.variable = inv.variables[0];
      if (inv.coverage?.temporal || inv.period) opt.dataset.period = JSON.stringify(inv.coverage?.temporal || inv.period);
      sel.appendChild(opt);
    });
    const wanted = getParam("investigation");
    if (wanted) sel.value = wanted;
    qs("#period-hint").textContent = data?.note ? `${qs("#period-hint").textContent} ${data.note}` : qs("#period-hint").textContent;
  } catch (err) {
    clear(sel);
    sel.appendChild(el("option", { value: "", text: "Unable to load options (backend unavailable)" }));
    qs("#variable-hint").textContent = `Could not load backend capabilities: ${err.message}`;
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
    meta.textContent = [ts.units ? `Units: ${ts.units}` : null, ts.period ? `Period: ${Array.isArray(ts.period)?ts.period.join("–"):ts.period}` : null, ts.note || ts.synthetic ? "Prototype/precomputed data where indicated." : null].filter(Boolean).join(" • ");
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
      const st = await getExecutionStatus(executionId, { signal: pollAbort.signal });
      const s = st?.status || st?.state;
      setStatus(`Execution ${executionId}: ${statusLabel(s)}${st?.message ? ` — ${st.message}` : ""}`, s === "failed" ? "error" : s === "completed" ? "success" : "info");
      const meta = qs("#execution-meta"); clear(meta);
      [["Execution ID", executionId], ["Status", statusLabel(s)], ["Updated", st?.updated_at || st?.timestamp || "—"]].forEach(([k,v]) => { meta.append(el("dt",{text:k}), el("dd",{text:String(v??"—")})); });
      if (["completed", "failed"].includes(s)) { stopPolling(); if (s === "completed") loadExecutionResults(executionId); }
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
  } catch { /* summary optional */ }
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

  qs("#explore-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const form = e.currentTarget;
    const errorsEl = qs("#form-errors"); clear(errorsEl);
    const investigation = form.investigation.value;
    const start = form.start.value;
    const end = form.end.value;
    const { valid, errors } = validateDateRange(start, end);
    if (!investigation) errors.unshift({ field: "investigation", message: "Select an available investigation/variable." });
    if (!valid || errors.length) { errorsEl.textContent = summarizeErrors(errors); return; }
    const payload = {
      investigation_id: investigation,
      bounds: selected ? { type: "point", lat: selected.lat, lon: selected.lon } : { type: "region", id: form.region.value || "kenya" },
      period: { start, end },
    };
    setStatus("Submitting investigation to backend…", "info");
    qs("#run-btn").disabled = true;
    try {
      const res = await submitExecution(payload);
      const executionId = res?.execution_id || res?.id;
      if (!executionId) throw new Error("Backend did not return an execution identifier.");
      setStatus(`Execution submitted: ${executionId}. Tracking status…`, "info");
      startPolling(executionId);
    } catch (err) {
      if (isEndpointMissing(err)) {
        setStatus("Execution API is not available on the connected backend. This frontend cannot simulate analysis; connect the Go backend execution endpoints or use available precomputed prototype views.", "warning");
      } else {
        setStatus(`Submission failed: ${err.message}`, "error");
      }
    } finally {
      qs("#run-btn").disabled = false;
    }
  });
});
