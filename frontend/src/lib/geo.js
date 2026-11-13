/** Geographic helpers for the map layers. */

export function imageCoordinates(bounds) {
  const [west, south, east, north] = bounds || [-180, -85, 180, 85];
  return [
    [west, north],
    [east, north],
    [east, south],
    [west, south],
  ];
}

export function buildGraticule(step = 30) {
  const features = [];
  for (let lon = -180; lon <= 180; lon += step) {
    features.push({
      type: "Feature",
      properties: { kind: "meridian" },
      geometry: {
        type: "LineString",
        coordinates: [
          [lon, -85],
          [lon, 85],
        ],
      },
    });
  }
  for (let lat = -60; lat <= 60; lat += step) {
    features.push({
      type: "Feature",
      properties: { kind: lat === 0 ? "equator" : "parallel" },
      geometry: {
        type: "LineString",
        coordinates: [
          [-180, lat],
          [180, lat],
        ],
      },
    });
  }
  return { type: "FeatureCollection", features };
}

export function boundsAround(lat, lon, halfWidth = 8) {
  const south = Math.max(-85, lat - halfWidth);
  const north = Math.min(85, lat + halfWidth);
  const west = Math.max(-180, lon - halfWidth * 1.5);
  const east = Math.min(180, lon + halfWidth * 1.5);
  return [
    [west, south],
    [east, north],
  ];
}
