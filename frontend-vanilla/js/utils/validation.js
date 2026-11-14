export function parseISODate(s) {
  if (!s || !/^\d{4}-\d{2}-\d{2}$/.test(s)) return null;
  const d = new Date(`${s}T00:00:00Z`);
  return Number.isNaN(d.getTime()) ? null : d;
}

export function validateDateRange(startStr, endStr, { min, max } = {}) {
  const errors = [];
  const start = parseISODate(startStr);
  const end = parseISODate(endStr);
  if (!start) errors.push({ field: "start", message: "A valid start date is required (YYYY-MM-DD)." });
  if (!end) errors.push({ field: "end", message: "A valid end date is required (YYYY-MM-DD)." });
  if (start && end && start > end) errors.push({ field: "range", message: "Start date must be on or before end date." });
  if (start && min) { const dmin = parseISODate(min) || new Date(min); if (!Number.isNaN(dmin) && start < dmin) errors.push({ field: "start", message: `Start date must be on or after ${min}.` }); }
  if (end && max) { const dmax = parseISODate(max) || new Date(max); if (!Number.isNaN(dmax) && end > dmax) errors.push({ field: "end", message: `End date must be on or before ${max}.` }); }
  return { valid: errors.length === 0, errors, start, end };
}

export function validateLatLon(lat, lon) {
  const la = Number(lat), lo = Number(lon);
  const errors = [];
  if (!Number.isFinite(la) || la < -90 || la > 90) errors.push({ field: "lat", message: "Latitude must be between -90 and 90." });
  if (!Number.isFinite(lo) || lo < -180 || lo > 180) errors.push({ field: "lon", message: "Longitude must be between -180 and 180." });
  return { valid: errors.length === 0, errors, lat: la, lon: lo };
}

export function summarizeErrors(errors = []) {
  return errors.map((e) => e.message).filter(Boolean).join(" ");
}
