import { config } from "../config.js";
import { getInvestigation } from "../api/investigations.js";
import { validateExecution, submitExecution, isEndpointMissing } from "../api/analysis.js";
import { normalizeInvestigation, isExecutable, coverageText } from "../features/investigations/normalize.js";
import { qs, clear, el, getParam, setParams } from "../utils/helpers.js";
import { validateDateRange, summarizeErrors } from "../utils/validation.js";
import { formatNumber, statusLabel } from "../utils/formatting.js";

let map = null;
let marker = null;
let selection = null; // { type:'point'|'preset', lat, lon, bounds }

const KENYA_BOUNDS = { min_lon: 33.9, min_lat: -4.7, max_lon: 41.9, max_lat: 5.5 };

function setNotice(id, message, type = "info") {
  const node = qs(id);
  if (!node) return;
  node.className = `notice notice-${type}`;
  node.textContent = message;
}

function renderInvestigationMeta(inv) {
  const root = qs("#investigation-meta");
  if (!root) return;
  clear(root);
  const dl = el("dl", { class: "dl" });
  const add = (k, v) => dl.append(el("dt", { text: k }), el("dd", { text: (v == null || v === "" ? "—" : (typeof v === "string" ? v : JSON.stringify(v))) }));
  add("Title", inv.title || inv.id);
  add("Question", inv.question || "—");
  add("Dataset", inv.dataset?.name || inv.dataset?.short_name || (typeof inv.dataset === "string" ? inv.dataset : "—"));
  add("Variable(s)", (inv.variables || []).join(", ") || "—");
  add("Geographical coverage", coverageText(inv.coverage?.spatial));
  add("Temporal coverage", coverageText(inv.coverage?.temporal));
  add("Availability", inv.availability || "—");
  root.append(dl);
  if (inv.limitations?.length) {
    const ul = el("ul");
    inv.limitations.forEach((x) => ul.appendChild(el("li", { text: typeof x === "string" ? x : JSON.stringify(x) })));
    root.append(el("p", { class: "field-hint", style: "margin-top:0.5rem;", text: "Known limitations:" }), ul);
  }
}

function getSelectedBounds() {
  if (selection?.bounds) return selection.bounds;
  return null;
}

function updateSelectionUI() {
  const info = qs("#selection-info");
  const bounds = getSelectedBounds();
  if (!bounds) {
    if (info) info.textContent = "No area selected. Choose a preset, click the map to set a point area, or enter coordinates.";
    return;
  }
  if (info) {
    const extra = selection?.lat != null ? ` (center ${formatNumber(selection.lat, {digits:4})}, ${formatNumber(selection.lon, {digits:4})})` : "";
    info.textContent = `Selected bounds: [${formatNumber(bounds.min_lon,{digits:4})}, ${formatNumber(bounds.min_lat,{digits:4})}] to [${formatNumber(bounds.max_lon,{digits:4})}, ${formatNumber(bounds.max_lat,{digits:4})}]${extra}. Backend validates supported coverage.`;
  }
  updateSummary();
}

function setPointSelection(lat, lon, bufferDeg = 0.1) {
  const b = Math.max(0.01, Math.min(5, Number(bufferDeg) || 0.1));
  const bounds = {
    min_lon: Math.max(-180, Number((lon - b).toFixed(6))),
    min_lat: Math.max(-90, Number((lat - b).toFixed(6))),
    max_lon: Math.min(180, Number((lon + b).toFixed(6))),
    max_lat: Math.min(90, Number((lat + b).toFixed(6))),
  };
  selection = { type: "point", lat, lon, bufferDeg: b, bounds };
  const latEl = qs("#point-lat"), lonEl = qs("#point-lon");
  if (latEl) latEl.value = String(lat);
  if (lonEl) lonEl.value = String(lon);
  if (map && window.maplibregl) {
    if (!marker) marker = new maplibregl.Marker({ color: "#0f766e" }).setLngLat([lon, lat]).addTo(map);
    else marker.setLngLat([lon, lat]);
    map.easeTo({ center: [lon, lat], zoom: Math.max(map.getZoom(), 6) });
  }
  updateSelectionUI();
}

function setPreset(preset) {
  if (preset === "kenya") {
    selection = { type: "preset", name: "Kenya", bounds: { ...KENYA_BOUNDS } };
    if (map) {
      try { map.fitBounds([[KENYA_BOUNDS.min_lon, KENYA_BOUNDS.min_lat], [KENYA_BOUNDS.max_lon, KENYA_BOUNDS.max_lat]], { padding: 20, duration: 0 }); } catch {}
    }
    updateSelectionUI();
  } else if (preset === "point") {
    // keep existing point if any; prompt via UI
    if (!selection || selection.type !== "point") {
      const info = qs("#selection-info");
      if (info) info.textContent = "Point mode: click the map or enter coordinates, then apply.";
    }
  }
}

function clearSelectionState() {
  selection = null;
  if (marker) { marker.remove(); marker = null; }
  updateSelectionUI();
  updateSummary();
}

function initMap() {
  const container = qs("#config-map");
  if (!container || !window.maplibregl) {
    const st = qs("#config-map-status");
    if (st) { st.hidden = false; st.className = "map-overlay map-overlay-status notice notice-warning"; st.textContent = "Map library unavailable. You can still enter coordinates/presets for bounds."; }
    return;
  }
  try {
    map = new maplibregl.Map({ container, style: config.map.styleUrl, center: config.map.defaultCenter, zoom: config.map.defaultZoom });
    map.addControl(new maplibregl.NavigationControl(), "top-right");
    map.on("load", () => {
      const st = qs("#config-map-status"); if (st) st.hidden = true;
    });
    map.on("click", (e) => {
      const buffer = Number(qs("#buffer-deg")?.value || 0.1);
      qs("#region-preset").value = "point";
      setPointSelection(e.lngLat.lat, e.lngLat.lng, buffer);
    });
    map.on("error", () => {
      const st = qs("#config-map-status"); if (st) { st.hidden = false; st.className = "map-overlay map-overlay-status notice notice-warning"; st.textContent = "Map tiles/style could not be fully loaded. Coordinate/preset selection still works."; }
    });
  } catch (err) {
    const st = qs("#config-map-status"); if (st) { st.hidden = false; st.className = "map-overlay map-overlay-status notice notice-error"; st.textContent = `Map initialization failed: ${err.message}`; }
  }
}

function buildPayload() {
  const investigation_id = (qs("#investigation-id")?.value || "").trim();
  const start = qs("#start-date")?.value || "";
  const end = qs("#end-date")?.value || "";
  const bounds = getSelectedBounds();
  return { investigation_id, bounds, period: { start, end } };
}

function updateSummary() {
  const root = qs("#param-summary");
  if (!root) return;
  const p = buildPayload();
  if (!p.investigation_id || !p.bounds || !p.period.start || !p.period.end) {
    root.textContent = "Complete investigation, geographical area, and historical period to review parameters.";
    return;
  }
  root.innerHTML = "";
  const ul = el("ul", { style: "margin:0;padding-left:1.1rem;" });
  ul.append(
    el("li", {}, [el("strong", { text: "Investigation: " }), document.createTextNode(p.investigation_id)]),
    el("li", {}, [el("strong", { text: "Period: " }), document.createTextNode(`${p.period.start} to ${p.period.end}`)]),
    el("li", {}, [el("strong", { text: "Bounds (WGS84): " }), document.createTextNode(`[${p.bounds.min_lon}, ${p.bounds.min_lat}, ${p.bounds.max_lon}, ${p.bounds.max_lat}]`)]),
  );
  root.append(ul);
}

async function runValidation(showSuccess = true) {
  const payload = buildPayload();
  const errorsEl = qs("#form-errors");
  if (errorsEl) errorsEl.textContent = "";
  const { valid, errors } = validateDateRange(payload.period.start, payload.period.end);
  if (!payload.investigation_id) errors.unshift({ message: "Investigation ID is required." });
  if (!payload.bounds) errors.unshift({ message: "Geographical bounds are required. Select a preset or point area." });
  if (!valid || errors.length) {
    const msg = summarizeErrors(errors);
    if (errorsEl) errorsEl.textContent = msg;
    setNotice("#submit-status", `Configuration incomplete/invalid: ${msg}`, "warning");
    return { ok: false, payload };
  }
  try {
    const res = await validateExecution(payload);
    if (res && res.valid === false) {
      const issues = res.issues || res.error?.details || [];
      const msg = Array.isArray(issues) && issues.length ? issues.map(i => `${i.field || "field"}: ${i.issue || i.message || "invalid"}`).join("; ") : (res.error?.message || "Validation failed.");
      if (errorsEl) errorsEl.textContent = msg;
      setNotice("#submit-status", `Backend validation failed: ${msg}`, "warning");
      return { ok: false, payload, response: res };
    }
    if (showSuccess) setNotice("#submit-status", "Configuration is valid according to the backend.", "success");
    return { ok: true, payload, response: res };
  } catch (err) {
    if (isEndpointMissing(err)) {
      setNotice("#submit-status", "Validation endpoint is unavailable on the connected backend. You can still attempt submission if supported; backend will enforce rules.", "warning");
      return { ok: true, payload, skipped: true };
    }
    if (err?.status === 422 || err?.status === 400) {
      const details = err?.data?.issues || err?.data?.error?.details || err?.details || [];
      const msg = Array.isArray(details) && details.length ? details.map(i => `${i.field || "field"}: ${i.issue || i.message || "invalid"}`).join("; ") : err.message;
      if (errorsEl) errorsEl.textContent = msg;
      setNotice("#submit-status", `Backend validation failed: ${msg}`, "warning");
      return { ok: false, payload, error: err };
    }
    throw err;
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  initMap();
  const invId = getParam("id") || getParam("investigation") || "INV-001";
  qs("#investigation-id").value = invId;
  setParams({ id: invId });

  try {
    const res = await getInvestigation(invId);
    const inv = normalizeInvestigation(res?.investigation || res);
    renderInvestigationMeta(inv);
    if (!isExecutable(inv.availability)) {
      setNotice("#investigation-status", `Investigation is not available for execution (status: ${inv.availability || "unknown"}). You can review and validate configuration, but submission will be rejected by the backend until it becomes available.`, "warning");
      qs("#submit-btn").disabled = true;
    } else {
      setNotice("#investigation-status", "Investigation details loaded from backend.", "success");
    }
    // coverage hints
    const temporal = inv.coverage?.temporal;
    if (temporal) qs("#period-hint").textContent = `Supported temporal coverage (backend): ${coverageText(temporal)}. Enter a valid period within coverage.`;
  } catch (err) {
    renderInvestigationMeta(normalizeInvestigation({ id: invId, title: invId, availability: "unavailable" }));
    setNotice("#investigation-status", `Could not load investigation details from backend: ${err.message}. Configuration may be incomplete.`, "warning");
  }

  // default selection
  setPreset("kenya");
  qs("#region-preset").addEventListener("change", (e) => setPreset(e.target.value));
  qs("#apply-point").addEventListener("click", () => {
    const lat = Number(qs("#point-lat").value);
    const lon = Number(qs("#point-lon").value);
    const buf = Number(qs("#buffer-deg").value || 0.1);
    if (!Number.isFinite(lat) || !Number.isFinite(lon) || lat < -90 || lat > 90 || lon < -180 || lon > 180) {
      setNotice("#submit-status", "Enter valid latitude/longitude before applying point selection.", "warning");
      return;
    }
    qs("#region-preset").value = "point";
    setPointSelection(lat, lon, buf);
  });
  qs("#clear-selection").addEventListener("click", () => { qs("#region-preset").value = ""; clearSelectionState(); });
  ["start-date","end-date","investigation-id"].forEach(id => qs(`#${id}`)?.addEventListener("change", updateSummary));
  ["start-date","end-date"].forEach(id => qs(`#${id}`)?.addEventListener("input", updateSummary));

  qs("#validate-btn").addEventListener("click", async () => {
    try { await runValidation(true); } catch (err) { setNotice("#submit-status", `Validation request failed: ${err.message}`, "error"); }
  });

  qs("#config-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const submitBtn = qs("#submit-btn");
    submitBtn.disabled = true;
    try {
      const validation = await runValidation(false);
      if (!validation.ok) return;
      setNotice("#submit-status", "Submitting investigation…", "info");
      const res = await submitExecution(validation.payload);
      const executionId = res?.execution_id || res?.id || res?.execution?.id;
      if (!executionId) throw new Error(res?.error?.message || res?.message || "Backend did not return an execution identifier.");
      const st = res?.execution?.status || res?.status;
      setNotice("#submit-status", `Execution ${executionId} ${statusLabel(st)}${res?.message ? ` — ${res.message}` : ""}. Redirecting to results…`, st === "failed" ? "warning" : "success");
      setTimeout(() => { window.location.href = `./results.html?execution=${encodeURIComponent(executionId)}`; }, 400);
    } catch (err) {
      if (isEndpointMissing(err)) {
        setNotice("#submit-status", "Execution API is unavailable on the connected backend. No analysis was submitted.", "warning");
      } else {
        const details = err?.data?.issues || err?.data?.error?.details || err?.details || [];
        const msg = Array.isArray(details) && details.length ? details.map(i => `${i.field || "field"}: ${i.issue || i.message || "invalid"}`).join("; ") : err.message;
        setNotice("#submit-status", `Submission failed: ${msg}`, "error");
        const errorsEl = qs("#form-errors"); if (errorsEl) errorsEl.textContent = msg;
      }
    } finally {
      submitBtn.disabled = false;
    }
  });

  updateSummary();
});
