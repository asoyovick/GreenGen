// Central configuration for API integration.
// Do not hardcode backend URLs in feature modules.
// Override by setting window.GREENGEN_CONFIG before loading modules, or via meta tags in HTML.

const meta = (name) => document.querySelector(`meta[name="${name}"]`)?.content?.trim();

const defaults = {
  // Target Go backend (draft contract, /api/v1). Falls back to current prototype /api when unavailable.
  apiBaseUrl: meta("greengen-api-base") || "",
  apiPrefix: meta("greengen-api-prefix") || "/api",
  contractApiPrefix: "/api/v1",
  requestTimeoutMs: 30000,
  pollIntervalMs: 4000,
  map: {
    defaultCenter: [37.9062, 0.0236], // [lon, lat] Kenya centroid (initial focus)
    defaultZoom: 5.2,
    styleUrl: meta("greengen-map-style") || "https://demotiles.maplibre.org/style.json",
  },
  charts: {
    defaultHeight: 320,
  },
};

export const config = Object.freeze({
  ...defaults,
  ...(window.GREENGEN_CONFIG || {}),
});

export function apiUrl(path = "") {
  const base = config.apiBaseUrl.replace(/\/+$/, "");
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${base}${p}`;
}
