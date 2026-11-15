const number = new Intl.NumberFormat("en", {
  maximumSignificantDigits: 3,
});

const compactNumber = new Intl.NumberFormat("en", {
  maximumSignificantDigits: 3,
  notation: "compact",
});

export const SYNTHETIC_WARNING = "SYNTHETIC DEMO DATA, not real observations.";
export const NOT_A_FORECAST = "Observed change only, not a forecast.";

export function unitLabel(unit) {
  if (!unit) return "";
  if (unit === "degC") return "°C";
  return unit;
}

export function formatNumber(value, { compact = false } = {}) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "—";
  }
  const n = Number(value);
  if (compact && Math.abs(n) >= 1000) return compactNumber.format(n);
  if (Math.abs(n) > 0 && (Math.abs(n) < 0.001 || Math.abs(n) >= 100000)) {
    return n.toExponential(2);
  }
  return number.format(n);
}

export function formatRate(value, unit) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "No rate available";
  }
  const n = Number(value);
  const sign = n > 0 ? "+" : n < 0 ? "−" : "±";
  return `${sign}${formatNumber(Math.abs(n))} ${unitLabel(unit)} per decade`;
}

export function formatSigned(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "—";
  }
  const n = Number(value);
  return `${n > 0 ? "+" : n < 0 ? "−" : "±"}${formatNumber(Math.abs(n))}`;
}

export function formatCoord(lat, lon, digits = 2) {
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) return "—";
  const ns = lat >= 0 ? "N" : "S";
  const ew = lon >= 0 ? "E" : "W";
  return `${Math.abs(lat).toFixed(digits)}°${ns}, ${Math.abs(lon).toFixed(digits)}°${ew}`;
}

export function shortCoord(lat, lon, digits = 1) {
  return `${lat.toFixed(digits)}, ${lon.toFixed(digits)}`;
}

export function verdictIcon(row) {
  if (!row?.significant) return "•";
  return row.class > 0 ? "↑" : "↓";
}

export function verdictText(row) {
  if (!row) return "No data";
  if (!row.significant) return "No significant change detected";
  return row.class > 0 ? "Significant increase" : "Significant decrease";
}

export function nearbyText(nearby) {
  if (!nearby) return "";
  const up = Math.round((nearby.up ?? 0) * 100);
  const down = Math.round((nearby.down ?? 0) * 100);
  return `${up}% of nearby cells increase, ${down}% decrease.`;
}

export function periodText(period) {
  if (!Array.isArray(period) || period.length < 2) return "";
  return `${period[0]} to ${period[1]}`;
}

export function downloadText(filename, text, type = "text/plain;charset=utf-8") {
  const blob = new Blob([text], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
