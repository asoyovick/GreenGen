import { lazy, Suspense, useState } from "react";
import {
  copyText,
  exportReportJson,
  exportReportMarkdown,
  shareUrl,
} from "../lib/export.js";
import {
  formatCoord,
  formatNumber,
  formatRate,
  nearbyText,
  periodText,
  verdictIcon,
  verdictText,
} from "../lib/format.js";

const TrendChart = lazy(() => import("./TrendChart.jsx"));

function VerdictBadge({ row }) {
  const tone = !row.significant ? "flat" : row.class > 0 ? "up" : "down";
  return (
    <span className={`badge badge--${tone}`}>
      <span aria-hidden="true">{verdictIcon(row)}</span>
      {verdictText(row)}
    </span>
  );
}

function VariableCard({ row, active, onSelect }) {
  return (
    <button
      type="button"
      className={`variable-card ${active ? "variable-card--active" : ""}`}
      onClick={() => onSelect(row.key)}
      aria-pressed={active}
    >
      <span className="variable-card__top">
        <span>
          <span className="variable-card__name">{row.variable}</span>
          <span className="variable-card__rate">{formatRate(row.rate_per_decade, row.unit)}</span>
        </span>
        <VerdictBadge row={row} />
      </span>
      <span className="variable-card__flags">
        {row.model_based && <span className="badge badge--model">Model-based</span>}
        {row.low_confidence && <span className="badge badge--warn">Low confidence</span>}
        {!row.significant && <span className="badge badge--flat">Not significant</span>}
        {row.scale === "grid_cell" && <span className="badge">Grid-cell scale</span>}
      </span>
      {row.nearby && (
        <span className="variable-card__nearby">Nearby ({row.nearby.n_cells} cells): {nearbyText(row.nearby)}</span>
      )}
      {row.inside_place && (
        <span className="variable-card__nearby">Inside: {Math.round((row.inside_place.up || 0) * 100)}% up, {Math.round((row.inside_place.down || 0) * 100)}% down</span>
      )}
    </button>
  );
}

function Provenance({ row }) {
  if (!row) return null;
  const source = row.source_dataset
    ? `${row.source_dataset}${row.dataset_version ? ` v${row.dataset_version}` : ""}`
    : row.synthetic
      ? "Synthetic demo layer (no NASA dataset)"
      : "Not recorded";
  return (
    <dl className="provenance">
      <div><dt>Dataset</dt><dd>{source}</dd></div>
      <div><dt>Period used</dt><dd>{periodText(row.period) || "—"}</dd></div>
      <div><dt>Years used</dt><dd>{row.n_years}</dd></div>
      <div><dt>Surface</dt><dd>{row.surface || "unknown"}</dd></div>
      <div><dt>Data type</dt><dd>{row.model_based ? "Model-based reanalysis, not a direct observation" : "Observation-based"}</dd></div>
      {row.scale && <div><dt>Scale</dt><dd>{row.scale === "region_average" ? "Region average" : "Grid-cell scale"}</dd></div>}
      {row.coverage != null && <div><dt>Coverage</dt><dd>{Math.round(row.coverage * 100)}%</dd></div>}
      {row.n_cells != null && <div><dt>Cells</dt><dd>{row.n_cells}</dd></div>}
      {row.standardized !== undefined && <div><dt>Standardized trend</dt><dd>{formatNumber(row.standardized)} (unitless)</dd></div>}
    </dl>
  );
}

export default function ReportPanel({
  selected,
  report,
  loading,
  error,
  onRetry,
  selectedVariable,
  onSelectVariable,
  timeseries,
  timeseriesLoading,
  timeseriesError,
  layerId,
}) {
  const [copyStatus, setCopyStatus] = useState("");
  const rows = report?.variables || [];
  const activeRow = rows.find((row) => row.key === selectedVariable) || rows[0] || null;
  const place = report?.place || null;
  const cell = report?.cell || (place?.centroid ? { lat: place.centroid[1], lon: place.centroid[0] } : selected);

  async function copyLink() {
    const url = new URL(window.location.href);
    url.searchParams.set("layer", layerId || "");
    const ok = await copyText(url.toString());
    setCopyStatus(ok ? "Shareable link copied." : "Could not copy the link.");
  }

  if (!selected && !place) {
    return (
      <>
        <div className="report-head">
          <span className="eyebrow">Location report</span>
          <h2>Pick a place</h2>
          <p className="report-head__meta">Click the map, search, or choose a place level.</p>
        </div>
        <div className="report-panel__scroll">
          <div className="empty-state">
            <h3>No place selected</h3>
            <p>Click a place on the map or use search. Reports show precomputed, FDR-corrected observed change — not forecasts.</p>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <div className="report-head">
        <span className="eyebrow">{place ? `${place.level} report` : "Location report"}</span>
        <h2>{place ? place.name : (selected?.label || formatCoord(cell?.lat, cell?.lon))}</h2>
        <p className="report-head__meta">
          {place ? place.hierarchy : (cell ? `${formatCoord(cell.lat, cell.lon)} · Nearest 0.5° grid cell` : "")}
          {report?.scale ? ` · ${report.scale === "region_average" ? "region average" : "grid-cell scale"}` : ""}
          {report?.mode ? ` · ${report.mode} mode` : ""}
        </p>
      </div>

      <div className="report-panel__scroll">
        {loading && (
          <div className="loading-block" role="status">
            <div className="spinner" aria-hidden="true" />
            <p>Loading precomputed trends and significance…</p>
          </div>
        )}

        {error && !loading && (
          <div className="empty-state" role="alert">
            <h3>Report unavailable</h3>
            <p>{error}</p>
            <button type="button" className="button button--primary" onClick={onRetry}>Retry</button>
          </div>
        )}

        {report && !loading && !error && (
          <>
            <div className="report-summary" aria-live="polite"><p>{report.summary}</p></div>

            <div className="report-export" aria-label="Export this report">
              <span className="field-help">Export or share</span>
              <div className="export-row">
                <button type="button" className="button button--small" onClick={() => exportReportMarkdown(report)}>Markdown</button>
                <button type="button" className="button button--small" onClick={() => exportReportJson(report)}>JSON</button>
                <button type="button" className="button button--small" onClick={copyLink}>Copy link</button>
              </div>
              {copyStatus && <p className="copy-status" role="status">{copyStatus}</p>}
            </div>

            {report.divergence_detected && (
              <div className="callout" role="note">
                <strong>Areas move in opposite directions.</strong> Significant increases and decreases both occur within this selection; an average can hide local differences.
              </div>
            )}

            {rows.length === 0 ? (
              <div className="empty-state">
                <h3>No variables apply here</h3>
                <p>None of the variables in this layer set applies at this location. This does not mean nothing changed.</p>
              </div>
            ) : (
              <>
                <section className="report-section">
                  <div className="report-section__head">
                    <h3>Variables</h3>
                    <span className="field-help">Ranked by strength and significance</span>
                  </div>
                  <div className="variable-list">
                    {rows.map((row) => (
                      <VariableCard key={row.key} row={row} active={row.key === activeRow?.key} onSelect={onSelectVariable} />
                    ))}
                  </div>
                </section>

                <section className="report-section">
                  <div className="chart-header">
                    <div>
                      <h3>{activeRow?.variable} over time</h3>
                      <p className="chart-sub">Annual anomaly with the stored Theil–Sen trend.</p>
                    </div>
                    {activeRow && <VerdictBadge row={activeRow} />}
                  </div>
                  {timeseriesLoading && <div className="loading-block" role="status"><div className="spinner" aria-hidden="true" /><p>Loading time series…</p></div>}
                  {timeseriesError && !timeseriesLoading && <div className="empty-state" role="alert"><p>{timeseriesError}</p></div>}
                  {timeseries && !timeseriesLoading && !timeseriesError && timeseries.applies && (
                    <Suspense fallback={<div className="loading-block" role="status"><div className="spinner" aria-hidden="true" /><p>Loading chart…</p></div>}>
                      <TrendChart series={timeseries} />
                    </Suspense>
                  )}
                  {timeseries && !timeseriesLoading && !timeseriesError && timeseries.applies === false && <p className="field-help">{timeseries.summary}</p>}
                </section>

                {activeRow?.inside_place && (
                  <section className="report-section">
                    <h3>Inside this place</h3>
                    <p className="field-help">
                      Area-weighted share of valid cells: {Math.round((activeRow.inside_place.up || 0) * 100)}% significant increase, {Math.round((activeRow.inside_place.down || 0) * 100)}% significant decrease, {Math.round((activeRow.inside_place.none || 0) * 100)}% no significant change ({activeRow.inside_place.n_cells} cells).
                    </p>
                    {activeRow.inside_place_summary && <p className="field-help">{activeRow.inside_place_summary}</p>}
                  </section>
                )}

                {report.neighbor_summary ? (
                  <section className="report-section">
                    <h3>Neighboring places</h3>
                    <p className="field-help">{report.neighbor_summary}</p>
                  </section>
                ) : null}

                <section className="report-section">
                  <h3>Provenance</h3>
                  <Provenance row={activeRow} />
                  <p className="field-help">Significance is the FDR-corrected Mann–Kendall result (α = 0.05). Raw p-values are not shown.</p>
                </section>
              </>
            )}

            {!place && (
              <section className="report-section">
                <h3>Nearby comparison</h3>
                {activeRow?.nearby ? (
                  <p className="field-help">Within about {report.query?.window_deg ?? 5}°, {nearbyText(activeRow.nearby)} This is a local context check, not a separate statistical test.</p>
                ) : (
                  <p className="field-help">No nearby comparison is available.</p>
                )}
              </section>
            )}

            <p className="field-help">{report.not_a_forecast}</p>
          </>
        )}
      </div>
    </>
  );
}
