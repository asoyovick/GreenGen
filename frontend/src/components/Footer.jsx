import { NOT_A_FORECAST, periodText } from "../lib/format.js";

export default function Footer({ health, variables, layerMeta }) {
  const period = periodText(health?.period) || periodText(layerMeta?.period);
  const sourceList = (variables?.variables || []).filter(
    (v) => v.source_dataset,
  );
  return (
    <footer className="site-footer">
      <div className="site-footer__grid">
        <div>
          <h2>About these numbers</h2>
          <p>
            {NOT_A_FORECAST} Rates are Theil–Sen slopes of annual anomalies.
            Significance is a Mann–Kendall test after Benjamini–Hochberg FDR
            correction at α = 0.05. Non-significance is not proof of no change.
          </p>
        </div>
        <div>
          <h2>Resolution and period</h2>
          <p>
            0.5° grid (about 55 km at the equator) · {period || "2002–2024"} ·
            monthly inputs, annual statistics. No gap filling.
          </p>
        </div>
        <div>
          <h2>Data and limits</h2>
          {health?.synthetic ? (
            <p>
              Synthetic demo data generated for this build. Not NASA
              observations. See <code>docs/DATA_SOURCES.md</code> and{" "}
              <code>docs/LIMITATIONS.md</code>.
            </p>
          ) : (
            <p>
              Sources are listed in <code>docs/DATA_SOURCES.md</code>. Read{" "}
              <code>docs/LIMITATIONS.md</code> before drawing conclusions.
            </p>
          )}
          {sourceList.length > 0 && (
            <details>
              <summary>Dataset names and versions</summary>
              <ul>
                {sourceList.map((v) => (
                  <li key={v.key}>
                    {v.display_name}: {v.source_dataset}
                    {v.dataset_version ? ` v${v.dataset_version}` : ""}
                    {v.model_based ? " (model-based)" : ""}
                  </li>
                ))}
              </ul>
            </details>
          )}
        </div>
      </div>
      <div className="site-footer__bottom">
        <span>
          Global Change Explorer · API {health?.version || "—"} · {health?.mode || "unknown"} mode
        </span>
        <span>
          Basemap: © OpenStreetMap contributors (when tile basemap loads) · Boundaries/names: Natural Earth (public domain).
        </span>
        <span>Boundaries and names are shown for reference and do not imply any position on disputed areas.</span>
        <span>{NOT_A_FORECAST}</span>
      </div>
    </footer>
  );
}
