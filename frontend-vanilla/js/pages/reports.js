import { getExecutionReport, exportExecutionReport } from "../api/reports.js";
import { qs, clear, el, getParam } from "../utils/helpers.js";

function renderReport(report) {
  const root = qs("#report-content");
  clear(root);
  if (report?.available === false) {
    root.append(el("div", { class: "notice notice-warning", text: report.reason || "Report is not available for this execution." }));
    return;
  }
  const sections = [
    ["Investigation details", report.investigation || report.details],
    ["Methodology", report.methodology],
    ["Results", report.results || report.summary],
    ["Dataset information & provenance", report.provenance || report.dataset],
    ["Scientific limitations", report.limitations],
  ];
  for (const [title, data] of sections) {
    if (data == null) continue;
    const body = typeof data === "string" ? el("p", { text: data }) : Array.isArray(data)
      ? (() => { const ul = el("ul"); data.forEach((x) => ul.appendChild(el("li", { text: typeof x === "string" ? x : JSON.stringify(x) }))); return ul; })()
      : el("pre", { class: "mono", style: "white-space:pre-wrap;overflow:auto;" , text: JSON.stringify(data, null, 2) });
    root.append(el("section", { class: "panel stack" }, [el("h2", { style: "margin:0;", text: title }), body]));
  }
  if (!root.children.length) {
    root.append(el("section", { class: "panel" }, [el("h2", { style: "margin-top:0;", text: "Report" }), el("pre", { class: "mono", style: "white-space:pre-wrap;overflow:auto;", text: JSON.stringify(report, null, 2) })]));
  }
  const actions = el("div", { class: "inline-actions" });
  const expBtn = el("button", { class: "btn btn-secondary", type: "button", text: "Export (if supported)" });
  expBtn.addEventListener("click", async () => {
    try {
      const out = await exportExecutionReport(report.execution_id || report.id || qs("#report-execution-id").value.trim(), "json");
      const blob = new Blob([JSON.stringify(out, null, 2)], { type: "application/json" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `greengen-report-${report.execution_id || "export"}.json`;
      a.click();
      URL.revokeObjectURL(a.href);
    } catch (e) {
      qs("#report-status").className = "notice notice-warning";
      qs("#report-status").textContent = e.message || "Export is not available.";
    }
  });
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
