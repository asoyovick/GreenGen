import { get, isNotFound, isUnavailable } from "./client.js";
import { config } from "../config.js";

function withPrefix(prefix, path) {
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${prefix}${p}`;
}

export async function getExecutionReport(executionId, opts = {}) {
  try {
    return await get(withPrefix(config.contractApiPrefix, `/executions/${encodeURIComponent(executionId)}/report`), opts);
  } catch (err) {
    if (isNotFound(err) || isUnavailable(err) || err?.status === 501) {
      return { available: false, reason: "Report endpoint is not available on the connected backend.", executionId };
    }
    throw err;
  }
}

export async function exportExecutionReport(executionId, format = "json", opts = {}) {
  try {
    return await get(withPrefix(config.contractApiPrefix, `/executions/${encodeURIComponent(executionId)}/report`), {
      ...opts,
      params: { ...(opts.params || {}), format },
    });
  } catch (err) {
    if (isNotFound(err) || isUnavailable(err) || err?.status === 501) {
      const e = new Error("Report export is not supported by the connected backend.");
      e.code = "EXPORT_UNAVAILABLE";
      throw e;
    }
    throw err;
  }
}
