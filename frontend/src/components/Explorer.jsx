import { useEffect, useMemo, useState } from "react";
import LayerLegend from "./LayerLegend.jsx";
import LayerSwitcher from "./LayerSwitcher.jsx";
import WorldMap from "./WorldMap.jsx";
import { normalizeLon } from "../lib/coords.js";
import { formatCoord } from "../lib/format.js";
import { readUrlState, writeUrlState } from "../lib/url.js";

export default function Explorer({ health, layers, variables }) {
  const layerIds = useMemo(
    () => Object.keys(layers?.layers || {}),
    [layers],
  );
  const defaults = useMemo(() => readUrlState(layerIds), [layerIds]);

  const [selectedLayerId, setSelectedLayerId] = useState(
    () => defaults.layer || layers?.default_layer || layerIds[0],
  );
  const [opacity, setOpacity] = useState(0.82);
  const [selected, setSelected] = useState(defaults.point || null);
  const [flyTarget, setFlyTarget] = useState(null);

  const activeLayer =
    layers?.layers?.[selectedLayerId] || layers?.layers?.[layerIds[0]];

  useEffect(() => {
    writeUrlState({ point: selected, layer: selectedLayerId });
  }, [selected, selectedLayerId]);

  function selectPoint(point, options = {}) {
    const normalized = {
      lat: point.lat,
      lon: normalizeLon(point.lon),
      label: point.label || null,
    };
    setSelected(normalized);
    if (options.fly) {
      setFlyTarget({
        lat: normalized.lat,
        lon: normalized.lon,
        zoom: options.zoom || 3.6,
        nonce: Date.now(),
      });
    }
  }

  function changeLayer(id) {
    if (layers?.layers?.[id]) setSelectedLayerId(id);
  }

  return (
    <div className="explorer">
      <div className="map-column">
        <WorldMap
          layer={activeLayer}
          opacity={opacity}
          selected={selected}
          flyTarget={flyTarget}
          synthetic={health?.synthetic}
          onSelect={selectPoint}
        >
          <div className="map-overlay map-overlay--layers">
            <LayerSwitcher
              metadata={layers}
              selectedId={activeLayer?.id || ""}
              onChange={changeLayer}
              opacity={opacity}
              onOpacityChange={setOpacity}
            />
          </div>
          <div className="map-overlay map-overlay--legend">
            <LayerLegend layer={activeLayer} />
          </div>
        </WorldMap>
      </div>

      <aside className="panel report-panel" aria-label="Change report">
        <div className="report-head">
          <span className="eyebrow">Location report</span>
          <h2>{selected ? formatCoord(selected.lat, selected.lon) : "Pick a place"}</h2>
          <p className="report-head__meta">
            {selected
              ? "Nearest 0.5° grid cell · report loads in the next step"
              : "Click the map to choose a 0.5° grid cell."}
          </p>
        </div>
        <div className="report-panel__scroll">
          <div className="empty-state">
            <h3>{selected ? "Location selected" : "No location selected"}</h3>
            <p>
              {selected
                ? `You chose ${formatCoord(selected.lat, selected.lon)}. The variable ranking, rates, significance and time series will appear here.`
                : "Click anywhere on the map. The report ranks the variables that changed at that cell and explains whether the change is significant."}
            </p>
            <p className="field-help">
              Observed change only. Non-significant means no significant change
              was detected, not that nothing changed.
            </p>
          </div>
          <div className="report-section">
            <h3>Variables in this mode</h3>
            <ul className="plain-list">
              {(variables?.variables || []).map((variable) => (
                <li key={variable.key}>
                  <strong>{variable.display_name}</strong>
                  <span>
                    {" "}
                    — {variable.unit}
                    {variable.model_based ? " · model-based" : ""}
                  </span>
                </li>
              ))}
            </ul>
          </div>
          <div className="report-section">
            <h3>Layer set</h3>
            <dl className="provenance">
              <div>
                <dt>Mode</dt>
                <dd>{health?.mode || "unknown"}</dd>
              </div>
              <div>
                <dt>Period</dt>
                <dd>{health?.period?.join(" to ") || "—"}</dd>
              </div>
              <div>
                <dt>Grid</dt>
                <dd>{health?.grid?.resolution_deg ?? 0.5}°</dd>
              </div>
              <div>
                <dt>Significance</dt>
                <dd>Mann–Kendall, FDR-corrected (α = 0.05)</dd>
              </div>
            </dl>
          </div>
        </div>
      </aside>
    </div>
  );
}
