import { get, post, isNotFound, isUnavailable } from "./client.js";
import { config } from "../config.js";

function withPrefix(prefix, path) {
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${prefix}${p}`;
}

// Planned execution endpoints (draft). If unavailable, callers must show clear
// unavailable state — never simulate success.

export async function submitExecution(payload, opts = {}) {
  return post(withPrefix(config.contractApiPrefix, "/executions"), payload, opts);
}

export async function getExecutionStatus(executionId, opts = {}) {
  return get(withPrefix(config.contractApiPrefix, `/executions/${encodeURIComponent(executionId)}`), opts);
}

export async function getExecutionResults(executionId, params = {}, opts = {}) {
  return get(withPrefix(config.contractApiPrefix, `/executions/${encodeURIComponent(executionId)}/results`), { ...opts, params });
}

export async function getExecutionSummary(executionId, opts = {}) {
  return get(withPrefix(config.contractApiPrefix, `/executions/${encodeURIComponent(executionId)}/summary`), opts);
}

export async function getCellDetails(executionId, cellId, opts = {}) {
  return get(withPrefix(config.contractApiPrefix, `/executions/${encodeURIComponent(executionId)}/cells/${encodeURIComponent(cellId)}`), opts);
}

export async function refreshExecutionStatus(executionId, opts = {}) {
  return post(withPrefix(config.contractApiPrefix, `/executions/${encodeURIComponent(executionId)}/refresh`), {}, opts);
}

// Prototype-compatible read helpers (precomputed point/place reports/timeseries/layers)
export async function getLayers(opts = {}) {
  return get(withPrefix(config.apiPrefix, "/layers"), opts);
}
export async function getVariables(opts = {}) {
  return get(withPrefix(config.apiPrefix, "/variables"), opts);
}
export async function getPointReport(lat, lon, window = 5, opts = {}) {
  return get(withPrefix(config.apiPrefix, "/report"), { ...opts, params: { lat, lon, window } });
}
export async function getPointTimeseries(lat, lon, variable, opts = {}) {
  return get(withPrefix(config.apiPrefix, "/timeseries"), { ...opts, params: { lat, lon, variable } });
}

export function isEndpointMissing(err) {
  return isNotFound(err) || isUnavailable(err) || err?.status === 501;
}

export function isResultsUnavailable(err) {
  const code = err?.data?.error?.code || err?.code;
  return err?.status === 409 || /UNAVAILABLE/i.test(String(code || ""));
}
