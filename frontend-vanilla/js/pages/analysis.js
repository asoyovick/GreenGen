import { getExecutionStatus, getExecutionSummary, refreshExecutionStatus, isResultsUnavailable } from "../api/analysis.js";
import { qs, clear, el, getParam } from "../utils/helpers.js";
import { statusLabel } from "../utils/formatting.js";

function renderMeta(obj) {
  const dl = el("dl", { class: "dl" });
  const entries = obj && typeof obj === "object" ? Object.entries(obj) : [];
  if (!entries.length) { dl.append(el("dt", { text: "Info" }), el("dd", { text: "No details available." })); return dl; }
  for (const [k, v] of entries) {
    dl.append(el("dt", { text: k }), el("dd", { text: typeof v === "object" ? JSON.stringify(v) : String(v ?? "—") }));
  }
  return dl;
}

async function load(id, doRefresh = false) {
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
    const res = doRefresh ? await refreshExecutionStatus(id) : await getExecutionStatus(id);
    const st = res?.execution || res;
    const label = statusLabel(st?.status || st?.state);
    statusEl.className = st?.status === "failed" ? "notice notice-error" : st?.status === "completed" ? "notice notice-success" : "notice notice-info";
    statusEl.textContent = `Execution ${id}: ${label}${st?.error_message ? ` — ${st.error_message}` : (res?.message ? ` — ${res.message}` : "")}`;
    details.append(el("h2", { text: "Execution details" }), renderMeta(st));
    if ((st?.status || st?.state) === "completed") {
      try {
        const sum = await getExecutionSummary(id);
        summary.append(el("h2", { text: "Results summary" }), renderMeta(sum?.execution ? sum : sum));
      } catch (e) {
        const msg = isResultsUnavailable(e) ? (e?.data?.error?.message || "No verified summary available.") : `Summary endpoint unavailable: ${e.message}`;
        summary.append(el("div", { class: "notice notice-warning", text: msg }));
      }
    } else {
      summary.append(el("div", { class: "notice notice-info", text: "Results/summary become available only after a completed execution with verified scientific outputs." }));
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
  loadBtn?.addEventListener("click", () => load((input?.value || "").trim(), false));
  refreshBtn?.addEventListener("click", () => load((input?.value || "").trim(), true));
  if (paramId) load(paramId, false);
});
