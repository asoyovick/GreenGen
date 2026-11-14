import { getExecutionStatus, getExecutionSummary } from "../api/analysis.js";
import { qs, clear, el, getParam } from "../utils/helpers.js";
import { statusLabel, formatDateTime } from "../utils/formatting.js";

function renderMeta(obj) {
  const dl = el("dl", { class: "dl" });
  const entries = obj && typeof obj === "object" ? Object.entries(obj) : [];
  if (!entries.length) { dl.append(el("dt", { text: "Info" }), el("dd", { text: "No details available." })); return dl; }
  for (const [k, v] of entries) {
    dl.append(el("dt", { text: k }), el("dd", { text: typeof v === "object" ? JSON.stringify(v) : String(v ?? "—") }));
  }
  return dl;
}

async function load(id) {
  const statusEl = qs("#analysis-status");
  const details = qs("#execution-details");
  const summary = qs("#results-summary");
  if (!id) {
    statusEl.className = "notice notice-warning";
    statusEl.textContent = "Enter an execution ID to load status from the backend.";
    return;
  }
  statusEl.className = "notice notice-info";
  statusEl.innerHTML = '<span class="spinner" aria-hidden="true"></span> Loading execution status…';
  clear(details); clear(summary);
  try {
    const st = await getExecutionStatus(id);
    const label = statusLabel(st?.status || st?.state);
    statusEl.className = st?.status === "failed" ? "notice notice-error" : st?.status === "completed" ? "notice notice-success" : "notice notice-info";
    statusEl.textContent = `Execution ${id}: ${label}${st?.message ? ` — ${st.message}` : ""}`;
    details.append(el("h2", { text: "Execution details" }), renderMeta(st));
    if ((st?.status || st?.state) === "completed") {
      try {
        const sum = await getExecutionSummary(id);
        summary.append(el("h2", { text: "Results summary" }), renderMeta(sum));
      } catch (e) {
        summary.append(el("div", { class: "notice notice-warning", text: `Summary endpoint unavailable: ${e.message}` }));
      }
    }
  } catch (err) {
    statusEl.className = "notice notice-error";
    statusEl.textContent = `Unable to load execution: ${err.message}. Ensure the execution API is available and the ID is correct.`;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const input = qs("#execution-id");
  const loadBtn = qs("#load-execution");
  const refreshBtn = qs("#refresh-execution");
  const paramId = getParam("execution") || getParam("id");
  if (paramId && input) input.value = paramId;
  const run = () => load((input?.value || "").trim());
  loadBtn?.addEventListener("click", run);
  refreshBtn?.addEventListener("click", run);
  if (paramId) run();
});
