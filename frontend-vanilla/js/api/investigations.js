import { get, isNotFound, isUnavailable } from "./client.js";
import { config } from "../config.js";

// Integrates with planned Go backend contract (/api/v1) and falls back to
// current prototype read-only endpoints where possible. Never fabricates data.

function withPrefix(prefix, path) {
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${prefix}${p}`;
}

export async function getApiHealth(opts = {}) {
  // Prototype: GET /api/health
  return get(withPrefix(config.apiPrefix, "/health"), opts);
}

export async function listInvestigations(opts = {}) {
  // Planned: GET /api/v1/investigations
  try {
    return await get(withPrefix(config.contractApiPrefix, "/investigations"), opts);
  } catch (err) {
    if (!isNotFound(err) && !isUnavailable(err)) throw err;
  }
  // Fallback: derive catalogue from prototype variables/layers (precomputed explorer), clearly not execution-based investigations.
  const [health, variables] = await Promise.all([
    get(withPrefix(config.apiPrefix, "/health"), opts).catch(() => null),
    get(withPrefix(config.apiPrefix, "/variables"), opts).catch(() => null),
  ]);
  const vars = variables?.variables || variables || [];
  const mode = health?.mode || "unknown";
  return {
    source: "prototype",
    note: "Investigation management API is not available; showing available variables from the current prototype (no synthetic data used).",
    investigations: Array.isArray(vars) ? vars.filter(v => !(v.synthetic || health?.synthetic)).map((v) => ({
      id: v.key || v.id || v.name,
      title: v.display_name || v.name || v.key,
      question: v.description || "How has this variable changed over time in the selected area?",
      variables: [v.key || v.id].filter(Boolean),
      dataset: { name: v.dataset || v.short_name || v.source || "Dataset", model_based: !!v.model_based },
      coverage: { spatial: v.surface || null, temporal: v.period || health?.period || null },
      availability: "available_precomputed",
      units: v.units || v.units_out || null,
      mode,
    })) : [],
  };
}

export async function getInvestigation(id, opts = {}) {
  try {
    return await get(withPrefix(config.contractApiPrefix, `/investigations/${encodeURIComponent(id)}`), opts);
  } catch (err) {
    if (!isNotFound(err) && !isUnavailable(err)) throw err;
  }
  const list = await listInvestigations(opts);
  const items = list?.investigations || list || [];
  const found = Array.isArray(items) ? items.find((x) => String(x.id) === String(id)) : null;
  if (!found) throw errIfMissing(id);
  return { source: list.source || "prototype", investigation: found };
}

function errIfMissing(id) {
  const e = new Error(`Investigation not found: ${id}`);
  e.status = 404;
  return e;
}
