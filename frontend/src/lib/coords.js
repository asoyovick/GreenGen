/**
 * Parse a coordinate typed by a person. Supports decimal degrees and simple
 * degrees/minutes/seconds, with N/S and E/W hemispheres. Longitude may be
 * given as 0..360 and is normalized to -180..180.
 */

const HEMISPHERE = /^([NSEW])$/i;

function decimalPart(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return null;
  return n;
}

function parseDms(parts, hemisphere) {
  const [deg, min = 0, sec = 0] = parts.map(decimalPart);
  if (deg === null || min === null || sec === null) return null;
  if (deg < 0 || min < 0 || sec < 0 || min >= 60 || sec >= 60) return null;
  let value = Math.abs(deg) + min / 60 + sec / 3600;
  if (hemisphere) {
    if (/[SW]/i.test(hemisphere)) value *= -1;
  } else if (String(parts[0]).startsWith("-")) {
    value *= -1;
  }
  return value;
}

export function normalizeLon(lon) {
  let value = Number(lon);
  if (!Number.isFinite(value)) return null;
  value = ((((value + 180) % 360) + 360) % 360) - 180;
  return value === -180 && lon > 0 ? 180 : value;
}

export function parseCoordinateInput(raw) {
  if (typeof raw !== "string" || !raw.trim()) return null;
  const text = raw
    .trim()
    .replace(/[−–—]/g, "-")
    .replace(/,/g, " ")
    .replace(/\s+/g, " ")
    .toUpperCase();

  // Decimal degrees: "55.5 N 70.2 E", "55.5, -70.2", "55.5 -70.2".
  const decimal = text.match(
    /^([+-]?\d+(?:\.\d+)?)\s*°?\s*([NS])?\s+([+-]?\d+(?:\.\d+)?)\s*°?\s*([EW])?$/,
  );
  if (decimal) {
    let lat = Number(decimal[1]);
    let lon = Number(decimal[3]);
    if (decimal[2] === "S") lat = -Math.abs(lat);
    if (decimal[4] === "W") lon = -Math.abs(lon);
    if (decimal[4] === "E") lon = Math.abs(lon);
    lon = normalizeLon(lon);
    return validate(lat, lon);
  }

  // Degrees, minutes and seconds: "55°45'00\"N 37°37'00\"E".
  const dms = text.match(
    /^(\d+(?:\.\d+)?)\s*°?\s*(\d+(?:\.\d+)?)?\s*['′]?\s*(\d+(?:\.\d+)?)?\s*["″]?\s*([NS])\s+(\d+(?:\.\d+)?)\s*°?\s*(\d+(?:\.\d+)?)?\s*['′]?\s*(\d+(?:\.\d+)?)?\s*["″]?\s*([EW])$/,
  );
  if (dms) {
    const lat = parseDms([dms[1], dms[2], dms[3]], dms[4]);
    const lon = normalizeLon(parseDms([dms[5], dms[6], dms[7]], dms[8]));
    return validate(lat, lon);
  }

  // Bare pair with an explicit sign or hemisphere is required; this avoids
  // silently treating a place name such as "Paris 2024" as coordinates.
  const bare = text.match(
    /^([+-]\d+(?:\.\d+)?)\s+([+-]\d+(?:\.\d+)?)$/,
  );
  if (bare) return validate(Number(bare[1]), normalizeLon(Number(bare[2])));

  return null;
}

export function validate(lat, lon) {
  if (lat === null || lon === null) return null;
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) return null;
  if (lat < -90 || lat > 90) return null;
  if (lon < -180 || lon > 180) return null;
  return { lat, lon };
}

export function coordLabel(lat, lon) {
  const ns = lat >= 0 ? "N" : "S";
  const ew = lon >= 0 ? "E" : "W";
  return `${Math.abs(lat).toFixed(2)}°${ns}, ${Math.abs(lon).toFixed(2)}°${ew}`;
}
