import { validate } from "./coords.js";

const LEVELS = new Set(["country", "region", "city", "sea"]);

export function readUrlState(layerIds = []) {
  if (typeof window === "undefined") return {};
  const params = new URLSearchParams(window.location.search);
  const lat = params.has("lat") ? Number(params.get("lat")) : null;
  const lon = params.has("lon") ? Number(params.get("lon")) : null;
  const point = lat !== null && lon !== null ? validate(lat, lon) : null;
  const layer = params.get("layer");
  const level = params.get("level");
  const place = params.get("place");
  const variable = params.get("var");
  return {
    point,
    place: place || null,
    level: LEVELS.has(level) ? level : null,
    variable: variable || null,
    layer: layer && (layerIds.length === 0 || layerIds.includes(layer)) ? layer : null,
  };
}

export function writeUrlState({ point, place, level, variable, layer } = {}) {
  if (typeof window === "undefined") return;
  const url = new URL(window.location.href);
  if (place) {
    url.searchParams.set("place", place);
    url.searchParams.delete("lat");
    url.searchParams.delete("lon");
  } else if (point) {
    url.searchParams.set("lat", Number(point.lat).toFixed(4));
    url.searchParams.set("lon", Number(point.lon).toFixed(4));
    url.searchParams.delete("place");
  } else {
    url.searchParams.delete("lat");
    url.searchParams.delete("lon");
    url.searchParams.delete("place");
  }
  if (level) url.searchParams.set("level", level);
  else url.searchParams.delete("level");
  if (variable) url.searchParams.set("var", variable);
  else url.searchParams.delete("var");
  if (layer) url.searchParams.set("layer", layer);
  else url.searchParams.delete("layer");
  window.history.replaceState({}, "", url);
}
