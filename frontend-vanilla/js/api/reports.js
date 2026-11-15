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
    const code = err?.data?.error?.code || err?.code;
    if (isNotFound(err) || isUnavailable(err) || err?.status === 501 || err?.status === 409 || /UNAVAILABLE/i.test(String(code || ""))) {
      return { available: false, reason: err?.data?.error?.message || "Report is not available on the connected backend.", executionId, details: err?.data?.error?.details || err?.data };
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
    const code = err?.data?.error?.code || err?.code;
    if (isNotFound(err) || isUnavailable(err) || err?.status === 501 || err?.status === 409 || /UNAVAILABLE/i.test(String(code || ""))) {
      const e = new Error(err?.data?.error?.message || "Report export is not supported by the connected backend.");
      e.code = "EXPORT_UNAVAILABLE";
      e.details = err?.data;
      throw e;
    }
    throw err;
  }
}
