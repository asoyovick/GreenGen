import { useEffect, useRef, useState } from "react";
import {
  AttributionControl,
  Map as MapLibreMap,
  Marker,
  NavigationControl,
  ScaleControl,
  setWorkerUrl,
} from "maplibre-gl";
import workerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?url";
import { buildGraticule, imageCoordinates } from "../lib/geo.js";

setWorkerUrl(workerUrl);

const BASE = import.meta.env.BASE_URL || "/";
const LAND_URL = `${BASE}data/land.geojson`;

function baseStyle() {
  return {
    version: 8,
    sources: {
      land: {
        type: "geojson",
        data: LAND_URL,
      },
      graticule: {
        type: "geojson",
        data: buildGraticule(30),
      },
    },
    layers: [
      {
        id: "background",
        type: "background",
        paint: { "background-color": "#0a2330" },
      },
      {
        id: "land-fill",
        type: "fill",
        source: "land",
        paint: {
          "fill-color": "#173a2f",
          "fill-opacity": 0.95,
        },
      },
      {
        id: "graticule",
        type: "line",
        source: "graticule",
        paint: {
          "line-color": "#7fa79a",
          "line-opacity": 0.18,
          "line-width": 0.7,
        },
      },
      {
        id: "land-outline",
        type: "line",
        source: "land",
        paint: {
          "line-color": "#6ea28e",
          "line-opacity": 0.55,
          "line-width": 0.65,
        },
      },
    ],
  };
}

export default function WorldMap({
  layer,
  opacity = 0.82,
  selected,
  flyTarget,
  synthetic = false,
  onSelect,
  children,
}) {
  const containerRef = useRef(null);
  const mapRef = useRef(null);
  const markerRef = useRef(null);
  const onSelectRef = useRef(onSelect);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState(null);

  onSelectRef.current = onSelect;

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return undefined;

    const map = new MapLibreMap({
      container: containerRef.current,
      style: baseStyle(),
      center: [18, 24],
      zoom: 1.35,
      minZoom: 1,
      maxZoom: 8,
      renderWorldCopies: true,
      attributionControl: false,
    });
    mapRef.current = map;

    map.addControl(
      new NavigationControl({ showCompass: false }),
      "top-right",
    );
    map.addControl(new ScaleControl({ unit: "metric" }), "bottom-right");
    map.addControl(
      new AttributionControl({
        compact: true,
        customAttribution:
          'Base map: <a href="https://www.naturalearthdata.com/">Natural Earth</a> (public domain) · Overlays: Global Change Explorer',
      }),
      "bottom-right",
    );

    map.on("load", () => {
      map.getCanvas().style.cursor = "crosshair";
      setReady(true);
    });

    map.on("click", (event) => {
      const handler = onSelectRef.current;
      if (!handler) return;
      handler({
        lat: event.lngLat.lat,
        lon: event.lngLat.lng,
      });
    });

    map.on("error", (event) => {
      const message = event?.error?.message || "The basemap or overlay failed to load.";
      if (!map.isStyleLoaded()) setError(message);
    });

    const observer = new ResizeObserver(() => map.resize());
    observer.observe(containerRef.current);

    return () => {
      observer.disconnect();
      markerRef.current?.remove();
      markerRef.current = null;
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready || !layer) return;
    const coordinates = imageCoordinates(layer.bounds);
    const source = map.getSource("overlay");
    if (source) {
      source.updateImage({ url: layer.url, coordinates });
    } else {
      map.addSource("overlay", {
        type: "image",
        url: layer.url,
        coordinates,
      });
      map.addLayer({
        id: "overlay",
        type: "raster",
        source: "overlay",
        paint: {
          "raster-opacity": opacity,
          "raster-fade-duration": 0,
          "raster-resampling": "linear",
        },
      });
    }
    setError(null);
  }, [layer, ready]); // opacity handled separately

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready || !map.getLayer("overlay")) return;
    map.setPaintProperty("overlay", "raster-opacity", opacity);
  }, [opacity, ready]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    if (!selected) {
      markerRef.current?.remove();
      markerRef.current = null;
      return;
    }
    if (!markerRef.current) {
      const element = document.createElement("div");
      element.className = "map-marker";
      element.setAttribute("aria-hidden", "true");
      markerRef.current = new Marker({ element, anchor: "center" })
        .setLngLat([selected.lon, selected.lat])
        .addTo(map);
    } else {
      markerRef.current.setLngLat([selected.lon, selected.lat]);
    }
  }, [selected, ready]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready || !flyTarget) return;
    map.flyTo({
      center: [flyTarget.lon, flyTarget.lat],
      zoom: flyTarget.zoom || 3.6,
      duration: 1100,
      essential: true,
    });
  }, [flyTarget, ready]);

  return (
    <div className="map-shell">
      <div
        ref={containerRef}
        className="map"
        role="application"
        aria-label="World map. Click a location to build a change report, or use the place search and coordinate entry for keyboard access."
      />
      {!ready && (
        <div className="map-status" role="status" aria-live="polite">
          <div>
            <div className="spinner" aria-hidden="true" />
            <p>Loading the offline base map…</p>
          </div>
        </div>
      )}
      {error && (
        <div className="map-status" role="alert">
          <div>
            <strong>Map layer problem</strong>
            <p>{error}</p>
          </div>
        </div>
      )}
      {synthetic && (
        <div className="map-note" aria-hidden="true">
          SYNTHETIC DEMO DATA · not observations
        </div>
      )}
      {children}
    </div>
  );
}
