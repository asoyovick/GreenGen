export function formatNumber(value, { digits = 3, fallback = "—" } = {}) {
  if (value == null || value === "" || Number.isNaN(Number(value))) return fallback;
  const n = Number(value);
  const abs = Math.abs(n);
  const opts = abs !== 0 && (abs >= 10000 || abs < 0.01)
    ? { notation: "scientific", maximumFractionDigits: Math.max(0, digits - 1) }
    : { maximumFractionDigits: digits };
  return new Intl.NumberFormat(undefined, opts).format(n);
}

export function formatDate(value, fallback = "—") {
  if (!value) return fallback;
  const d = value instanceof Date ? value : new Date(value);
  return Number.isNaN(d.getTime()) ? String(value) : d.toLocaleDateString();
}

export function formatDateTime(value, fallback = "—") {
  if (!value) return fallback;
  const d = value instanceof Date ? value : new Date(value);
  return Number.isNaN(d.getTime()) ? String(value) : d.toLocaleString();
}

export function formatPercent(value, { digits = 1, fallback = "—", fromFraction = false } = {}) {
  if (value == null || Number.isNaN(Number(value))) return fallback;
  const n = Number(value) * (fromFraction ? 100 : 1);
  return `${formatNumber(n, { digits })}%`;
}

export function titleCase(s) {
  return String(s || "").replace(/[_-]+/g, " ").replace(/\b\w/g, (m) => m.toUpperCase());
}

export function classificationLabel(key) {
  const map = {
    significant_increase: "Statistically significant increasing trend",
    significant_decrease: "Statistically significant decreasing trend",
    no_significant_trend: "No statistically significant trend detected",
    insufficient_data: "Insufficient data",
    inconclusive: "Inconclusive",
    unavailable: "Unavailable",
  };
  return map[key] || titleCase(key || "Unavailable");
}

export function statusLabel(status) {
  const map = {
    ready: "Ready",
    submitting: "Submitting",
    queued: "Queued",
    retrieving: "Retrieving data",
    retrieving_data: "Retrieving data",
    processing: "Processing",
    analysing: "Processing",
    analyzing: "Processing",
    completed: "Completed",
    failed: "Failed",
  };
  return map[status] || titleCase(status || "Unknown");
}
