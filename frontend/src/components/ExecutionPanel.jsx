import { useEffect, useRef, useState } from "react";
import { api } from "../api.js";

const DEFAULT_BOUNDS = { min_lon: 33.9, min_lat: -4.7, max_lon: 41.9, max_lat: 5.5 };
const DEFAULT_PERIOD = { start: "2001-01-01", end: "2020-12-31" };
const TERMINAL = new Set(["completed", "failed"]);

function fmtStatus(s) {
  return String(s || "unknown").replace(/_/g, " ");
}

export default function ExecutionPanel() {
  const [investigationId, setInvestigationId] = useState("INV-001");
  const [bounds, setBounds] = useState(DEFAULT_BOUNDS);
  const [period, setPeriod] = useState(DEFAULT_PERIOD);
  const [submitting, setSubmitting] = useState(false);
  const [execution, setExecution] = useState(null);
  const [error, setError] = useState(null);
  const [report, setReport] = useState(null);
  const [reportError, setReportError] = useState(null);
  const pollRef = useRef(null);

  useEffect(() => () => { if (pollRef.current) clearTimeout(pollRef.current); }, []);

  function updateBound(key, value) {
    setBounds((b) => ({ ...b, [key]: value === "" ? "" : Number(value) }));
  }

  async function poll(id) {
    try {
      const res = await api.v1.refreshExecution(id);
      const ex = res.execution || res;
      setExecution(ex);
      if (TERMINAL.has(ex.status)) {
        if (ex.status === "completed") {
          try {
            const rep = await api.v1.report(id);
            setReport(rep.report || rep);
            setReportError(null);
          } catch (e) {
            setReport(null);
            setReportError(e?.message || "Report unavailable.");
          }
        }
        return;
      }
      pollRef.current = setTimeout(() => poll(id), 3000);
    } catch (e) {
      setError(e?.message || "Failed to refresh execution status.");
    }
  }

  async function onSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    setReport(null);
    setReportError(null);
    setExecution(null);
    if (pollRef.current) clearTimeout(pollRef.current);
    try {
      const payload = { investigation_id: investigationId, bounds, period };
      const res = await api.v1.submitExecution(payload);
      const ex = res.execution || res;
      setExecution(ex);
      if (ex?.id && !TERMINAL.has(ex.status)) poll(ex.id);
      if (ex?.status === "completed" && ex?.id) {
        try { const rep = await api.v1.report(ex.id); setReport(rep.report || rep); } catch (re) { setReportError(re?.message || "Report unavailable."); }
      }
    } catch (err) {
      const details = err?.data?.error?.details;
      setError(details ? `${err.message}: ${JSON.stringify(details)}` : (err?.message || "Submission failed."));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="report-section" aria-labelledby="execution-panel-title">
      <h3 id="execution-panel-title">Run investigation (backend v1)</h3>
      <p className="field-help">Submits to the Go backend contract-aligned execution API. Results appear only when verified, non-synthetic outputs are ingested.</p>
      <form onSubmit={onSubmit} className="execution-form">
        <label className="field-label" htmlFor="exec-investigation">Investigation</label>
        <select id="exec-investigation" value={investigationId} onChange={(e) => setInvestigationId(e.target.value)}>
          <option value="INV-001">INV-001 Precipitation trends</option>
        </select>

        <div className="field-grid" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
          {["min_lon", "min_lat", "max_lon", "max_lat"].map((k) => (
            <label key={k} className="field-label">{k}
              <input type="number" step="any" value={bounds[k]} onChange={(e) => updateBound(k, e.target.value)} aria-label={k} />
            </label>
          ))}
        </div>
        <div className="field-grid" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
          <label className="field-label">Start
            <input type="date" value={period.start} onChange={(e) => setPeriod((p) => ({ ...p, start: e.target.value }))} />
          </label>
          <label className="field-label">End
            <input type="date" value={period.end} onChange={(e) => setPeriod((p) => ({ ...p, end: e.target.value }))} />
          </label>
        </div>
        <button type="submit" className="button button--primary" disabled={submitting}>
          {submitting ? "Submitting..." : "Run analysis"}
        </button>
      </form>

      <div aria-live="polite" style={{ marginTop: 8 }}>
        {error && <p role="alert" className="field-help" style={{ color: "#b91c1c" }}>{error}</p>}
        {execution && (
          <div className="panel panel--compact">
            <p><strong>Status:</strong> <span className={`status-chip status-chip--${execution.status}`}>{fmtStatus(execution.status)}</span></p>
            <p className="field-help">Execution ID: {execution.id}</p>
            {execution.error_message && <p role="alert" className="field-help" style={{ color: "#b91c1c" }}>{execution.error_message}</p>}
          </div>
        )}
        {reportError && <p className="field-help" role="status">Report: {reportError}</p>}
        {report && (
          <details style={{ marginTop: 8 }}>
            <summary>Execution report (JSON)</summary>
            <pre style={{ maxHeight: 240, overflow: "auto", fontSize: 12 }}><code>{JSON.stringify(report, null, 2)}</code></pre>
          </details>
        )}
      </div>
    </section>
  );
}
