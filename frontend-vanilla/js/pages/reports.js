import { getExecutionReport, exportExecutionReport } from "../api/reports.js";
import { qs, clear, el, getParam } from "../utils/helpers.js";

function renderValue(data) {
  if (data == null) return el("p", { class: "muted", text: "Not provided." });
  if (typeof data === "string" || typeof data === "number" || typeof data === "boolean") return el("p", { text: String(data) });
  if (Array.isArray(data)) {
    if (!data.length) return el("p", { class: "muted", text: "No items." });
    const ul = el("ul");
    data.forEach((x) => ul.appendChild(el("li", {}, [typeof x === "object" && x ? el("pre", { class: "mono", style: "white-space:pre-wrap;margin:0;", text: JSON.stringify(x, null, 2) }) : document.createTextNode(String(x))])));
    return ul;
  }
  if (typeof data === "object") {
    const pre = el("pre", { class: "mono", style: "white-space:pre-wrap;overflow:auto;margin:0;" });
    pre.textContent = JSON.stringify(data, null, 2);
    return pre;
  }
  return el("p", { text: String(data) });
}

function renderReport(payload) {
  const root = qs("#report-content");
  clear(root);
  const report = payload?.report || payload;
  if (payload?.available === false || report?.available === false) {
    root.append(el("div", { class: "notice notice-warning", text: payload?.reason || report?.reason || "Report is not available for this execution." }));
    if (payload?.details) root.append(el("section", { class: "panel" }, [el("h3", { style: "margin-top:0;", text: "Details" }), renderValue(payload.details)]));
    return;
  }

  const execution = payload?.execution || report?.execution || null;
  const sections = [
    ["Execution", execution],
    ["Investigation details", report?.investigation || report?.investigation_details || report?.details],
    ["Methodology", report?.methodology],
    ["Scientific findings / results", report?.results || report?.findings],
    ["Summary", report?.summary],
    ["Dataset information & provenance", report?.provenance || report?.dataset || report?.dataset_information],
    ["Uncertainty & quality", report?.uncertainty || report?.quality || report?.data_quality],
    ["Scientific limitations", report?.limitations || report?.scientific_limitations],
    ["Run metadata", report?.run_metadata || payload?.run_metadata],
  ];

  let rendered = 0;
  for (const [title, data] of sections) {
    if (data == null) continue;
    rendered++;
    root.append(el("section", { class: "panel stack" }, [el("h2", { style: "margin:0;", text: title }), renderValue(data)]));
  }
  if (!rendered) {
    root.append(el("section", { class: "panel" }, [el("h2", { style: "margin-top:0;", text: "Report payload" }), renderValue(report)]));
  }

  const actions = el("div", { class: "inline-actions" });
  const execId = payload?.execution_id || report?.execution_id || qs("#report-execution-id")?.value?.trim();
  const expBtn = el("button", { class: "btn btn-secondary", type: "button", text: "Export JSON (if supported)" });
  expBtn.addEventListener("click", async () => {
    try {
      const out = await exportExecutionReport(execId, "json");
      const blob = new Blob([JSON.stringify(out, null, 2)], { type: "application/json" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `greengen-report-${execId || "export"}.json`;
      a.click();
      URL.revokeObjectURL(a.href);
    } catch (e) {
      qs("#report-status").className = "notice notice-warning";
      qs("#report-status").textContent = e?.message || "Export is not available.";
    }
  });
  if (execId) actions.append(el("a", { class: "btn btn-secondary", href: `./results.html?execution=${encodeURIComponent(execId)}`, text: "Open results view" }));
  actions.append(expBtn);
  root.prepend(actions);
}

document.addEventListener("DOMContentLoaded", () => {
  const input = qs("#report-execution-id");
  const btn = qs("#load-report");
  const status = qs("#report-status");
  const paramId = getParam("execution") || getParam("id");
  if (paramId && input) input.value = paramId;
  async function load() {
    const id = (input?.value || "").trim();
    if (!id) { status.className = "notice notice-warning"; status.textContent = "Please enter an execution ID."; return; }
    status.className = "notice notice-info";
    status.innerHTML = '<span class="spinner" aria-hidden="true"></span> Loading report…';
    try {
      const report = await getExecutionReport(id);
      status.className = report?.available === false ? "notice notice-warning" : "notice notice-success";
      status.textContent = report?.available === false ? (report.reason || "Report not available.") : `Report loaded for execution ${id}.`;
      renderReport({ execution_id: id, ...report });
    } catch (err) {
      status.className = "notice notice-error";
      status.textContent = `Unable to load report: ${err.message}`;
      clear(qs("#report-content"));
    }
  }
  btn?.addEventListener("click", load);
  if (paramId) load();
});
