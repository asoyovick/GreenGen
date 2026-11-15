import { config } from "../config.js";
import { getExecutionStatus, getExecutionResults, getExecutionSummary, getCellDetails, refreshExecutionStatus, isResultsUnavailable } from "../api/analysis.js";
import { qs, clear, el, getParam, setParams } from "../utils/helpers.js";
import { statusLabel, classificationLabel, formatNumber, formatDateTime } from "../utils/formatting.js";

let map = null, mapLoaded = false, pollTimer = null, pollAbort = null, currentExecutionId = null, chart = null, lastResultsPayload = null;

const CLASS_COLORS = {
  significant_increase: "#b42318",
  significant_decrease: "#1d4ed8",
  no_significant_trend: "#475467",
  insufficient_data: "#b54708",
  inconclusive: "#667085",
};

function setStatus(message, type = "info") {
  const node = qs("#results-status");
  if (!node) return;
  node.className = `notice notice-${type}`;
  node.textContent = message;
}

function renderLegend() {
  const root = qs("#results-legend");
  if (!root) return;
  root.innerHTML = `<strong style="display:block;margin-bottom:0.35rem;">Trend classification</strong>
  <ul class="legend">
    <li class="legend-item"><span class="swatch" style="background:${CLASS_COLORS.significant_increase}"></span> Significant increase</li>
    <li class="legend-item"><span class="swatch" style="background:${CLASS_COLORS.significant_decrease}"></span> Significant decrease</li>
    <li class="legend-item"><span class="swatch" style="background:${CLASS_COLORS.no_significant_trend}"></span> No significant trend detected</li>
    <li class="legend-item"><span class="swatch" style="background:${CLASS_COLORS.insufficient_data}"></span> Insufficient data</li>
    <li class="legend-item"><span class="swatch" style="background:${CLASS_COLORS.inconclusive}"></span> Inconclusive / unavailable</li>
  </ul>
  <p class="field-hint" style="margin:0.4rem 0 0;">Rendered from backend results only; no frontend classification or calculation.</p>`;
}

function initMap() {
  const container = qs("#results-map");
  if (!container || !window.maplibregl) {
    const st = qs("#results-map-status");
    if (st) { st.hidden = false; st.className = "map-overlay map-overlay-status notice notice-warning"; st.textContent = "Map library unavailable."; }
    return;
  }
  try {
    map = new maplibregl.Map({ container, style: config.map.styleUrl, center: config.map.defaultCenter, zoom: config.map.defaultZoom });
    map.addControl(new maplibregl.NavigationControl(), "top-right");
    map.on("load", () => {
      mapLoaded = true;
      const st = qs("#results-map-status"); if (st) st.hidden = true;
      if (lastResultsPayload) tryRenderResultsOnMap(lastResultsPayload);
    });
  } catch (err) {
    const st = qs("#results-map-status"); if (st) { st.hidden = false; st.className = "map-overlay map-overlay-status notice notice-error"; st.textContent = `Map initialization failed: ${err.message}`; }
  }
}

function renderObject(rootSel, obj, emptyMsg) {
  const root = qs(rootSel);
  if (!root) return;
  clear(root);
  if (obj == null) { root.className = "muted"; root.textContent = emptyMsg; return; }
  root.className = "";
  if (typeof obj === "string" || typeof obj === "number" || typeof obj === "boolean") {
    root.textContent = String(obj);
    return;
  }
  const pre = el("pre", { class: "mono", style: "white-space:pre-wrap;overflow:auto;max-height:420px;margin:0;" });
  pre.textContent = JSON.stringify(obj, null, 2);
  root.append(pre);
}

function renderTimeline(ex) {
  const root = qs("#execution-timeline");
  if (!root) return;
  clear(root);
  const st = String(ex?.status || ex?.state || "").toLowerCase();
  const steps = [
    { key: "pending", label: "Pending" },
    { key: "queued", label: "Queued" },
    { key: "running", label: "Running" },
    { key: "completed", label: "Completed" },
  ];
  const order = ["pending", "queued", "running", "completed"];
  const idx = order.indexOf(st);
  const failed = st === "failed";
  const ul = el("ul", { class: "timeline" });
  steps.forEach((s, i) => {
    let cls = "timeline-item";
    if (failed && i === Math.max(idx, 0)) cls += " is-failed";
    else if (idx > i || (st === "completed" && s.key === "completed")) cls += " is-done";
    else if (idx === i) cls += " is-active";
    ul.append(el("li", { class: cls }, [el("span", { class: "timeline-dot", "aria-hidden": "true" }), el("span", { text: s.label })]));
  });
  if (failed) ul.append(el("li", { class: "timeline-item is-failed" }, [el("span", { class: "timeline-dot", "aria-hidden": "true" }), el("span", { text: "Failed" })]));
  root.append(ul);
}

function renderExecutionMeta(ex) {
  const root = qs("#execution-meta");
  if (!root) return;
  clear(root);
  if (!ex) { root.className = "muted"; root.textContent = "No execution loaded."; return; }
  root.className = "";
  const dl = el("dl", { class: "dl" });
  const add = (k, v) => dl.append(el("dt", { text: k }), el("dd", { text: v == null || v === "" ? "—" : (typeof v === "object" ? JSON.stringify(v) : String(v)) }));
  add("Execution ID", ex.id || currentExecutionId);
  add("Investigation", ex.investigation_id || ex.investigationId || "—");
  add("Status", statusLabel(ex.status || ex.state));
  add("Requested", ex.requested_at ? formatDateTime(ex.requested_at) : "—");
  add("Started", ex.started_at ? formatDateTime(ex.started_at) : "—");
  add("Completed", ex.completed_at ? formatDateTime(ex.completed_at) : "—");
  add("Period", (ex.period_start || ex.period?.start) ? `${ex.period_start || ex.period?.start} to ${ex.period_end || ex.period?.end}` : "—");
  if (ex.bounds) add("Bounds", JSON.stringify(ex.bounds));
  if (ex.error_code || ex.error_message) add("Error", [ex.error_code, ex.error_message].filter(Boolean).join(": "));
  root.append(dl);
  renderTimeline(ex);
}

function extractSeries(payload) {
  if (!payload || typeof payload !== "object") return null;
  const candidates = [
    payload.timeseries, payload.time_series, payload.series, payload.observations,
    payload.data?.timeseries, payload.data?.series, payload.result?.timeseries, payload.summary?.timeseries,
  ];
  for (const c of candidates) {
    if (Array.isArray(c) && c.length) return c;
  }
  // cells may contain per-cell series
  const cell = payload.cell || payload;
  const cellSeries = cell.timeseries || cell.time_series || cell.series || cell.observations;
  if (Array.isArray(cellSeries) && cellSeries.length) return cellSeries;
  return null;
}

function renderChart(payload, labelHint = "Value") {
  const state = qs("#results-chart-state");
  const wrap = qs("#results-chart-wrap");
  const meta = qs("#results-chart-meta");
  if (!state || !wrap || !meta) return;
  clear(meta);
  const series = extractSeries(payload);
  if (!series) {
    state.hidden = false; wrap.hidden = true;
    state.className = "chart-empty";
    state.textContent = "No backend-provided time-series data available for this execution/cell.";
    if (chart) { chart.destroy(); chart = null; }
    return;
  }
  if (!window.Chart) {
    state.hidden = false; wrap.hidden = true;
    state.className = "chart-error";
    state.textContent = "Chart library unavailable; cannot render time series.";
    return;
  }
  const labels = series.map((p) => p.year ?? p.time ?? p.date ?? p.t ?? p.period ?? "");
  const values = series.map((p) => p.value ?? p.observation ?? p.anomaly ?? p.y ?? null);
  const trend = series.map((p) => p.trend ?? p.trend_line ?? p.fitted ?? null);
  state.hidden = true; wrap.hidden = false;
  const ctx = qs("#results-chart").getContext("2d");
  if (chart) chart.destroy();
  const datasets = [{ label: payload?.variable || payload?.units || labelHint, data: values, borderColor: "#0f766e", backgroundColor: "rgba(15,118,110,0.15)", tension: 0.15, spanGaps: false }];
  if (trend.some((v) => v != null)) datasets.push({ label: "Trend (backend-provided)", data: trend, borderColor: "#b42318", pointRadius: 0, borderDash: [6,4], tension: 0 });
  chart = new Chart(ctx, { type: "line", data: { labels, datasets }, options: { responsive: true, maintainAspectRatio: false, interaction: { mode: "index", intersect: false }, plugins: { legend: { display: true } }, scales: { x: { title: { display: true, text: "Time" } }, y: { title: { display: true, text: payload?.units || payload?.unit || "Value" } } } } });
  const bits = [];
  if (payload?.units || payload?.unit) bits.push(`Units: ${payload.units || payload.unit}`);
  if (payload?.period) bits.push(`Period: ${Array.isArray(payload.period) ? payload.period.join("–") : JSON.stringify(payload.period)}`);
  if (payload?.provenance?.dataset || payload?.dataset) bits.push(`Dataset: ${payload.provenance?.dataset || payload.dataset}`);
  meta.textContent = bits.join(" • ");
}

function pointToFeature(c, i) {
  const lat = c.lat ?? c.latitude ?? c.y;
  const lon = c.lon ?? c.longitude ?? c.lng ?? c.x;
  if (!Number.isFinite(Number(lat)) || !Number.isFinite(Number(lon))) return null;
  return { type: "Feature", geometry: { type: "Point", coordinates: [Number(lon), Number(lat)] }, properties: { ...c, _idx: i } };
}

function extractGeoJSON(resultPayload) {
  if (!resultPayload || typeof resultPayload !== "object") return null;
  if (resultPayload.type === "FeatureCollection" && Array.isArray(resultPayload.features)) return resultPayload;
  const candidates = [resultPayload.geojson, resultPayload.grid, resultPayload.features, resultPayload.results?.geojson, resultPayload.result?.geojson, resultPayload.data?.geojson];
  for (const c of candidates) {
    if (c && c.type === "FeatureCollection" && Array.isArray(c.features)) return c;
  }
  const cells = Array.isArray(resultPayload.cells) ? resultPayload.cells : (Array.isArray(resultPayload.results?.cells) ? resultPayload.results.cells : (Array.isArray(resultPayload.data?.cells) ? resultPayload.data.cells : null));
  if (cells && cells.length) {
    if (cells[0] && (cells[0].geometry || cells[0].geom)) {
      const features = cells.map((c, i) => ({ type: "Feature", geometry: c.geometry || c.geom, properties: { ...c, _idx: i } })).filter(f => f.geometry);
      if (features.length) return { type: "FeatureCollection", features };
    }
    const pointFeatures = cells.map(pointToFeature).filter(Boolean);
    if (pointFeatures.length) return { type: "FeatureCollection", features: pointFeatures };
  }
  return null;
}

function fitToGeoJSON(geojson) {
  if (!map || !geojson?.features?.length) return;
  let minX=180,minY=90,maxX=-180,maxY=-90, found=false;
  const scan = (coords) => {
    if (!Array.isArray(coords)) return;
    if (typeof coords[0] === "number" && typeof coords[1] === "number") {
      const [x,y]=coords; if (!Number.isFinite(x)||!Number.isFinite(y)) return;
      minX=Math.min(minX,x); minY=Math.min(minY,y); maxX=Math.max(maxX,x); maxY=Math.max(maxY,y); found=true; return;
    }
    coords.forEach(scan);
  };
  geojson.features.forEach(f => scan(f.geometry?.coordinates));
  if (found) { try { map.fitBounds([[minX,minY],[maxX,maxY]], { padding: 20, maxZoom: 10, duration: 0 }); } catch {} }
}

function renderCellProperties(props) {
  const root = qs("#cell-details");
  if (!root) return;
  clear(root); root.className = "";
  const dl = el("dl", { class: "dl" });
  const add = (k, v) => dl.append(el("dt", { text: k }), el("dd", { text: v == null || v === "" ? "—" : String(v) }));
  add("Cell ID", props.cell_id || props.id || "—");
  add("Classification", classificationLabel(props.classification || props.class || props.trend_class));
  add("Trend direction", props.trend_direction || props.direction || "—");
  const slope = props.sens_slope ?? props.slope;
  if (slope && typeof slope === "object") add("Trend magnitude", `${formatNumber(slope.value)} ${slope.units || ""}${slope.ci_lower != null ? ` (CI [${formatNumber(slope.ci_lower)}, ${formatNumber(slope.ci_upper)}])` : ""}`.trim());
  else add("Trend magnitude", slope != null ? String(slope) : "—");
  const mk = props.mann_kendall || {};
  add("P-value", props.p_value != null ? formatNumber(props.p_value) : (mk.p_value != null ? formatNumber(mk.p_value) : "—"));
  add("Significant", props.significant != null ? String(props.significant) : "—");
  add("Completeness", props.completeness != null ? formatNumber(props.completeness) : "—");
  add("Observations", props.n_observations ?? props.observation_count ?? "—");
  if (props.flags) add("Flags/quality", Array.isArray(props.flags) ? props.flags.join(", ") : String(props.flags));
  if (props.units) add("Units", props.units);
  root.append(dl);
  if (extractSeries(props)) renderChart(props, props.variable || "Cell series");
}

function tryRenderResultsOnMap(resultResponse) {
  const payload = resultResponse?.result || resultResponse?.results || resultResponse;
  lastResultsPayload = resultResponse;
  if (!map || !mapLoaded) return;
  const geojson = extractGeoJSON(payload);
  const mode = qs("#results-map-mode");
  const st = qs("#results-map-status");
  try {
    if (map.getLayer("results-fill")) map.removeLayer("results-fill");
    if (map.getLayer("results-circle")) map.removeLayer("results-circle");
    if (map.getLayer("results-line")) map.removeLayer("results-line");
    if (map.getSource("results")) map.removeSource("results");
  } catch {}

  if (!geojson || !geojson.features?.length) {
    if (mode) { mode.textContent = "No mappable grid data"; mode.className = "badge badge-unavailable"; }
    if (st) { st.hidden = false; st.className = "map-overlay map-overlay-status notice notice-warning"; st.textContent = "Results are available but no recognized grid geometry (GeoJSON/cells with geometry or lat/lon) was returned. Map rendering awaits the agreed result format."; }
    return;
  }

  try {
    map.addSource("results", { type: "geojson", data: geojson });
    const geomType = geojson.features[0]?.geometry?.type;
    if (geomType === "Point" || geomType === "MultiPoint") {
      map.addLayer({ id: "results-circle", type: "circle", source: "results", paint: {
        "circle-radius": 5,
        "circle-color": ["match", ["get", "classification"], "significant_increase", CLASS_COLORS.significant_increase, "significant_decrease", CLASS_COLORS.significant_decrease, "no_significant_trend", CLASS_COLORS.no_significant_trend, "insufficient_data", CLASS_COLORS.insufficient_data, "inconclusive", CLASS_COLORS.inconclusive, "#94a3b8"],
        "circle-stroke-color": "#ffffff", "circle-stroke-width": 1, "circle-opacity": 0.8,
      }});
      map.on("click", "results-circle", onFeatureClick);
    } else {
      map.addLayer({ id: "results-fill", type: "fill", source: "results", paint: {
        "fill-color": ["match", ["get", "classification"], "significant_increase", CLASS_COLORS.significant_increase, "significant_decrease", CLASS_COLORS.significant_decrease, "no_significant_trend", CLASS_COLORS.no_significant_trend, "insufficient_data", CLASS_COLORS.insufficient_data, "inconclusive", CLASS_COLORS.inconclusive, "#94a3b8"],
        "fill-opacity": 0.55,
      }});
      map.addLayer({ id: "results-line", type: "line", source: "results", paint: { "line-color": "#ffffff", "line-width": 0.5, "line-opacity": 0.6 } });
      map.on("click", "results-fill", onFeatureClick);
    }
    if (mode) { mode.textContent = "Results rendered"; mode.className = "badge badge-available"; }
    if (st) st.hidden = true;
    fitToGeoJSON(geojson);
  } catch (err) {
    if (mode) { mode.textContent = "Map render error"; mode.className = "badge badge-unavailable"; }
    if (st) { st.hidden = false; st.className = "map-overlay map-overlay-status notice notice-warning"; st.textContent = `Could not render returned results: ${err.message}`; }
  }
}

async function onFeatureClick(e) {
  const props = e.features?.[0]?.properties || {};
  const cellId = props.cell_id || props.id;
  if (cellId) { const input = qs("#cell-id"); if (input) input.value = String(cellId); }
  // Try to fetch authoritative cell details from backend if possible
  if (currentExecutionId && cellId) {
    try {
      const res = await getCellDetails(currentExecutionId, String(cellId));
      const cell = res?.cell || res?.result || res;
      renderObject("#cell-details", cell, "No cell details returned.");
      if (cell && typeof cell === "object") renderChart(cell, cell.variable || "Cell series");
      return;
    } catch (_) { /* fall back to feature properties */ }
  }
  renderCellProperties(props);
}

async function loadSummary(id) {
  try {
    const sum = await getExecutionSummary(id);
    renderObject("#results-summary", sum?.summary || sum, "No summary available.");
    if (extractSeries(sum?.summary || sum)) renderChart(sum?.summary || sum, "Summary series");
  } catch (err) {
    const msg = isResultsUnavailable(err) ? (err?.data?.error?.message || "Summary unavailable for this execution.") : `Summary unavailable: ${err.message}`;
    renderObject("#results-summary", msg, msg);
  }
}

async function loadResults(id) {
  try {
    const res = await getExecutionResults(id);
    const payload = res?.result || res?.results || res;
    renderObject("#results-data", payload, "No results available.");
    tryRenderResultsOnMap(res);
    if (extractSeries(payload)) renderChart(payload, payload?.variable || "Results series");
    // provenance/status hints
    if (res?.provenance && qs("#results-summary")) {
      // keep summary as-is; provenance included in payload display
    }
  } catch (err) {
    const msg = isResultsUnavailable(err) ? (err?.data?.error?.message || "No verified results available for this execution.") : `Results unavailable: ${err.message}`;
    renderObject("#results-data", msg, msg);
    const mode = qs("#results-map-mode"); if (mode) { mode.textContent = "Results unavailable"; mode.className = "badge badge-unavailable"; }
  }
}

async function loadCell(id, cellId) {
  if (!cellId) return;
  try {
    const res = await getCellDetails(id, cellId);
    const cell = res?.cell || res?.result || res;
    renderObject("#cell-details", cell, "No cell details returned.");
    if (cell && typeof cell === "object") renderChart(cell, cell.variable || "Cell series");
  } catch (err) {
    const msg = isResultsUnavailable(err) ? (err?.data?.error?.message || "Cell results unavailable.") : `Cell details unavailable: ${err.message}`;
    renderObject("#cell-details", msg, msg);
  }
}

function stopPolling() {
  if (pollTimer) clearInterval(pollTimer);
  pollTimer = null;
  if (pollAbort) pollAbort.abort();
  pollAbort = null;
}

async function loadExecution(id, doRefresh = false) {
  if (!id) { setStatus("Enter an execution ID.", "warning"); return; }
  currentExecutionId = id;
  setParams({ execution: id });
  const reportLink = qs("#report-link"); if (reportLink) reportLink.href = `./reports.html?execution=${encodeURIComponent(id)}`;
  setStatus("Loading execution status…", "info");
  try {
    const res = doRefresh ? await refreshExecutionStatus(id) : await getExecutionStatus(id);
    const ex = res?.execution || res;
    renderExecutionMeta(ex);
    const st = String(ex?.status || ex?.state || "").toLowerCase();
    setStatus(`Execution ${id}: ${statusLabel(st)}${ex?.error_message ? ` — ${ex.error_message}` : (res?.message ? ` — ${res.message}` : "")}`, st === "failed" ? "error" : st === "completed" ? "success" : "info");
    if (st === "completed") {
      stopPolling();
      await Promise.all([loadSummary(id), loadResults(id)]);
    } else if (st === "failed") {
      stopPolling();
      renderObject("#results-summary", ex?.error_message || "Execution failed. No scientific results are available.", "");
      renderObject("#results-data", null, "No results available.");
    } else {
      renderObject("#results-summary", "Summary will be available after verified completion.", "");
      renderObject("#results-data", "Results will be available after verified completion.", "");
    }
  } catch (err) {
    if (err?.code === "ABORTED") return;
    stopPolling();
    setStatus(`Unable to load execution: ${err.message}`, "error");
  }
}

function startPolling(id) {
  stopPolling();
  pollAbort = new AbortController();
  pollTimer = setInterval(async () => {
    try { await loadExecution(id, true); } catch {}
  }, config.pollIntervalMs);
}

document.addEventListener("DOMContentLoaded", async () => {
  renderLegend();
  initMap();
  const input = qs("#execution-id");
  const id = getParam("execution") || getParam("id");
  if (id && input) input.value = id;

  qs("#load-execution")?.addEventListener("click", async () => {
    const val = (qs("#execution-id")?.value || "").trim();
    if (!val) { setStatus("Enter an execution ID.", "warning"); return; }
    stopPolling();
    await loadExecution(val, false);
    startPolling(val);
  });
  qs("#refresh-execution")?.addEventListener("click", async () => {
    const val = (qs("#execution-id")?.value || currentExecutionId || "").trim();
    if (!val) { setStatus("Enter an execution ID.", "warning"); return; }
    await loadExecution(val, true);
  });
  qs("#load-cell")?.addEventListener("click", async () => {
    const exId = (qs("#execution-id")?.value || currentExecutionId || "").trim();
    const cellId = (qs("#cell-id")?.value || "").trim();
    if (!exId) { setStatus("Load an execution before requesting a cell.", "warning"); return; }
    if (!cellId) { setStatus("Enter a cell ID.", "warning"); return; }
    await loadCell(exId, cellId);
  });

  if (id) {
    await loadExecution(id, false);
    startPolling(id);
  }
});
