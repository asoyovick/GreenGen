import { apiUrl, config } from "../config.js";

export class ApiError extends Error {
  constructor(message, { status = 0, code = null, details = null, body = null, data = null, cause = null } = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
    this.body = body;
    this.data = data ?? body;
    this.cause = cause;
  }
}

function withTimeout(signal, timeoutMs) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(new DOMException("Request timed out", "AbortError")), timeoutMs);
  const onAbort = () => controller.abort(signal?.reason);
  if (signal) {
    if (signal.aborted) controller.abort(signal.reason);
    else signal.addEventListener("abort", onAbort, { once: true });
  }
  return {
    signal: controller.signal,
    cleanup: () => {
      clearTimeout(timer);
      if (signal) signal.removeEventListener("abort", onAbort);
    },
  };
}

export async function request(path, { method = "GET", params, body, headers = {}, signal, timeoutMs = config.requestTimeoutMs } = {}) {
  const url = new URL(apiUrl(path), window.location.origin);
  if (params && typeof params === "object") {
    for (const [k, v] of Object.entries(params)) {
      if (v == null || v === "") continue;
      url.searchParams.set(k, String(v));
    }
  }
  const init = { method, headers: { Accept: "application/json", ...headers }, signal: undefined };
  if (body != null) {
    init.headers["Content-Type"] = init.headers["Content-Type"] || "application/json";
    init.body = typeof body === "string" ? body : JSON.stringify(body);
  }
  const t = withTimeout(signal, timeoutMs);
  init.signal = t.signal;

  let res;
  try {
    res = await fetch(url, init);
  } catch (err) {
    t.cleanup();
    if (err?.name === "AbortError") throw new ApiError("The request was cancelled or timed out.", { status: 0, code: "ABORTED", cause: err });
    throw new ApiError("Unable to reach the backend API. Check that the server is running and the API base URL is configured.", { status: 0, code: "NETWORK_ERROR", cause: err });
  }
  t.cleanup();

  const contentType = res.headers.get("content-type") || "";
  let payload = null;
  if (res.status !== 204) {
    if (contentType.includes("application/json")) {
      try { payload = await res.json(); } catch { payload = null; }
    } else {
      try { payload = await res.text(); } catch { payload = null; }
    }
  }

  if (!res.ok) {
    const detail = payload?.error || payload?.detail || payload;
    const message = (typeof detail === "string" && detail) ||
      detail?.message || (typeof payload?.detail === "string" && payload.detail) ||
      `Request failed with HTTP ${res.status}.`;
    const code = detail?.code || payload?.code || null;
    const details = detail?.details || payload?.details || payload?.issues || null;
    throw new ApiError(message, { status: res.status, code, details, body: payload, data: payload });
  }
  return payload;
}

export function get(path, opts) { return request(path, { ...opts, method: "GET" }); }
export function post(path, body, opts) { return request(path, { ...opts, method: "POST", body }); }

export function isNotFound(err) { return err instanceof ApiError && err.status === 404; }
export function isUnavailable(err) { return err instanceof ApiError && (err.status === 503 || err.status === 501 || err.status === 0); }
