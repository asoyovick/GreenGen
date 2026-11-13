import { validate } from "./coords.js";

export function readUrlState(layerIds = []) {
  if (typeof window === "undefined") return {};
  const params = new URLSearchParams(window.location.search);
  const lat = params.has("lat") ? Number(params.get("lat")) : null;
  const lon = params.has("lon") ? Number(params.get("lon")) : null;
  const point =
    lat !== null && lon !== null ? validate(lat, lon) : null;
  const layer = params.get("layer");
  return {
    point,
    layer: layer && (layerIds.length === 0 || layerIds.includes(layer)) ? layer : null,
  };
}

export function writeUrlState({ point, layer } = {}) {
  if (typeof window === "undefined") return;
  const url = new URL(window.location.href);
  if (point) {
    url.searchParams.set("lat", Number(point.lat).toFixed(4));
    url.searchParams.set("lon", Number(point.lon).toFixed(4));
  } else {
    url.searchParams.delete("lat");
    url.searchParams.delete("lon");
  }
  if (layer) url.searchParams.set("layer", layer);
  else url.searchParams.delete("layer");
  window.history.replaceState({}, "", url);
}
