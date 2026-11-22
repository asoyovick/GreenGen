const BASE = (import.meta.env.VITE_API_BASE || "").replace(/\/+$/, "");
const V1_BASE = (import.meta.env.VITE_BACKEND_BASE || import.meta.env.VITE_API_BASE || "").replace(/\/+$/, "");

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request(path, params = {}, { signal } = {}) {
  const url = new URL(`${BASE}${path}`, window.location.origin);
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== "") {
      url.searchParams.set(key, String(value));
    }
  }

  let response;
  try {
    response = await fetch(url, {
      headers: { Accept: "application/json" },
      signal,
    });
  } catch (error) {
    if (error?.name === "AbortError") throw error;
    throw new ApiError(
      "Cannot reach the Global Change Explorer API. Start it with `make api` (or `make demo`) and retry.",
      0,
    );
  }

  if (!response.ok) {
    let detail = `Request failed with HTTP ${response.status}.`;
    try {
      const body = await response.json();
      if (body?.detail) {
        detail =
          typeof body.detail === "string"
            ? body.detail
            : JSON.stringify(body.detail);
      }
    } catch {
      // Keep the HTTP status message when the body is not JSON.
    }
    throw new ApiError(detail, response.status);
  }
  return response.json();
}

async function requestV1(path, { method = "GET", params = {}, body, signal, headers = {} } = {}) {
  const url = new URL(`${V1_BASE}${path}`, window.location.origin);
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== "") url.searchParams.set(key, String(value));
  }
  let response;
  try {
    response = await fetch(url, {
      method,
      headers: { Accept: "application/json", ...(body ? { "Content-Type": "application/json" } : {}), ...headers },
      body: body ? JSON.stringify(body) : undefined,
      signal,
    });
  } catch (error) {
    if (error?.name === "AbortError") throw error;
    throw new ApiError("Cannot reach the GreenGen backend API. Check VITE_BACKEND_BASE / backend server.", 0);
  }
  const text = await response.text();
  let data = null;
  try { data = text ? JSON.parse(text) : null; } catch { data = text; }
  if (!response.ok) {
    const detail = data?.error?.message || data?.detail || `Request failed with HTTP ${response.status}.`;
    const err = new ApiError(typeof detail === "string" ? detail : JSON.stringify(detail), response.status);
    err.data = data;
    throw err;
  }
  return data;
}

export const api = {
  health: () => request("/api/health"),
  variables: () => request("/api/variables"),
  layers: () => request("/api/layers"),
  report: (lat, lon, window = 5, options = {}) =>
    request("/api/report", { lat, lon, window }, options),
  timeseries: (lat, lon, variable, options = {}) =>
    request("/api/timeseries", { lat, lon, variable }, options),
  placesSearch: (q, level, limit = 10, options = {}) =>
    request("/api/places/search", { q, level, limit }, options),
  placesAt: (lat, lon, level = "region", options = {}) =>
    request("/api/places/at", { lat, lon, level }, options),
  place: (placeId, options = {}) => request(`/api/places/${encodeURIComponent(placeId)}`, {}, options),
  placeReport: (placeId, options = {}) =>
    request("/api/report", { place_id: placeId }, options),
  placeTimeseries: (placeId, variable, options = {}) =>
    request(`/api/places/${encodeURIComponent(placeId)}/timeseries`, { variable }, options),
  placeLayerUrl: (level) => `${BASE}/api/places/layer/${encodeURIComponent(level)}`,

  // Backend v1 contract-aligned client (Issues #46,#47,#48)
  v1: {
    health: (options = {}) => requestV1("/api/v1/health", options),
    investigations: (options = {}) => requestV1("/api/v1/investigations", options),
    investigation: (id, options = {}) => requestV1(`/api/v1/investigations/${encodeURIComponent(id)}`, options),
    validateExecution: (body, options = {}) => requestV1("/api/v1/executions/validate", { method: "POST", body, ...options }),
    submitExecution: (body, options = {}) => requestV1("/api/v1/executions", { method: "POST", body, ...options }),
    execution: (id, options = {}) => requestV1(`/api/v1/executions/${encodeURIComponent(id)}`, options),
    refreshExecution: (id, options = {}) => requestV1(`/api/v1/executions/${encodeURIComponent(id)}/refresh`, { method: "POST", ...options }),
    results: (id, params = {}, options = {}) => requestV1(`/api/v1/executions/${encodeURIComponent(id)}/results`, { params, ...options }),
    summary: (id, options = {}) => requestV1(`/api/v1/executions/${encodeURIComponent(id)}/summary`, options),
    cell: (id, cellId, options = {}) => requestV1(`/api/v1/executions/${encodeURIComponent(id)}/cells/${encodeURIComponent(cellId)}`, options),
    report: (id, options = {}) => requestV1(`/api/v1/executions/${encodeURIComponent(id)}/report`, options),
  },
};
