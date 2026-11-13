import { useState } from "react";
import TrendChart from "./TrendChart.jsx";
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
          <span className="variable-card__rate">
            {formatRate(row.rate_per_decade, row.unit)}
          </span>
        </span>
        <VerdictBadge row={row} />
      </span>
      <span className="variable-card__flags">
        {row.model_based && <span className="badge badge--model">Model-based</span>}
        {row.low_confidence && <span className="badge badge--warn">Low confidence</span>}
        {!row.significant && (
          <span className="badge badge--flat">Not significant</span>
        )}
      </span>
      {row.nearby && (
        <span className="variable-card__nearby">
          Nearby ({row.nearby.n_cells} cells): {nearbyText(row.nearby)}
        </span>
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
      <div>
        <dt>Dataset</dt>
        <dd>{source}</dd>
      </div>
      <div>
        <dt>Period used</dt>
        <dd>{periodText(row.period) || "—"}</dd>
      </div>
      <div>
        <dt>Years used</dt>
        <dd>{row.n_years}</dd>
      </div>
      <div>
        <dt>Surface</dt>
        <dd>{row.surface || "unknown"}</dd>
      </div>
      <div>
        <dt>Data type</dt>
        <dd>
          {row.model_based
            ? "Model-based reanalysis, not a direct observation"
            : "Observation-based"}
        </dd>
      </div>
      {row.standardized !== undefined && (
        <div>
          <dt>Standardized trend</dt>
          <dd>{formatNumber(row.standardized)} (unitless, variability-scaled)</dd>
        </div>
      )}
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
  const activeRow =
    rows.find((row) => row.key === selectedVariable) || rows[0] || null;

  async function copyLink() {
    const ok = await copyText(
      shareUrl(
        report?.cell?.lat ?? selected.lat,
        report?.cell?.lon ?? selected.lon,
        layerId,
      ),
    );
    setCopyStatus(ok ? "Shareable link copied." : "Could not copy the link.");
  }

  if (!selected) {
    return (
      <>
        <div className="report-head">
          <span className="eyebrow">Location report</span>
          <h2>Pick a place</h2>
          <p className="report-head__meta">
            Click the map to choose a 0.5° grid cell.
          </p>
        </div>
        <div className="report-panel__scroll">
          <div className="empty-state">
            <h3>No location selected</h3>
            <p>
              Click anywhere on the map. The report ranks the variables that
              changed at that cell and explains whether the change is
              statistically significant.
            </p>
            <p className="field-help">
              Observed change only. Non-significant means no significant change
              was detected, not that nothing changed.
            </p>
          </div>
        </div>
      </>
    );
  }

  const cell = report?.cell || selected;
  return (
    <>
      <div className="report-head">
        <span className="eyebrow">Location report</span>
        <h2>
          {selected.label
            ? selected.label
            : formatCoord(cell.lat, cell.lon)}
        </h2>
        <p className="report-head__meta">
          {selected.label && `${formatCoord(cell.lat, cell.lon)} · `}
          Nearest 0.5° grid cell
          {report?.mode ? ` · ${report.mode} mode` : ""}
        </p>
      </div>

      <div className="report-panel__scroll">
        {loading && (
          <div className="loading-block" role="status">
            <div className="spinner" aria-hidden="true" />
            <p>Looking up precomputed trends and significance…</p>
          </div>
        )}

        {error && !loading && (
          <div className="empty-state" role="alert">
            <h3>Report unavailable</h3>
            <p>{error}</p>
            <button type="button" className="button button--primary" onClick={onRetry}>
              Retry this location
            </button>
          </div>
        )}

        {report && !loading && !error && (
          <>
            <div className="report-summary" aria-live="polite">
              <p>{report.summary}</p>
            </div>

            <div className="report-export" aria-label="Export this report">
              <span className="field-help">Export or share</span>
              <div className="export-row">
                <button
                  type="button"
                  className="button button--small"
                  onClick={() => exportReportMarkdown(report)}
                >
                  Markdown
                </button>
                <button
                  type="button"
                  className="button button--small"
                  onClick={() => exportReportJson(report)}
                >
                  JSON
                </button>
                <button type="button" className="button button--small" onClick={copyLink}>
                  Copy link
                </button>
              </div>
              {copyStatus && (
                <p className="copy-status" role="status">
                  {copyStatus}
                </p>
              )}
            </div>

            {report.divergence_detected && (
              <div className="callout" role="note">
                <strong>Neighbours move in opposite directions.</strong> Within
                about {report.query?.window_deg ?? 5}° of this cell, at least one
                variable has both significant increases and significant
                decreases. A single regional average would hide that.
              </div>
            )}

            {report.surface_inferred && (
              <p className="surface-note">{report.surface_inferred.explanation}</p>
            )}

            {rows.length === 0 ? (
              <div className="empty-state">
                <h3>No variables apply here</h3>
                <p>
                  None of the variables in this layer set has data at this
                  location. That is common over open ocean, ice, or outside a
                  land-only dataset. It does not mean nothing changed.
                </p>
              </div>
            ) : (
              <>
                <section className="report-section">
                  <div className="report-section__head">
                    <h3>Variables that apply here</h3>
                    <span className="field-help">Ranked by strength</span>
                  </div>
                  <div className="variable-list">
                    {rows.map((row) => (
                      <VariableCard
                        key={row.key}
                        row={row}
                        active={row.key === activeRow?.key}
                        onSelect={onSelectVariable}
                      />
                    ))}
                  </div>
                </section>

                <section className="report-section">
                  <div className="chart-header">
                    <div>
                      <h3>{activeRow?.variable} over time</h3>
                      <p className="chart-sub">
                        Annual anomaly with the stored Theil–Sen trend.
                      </p>
                    </div>
                    {activeRow && <VerdictBadge row={activeRow} />}
                  </div>
                  {timeseriesLoading && (
                    <div className="loading-block" role="status">
                      <div className="spinner" aria-hidden="true" />
                      <p>Loading the annual time series…</p>
                    </div>
                  )}
                  {timeseriesError && !timeseriesLoading && (
                    <div className="empty-state" role="alert">
                      <p>{timeseriesError}</p>
                    </div>
                  )}
                  {timeseries && !timeseriesLoading && !timeseriesError && timeseries.applies && (
                    <TrendChart series={timeseries} />
                  )}
                  {timeseries && !timeseriesLoading && !timeseriesError && timeseries.applies === false && (
                    <p className="field-help">{timeseries.summary}</p>
                  )}
                </section>

                <section className="report-section">
                  <h3>Provenance for the charted variable</h3>
                  <Provenance row={activeRow} />
                  <p className="field-help">
                    Significance is the FDR-corrected Mann–Kendall result (α =
                    0.05). Raw p-values are not shown.
                  </p>
                </section>
              </>
            )}

            <section className="report-section">
              <h3>Nearby comparison</h3>
              {activeRow?.nearby ? (
                <p className="field-help">
                  Within about {report.query?.window_deg ?? 5}°,{" "}
                  {nearbyText(activeRow.nearby)} This is a local context check,
                  not a separate statistical test.
                </p>
              ) : (
                <p className="field-help">
                  No nearby comparison is available for this location.
                </p>
              )}
              <p className="field-help">{report.not_a_forecast}</p>
            </section>
          </>
        )}
      </div>
    </>
  );
}
