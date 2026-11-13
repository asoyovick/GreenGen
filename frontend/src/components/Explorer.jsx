import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import LayerLegend from "./LayerLegend.jsx";
import LayerSwitcher from "./LayerSwitcher.jsx";
import ReportPanel from "./ReportPanel.jsx";
import SearchControl from "./SearchControl.jsx";
import WorldMap from "./WorldMap.jsx";
import { api } from "../api.js";
import { normalizeLon } from "../lib/coords.js";
import { readUrlState, writeUrlState } from "../lib/url.js";

const IDLE = { status: "idle", data: null, error: null };
const LEVELS = [
  { id: "city", label: "City" },
  { id: "region", label: "Region" },
  { id: "country", label: "Country" },
  { id: "sea", label: "Sea" },
];

export default function Explorer({ health, layers }) {
  const layerIds = useMemo(() => Object.keys(layers?.layers || {}), [layers]);
  const defaults = useMemo(() => readUrlState(layerIds), [layerIds]);

  const [selectedLayerId, setSelectedLayerId] = useState(
    () => defaults.layer || layers?.default_layer || layerIds[0],
  );
  const [selectLevel, setSelectLevel] = useState(defaults.level || "region");
  const [opacity, setOpacity] = useState(0.82);
  const [selection, setSelection] = useState(
    defaults.place
      ? { type: "place", placeId: defaults.place }
      : defaults.point
        ? { type: "point", point: defaults.point }
        : null,
  );
  const [flyTarget, setFlyTarget] = useState(null);
  const [reportState, setReportState] = useState(IDLE);
  const [selectedVariable, setSelectedVariable] = useState(defaults.variable || null);
  const [timeseriesState, setTimeseriesState] = useState(IDLE);
  const [retryNonce, setRetryNonce] = useState(0);
  const reportAbort = useRef(null);
  const timeseriesAbort = useRef(null);

  const activeLayer = layers?.layers?.[selectedLayerId] || layers?.layers?.[layerIds[0]];
  const placesAvailable = Boolean(health?.places_available);

  useEffect(() => {
    writeUrlState({
      place: selection?.type === "place" ? selection.placeId : null,
      point: selection?.type === "point" ? selection.point : null,
      level: selectLevel,
      variable: selectedVariable,
      layer: selectedLayerId,
    });
  }, [selection, selectLevel, selectedVariable, selectedLayerId]);

  // Load report for current selection
  useEffect(() => {
    reportAbort.current?.abort();
    timeseriesAbort.current?.abort();
    if (!selection) {
      setReportState(IDLE);
      setTimeseriesState(IDLE);
      return undefined;
    }
    const controller = new AbortController();
    reportAbort.current = controller;
    setReportState({ status: "loading", data: null, error: null });
    if (!selectedVariable) setTimeseriesState(IDLE);

    const promise =
      selection.type === "place"
        ? api.placeReport(selection.placeId, { signal: controller.signal })
        : api.report(selection.point.lat, selection.point.lon, 5, { signal: controller.signal });

    promise
      .then((data) => {
        setReportState({ status: "ready", data, error: null });
        setSelectedVariable((previous) => {
          if (previous && data.variables?.some((row) => row.key === previous)) return previous;
          return data.variables?.[0]?.key || null;
        });
      })
      .catch((error) => {
        if (error?.name === "AbortError") return;
        setReportState({ status: "error", data: null, error: error?.message || "Unknown API error." });
      });
    return () => controller.abort();
  }, [selection, retryNonce]);

  // Load timeseries for selected variable
  useEffect(() => {
    timeseriesAbort.current?.abort();
    if (!selection || !selectedVariable) {
      setTimeseriesState(IDLE);
      return undefined;
    }
    const controller = new AbortController();
    timeseriesAbort.current = controller;
    setTimeseriesState({ status: "loading", data: null, error: null });

    const promise =
      selection.type === "place"
        ? api.placeTimeseries(selection.placeId, selectedVariable, { signal: controller.signal })
        : api.timeseries(selection.point.lat, selection.point.lon, selectedVariable, { signal: controller.signal });

    promise
      .then((data) => setTimeseriesState({ status: "ready", data, error: null }))
      .catch((error) => {
        if (error?.name === "AbortError") return;
        setTimeseriesState({ status: "error", data: null, error: error?.message || "Unknown API error." });
      });
    return () => controller.abort();
  }, [selection, selectedVariable]);

  const selectPlace = useCallback((place, options = {}) => {
    if (!place?.id) return;
    setSelection({ type: "place", placeId: place.id, meta: place });
    const c = place.centroid;
    if (options.fly && c) {
      setFlyTarget({ lat: c[1], lon: c[0], zoom: options.zoom || 3.6, nonce: Date.now() });
    }
  }, []);

  const selectPoint = useCallback((point, options = {}) => {
    const normalized = { lat: point.lat, lon: normalizeLon(point.lon), label: point.label || null };
    setSelection({ type: "point", point: normalized });
    if (options.fly) {
      setFlyTarget({ lat: normalized.lat, lon: normalized.lon, zoom: options.zoom || 3.6, nonce: Date.now() });
    }
  }, []);

  // Map click: resolve to place at selected level when available, else point
  const onMapSelect = useCallback(
    async (point, options = {}) => {
      if (!placesAvailable) {
        selectPoint(point, options);
        return;
      }
      try {
        const resolved = await api.placesAt(point.lat, point.lon, selectLevel);
        if (resolved?.place?.id) {
          selectPlace(resolved.place, options);
          return;
        }
        if (resolved?.open_ocean) {
          // keep point context but show open ocean message via point report fallback
          selectPoint({ ...point, label: resolved.label || "Open ocean" }, options);
          return;
        }
      } catch {
        // fall back to point
      }
      selectPoint(point, options);
    },
    [placesAvailable, selectLevel, selectPlace, selectPoint],
  );

  const onSearchSelect = useCallback(
    (item, options = {}) => {
      if (item?.type === "place" && item.placeId) {
        selectPlace({ id: item.placeId, centroid: [item.lon, item.lat], name: item.label, ...item.place }, options);
      } else {
        onMapSelect({ lat: item.lat, lon: item.lon, label: item.label || null }, options);
      }
    },
    [onMapSelect, selectPlace],
  );

  function changeLayer(id) {
    if (layers?.layers?.[id]) setSelectedLayerId(id);
  }

  const retry = useCallback(() => setRetryNonce((v) => v + 1), []);
  const selectedForMap = selection?.type === "point" ? selection.point : (reportState.data?.place?.centroid ? { lat: reportState.data.place.centroid[1], lon: reportState.data.place.centroid[0] } : null);

  return (
    <div className="explorer">
      <div className="map-column">
        <WorldMap
          layer={activeLayer}
          opacity={opacity}
          selected={selectedForMap}
          flyTarget={flyTarget}
          synthetic={health?.synthetic}
          onSelect={onMapSelect}
          selectLevel={selectLevel}
        >
          <div className="map-overlay map-overlay--search">
            <SearchControl onSelect={onSearchSelect} placesAvailable={placesAvailable} selectLevel={selectLevel} />
          </div>
          <div className="map-overlay map-overlay--layers">
            <div className="panel panel--compact" style={{ marginBottom: 8 }}>
              <div className="field-label">Select by</div>
              <div role="radiogroup" aria-label="Select by place level" style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                {LEVELS.map((l) => (
                  <label key={l.id} className={`chip ${selectLevel === l.id ? "chip--active" : ""}`} style={{ cursor: "pointer" }}>
                    <input
                      type="radio"
                      name="select-level"
                      value={l.id}
                      checked={selectLevel === l.id}
                      onChange={() => setSelectLevel(l.id)}
                      style={{ position: "absolute", opacity: 0 }}
                    />
                    {l.label}
                  </label>
                ))}
              </div>
              {!placesAvailable && <p className="field-help">Place gazetteer unavailable; clicking selects a grid point.</p>}
            </div>
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
        <ReportPanel
          selected={selectedForMap}
          selection={selection}
          report={reportState.data}
          loading={reportState.status === "loading"}
          error={reportState.error}
          onRetry={retry}
          selectedVariable={selectedVariable}
          onSelectVariable={setSelectedVariable}
          timeseries={timeseriesState.data}
          timeseriesLoading={timeseriesState.status === "loading"}
          timeseriesError={timeseriesState.error}
          layerId={selectedLayerId}
        />
      </aside>
    </div>
  );
}
