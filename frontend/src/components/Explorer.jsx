import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import LayerLegend from "./LayerLegend.jsx";
import LayerSwitcher from "./LayerSwitcher.jsx";
import ReportPanel from "./ReportPanel.jsx";
import WorldMap from "./WorldMap.jsx";
import { api } from "../api.js";
import { normalizeLon } from "../lib/coords.js";
import { readUrlState, writeUrlState } from "../lib/url.js";

const IDLE = { status: "idle", data: null, error: null };

export default function Explorer({ health, layers }) {
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
  const [reportState, setReportState] = useState(IDLE);
  const [selectedVariable, setSelectedVariable] = useState(null);
  const [timeseriesState, setTimeseriesState] = useState(IDLE);
  const [retryNonce, setRetryNonce] = useState(0);
  const reportAbort = useRef(null);
  const timeseriesAbort = useRef(null);

  const activeLayer =
    layers?.layers?.[selectedLayerId] || layers?.layers?.[layerIds[0]];

  useEffect(() => {
    writeUrlState({ point: selected, layer: selectedLayerId });
  }, [selected, selectedLayerId]);

  useEffect(() => {
    reportAbort.current?.abort();
    timeseriesAbort.current?.abort();
    if (!selected) {
      setReportState(IDLE);
      setSelectedVariable(null);
      setTimeseriesState(IDLE);
      return undefined;
    }

    const controller = new AbortController();
    reportAbort.current = controller;
    setReportState({ status: "loading", data: null, error: null });
    setSelectedVariable(null);
    setTimeseriesState(IDLE);

    api
      .report(selected.lat, selected.lon, 5, { signal: controller.signal })
      .then((data) => {
        setReportState({ status: "ready", data, error: null });
        setSelectedVariable((previous) => {
          if (data.variables.some((row) => row.key === previous)) return previous;
          return data.variables[0]?.key || null;
        });
      })
      .catch((error) => {
        if (error?.name === "AbortError") return;
        setReportState({
          status: "error",
          data: null,
          error: error?.message || "Unknown API error.",
        });
      });

    return () => controller.abort();
  }, [selected, retryNonce]);

  useEffect(() => {
    timeseriesAbort.current?.abort();
    if (!selected || !selectedVariable) {
      setTimeseriesState(IDLE);
      return undefined;
    }

    const controller = new AbortController();
    timeseriesAbort.current = controller;
    setTimeseriesState({ status: "loading", data: null, error: null });

    api
      .timeseries(selected.lat, selected.lon, selectedVariable, {
        signal: controller.signal,
      })
      .then((data) => {
        setTimeseriesState({ status: "ready", data, error: null });
      })
      .catch((error) => {
        if (error?.name === "AbortError") return;
        setTimeseriesState({
          status: "error",
          data: null,
          error: error?.message || "Unknown API error.",
        });
      });

    return () => controller.abort();
  }, [selected, selectedVariable]);

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

  const retry = useCallback(() => setRetryNonce((value) => value + 1), []);

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
        <ReportPanel
          selected={selected}
          report={reportState.data}
          loading={reportState.status === "loading"}
          error={reportState.error}
          onRetry={retry}
          selectedVariable={selectedVariable}
          onSelectVariable={setSelectedVariable}
          timeseries={timeseriesState.data}
          timeseriesLoading={timeseriesState.status === "loading"}
          timeseriesError={timeseriesState.error}
        />
      </aside>
    </div>
  );
}
