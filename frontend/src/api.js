const BASE = (import.meta.env.VITE_API_BASE || "").replace(/\/+$/, "");

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request(path, params = {}) {
  const url = new URL(`${BASE}${path}`, window.location.origin);
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== "") {
      url.searchParams.set(key, String(value));
    }
  }

  let response;
  try {
    response = await fetch(url, { headers: { Accept: "application/json" } });
  } catch {
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

export const api = {
  health: () => request("/api/health"),
  variables: () => request("/api/variables"),
  layers: () => request("/api/layers"),
  report: (lat, lon, window = 5) =>
    request("/api/report", { lat, lon, window }),
  timeseries: (lat, lon, variable) =>
    request("/api/timeseries", { lat, lon, variable }),
};
