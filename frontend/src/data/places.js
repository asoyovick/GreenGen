/**
 * Offline place gazetteer for the demo. This deliberately ships with the app so
 * search works without calling an external geocoder. It is not a complete
 * world gazetteer; coordinate entry covers any point on Earth.
 */
export const PLACES = [
  { name: "Nairobi", country: "Kenya", lat: -1.286, lon: 36.817, aliases: ["capital of kenya"] },
  { name: "Mombasa", country: "Kenya", lat: -4.043, lon: 39.668 },
  { name: "Kisumu", country: "Kenya", lat: -0.091, lon: 34.768 },
  { name: "Addis Ababa", country: "Ethiopia", lat: 9.03, lon: 38.74 },
  { name: "Kampala", country: "Uganda", lat: 0.347, lon: 32.582 },
  { name: "Dar es Salaam", country: "Tanzania", lat: -6.792, lon: 39.208 },
  { name: "Kigali", country: "Rwanda", lat: -1.944, lon: 30.062 },
  { name: "Cairo", country: "Egypt", lat: 30.044, lon: 31.236 },
  { name: "Lagos", country: "Nigeria", lat: 6.524, lon: 3.379 },
  { name: "Accra", country: "Ghana", lat: 5.603, lon: -0.187 },
  { name: "Dakar", country: "Senegal", lat: 14.716, lon: -17.467 },
  { name: "Cape Town", country: "South Africa", lat: -33.925, lon: 18.424 },
  { name: "Johannesburg", country: "South Africa", lat: -26.204, lon: 28.047 },
  { name: "Antananarivo", country: "Madagascar", lat: -18.879, lon: 47.508 },
  { name: "Marrakesh", country: "Morocco", lat: 31.63, lon: -7.981 },
  { name: "Sahel region", country: "Africa", lat: 14.5, lon: 0.0, aliases: ["sahel"] },
  { name: "Congo Basin", country: "Central Africa", lat: 0.0, lon: 20.0, aliases: ["congo rainforest"] },
  { name: "London", country: "United Kingdom", lat: 51.507, lon: -0.128 },
  { name: "Paris", country: "France", lat: 48.857, lon: 2.352 },
  { name: "Berlin", country: "Germany", lat: 52.52, lon: 13.405 },
  { name: "Madrid", country: "Spain", lat: 40.417, lon: -3.704 },
  { name: "Rome", country: "Italy", lat: 41.903, lon: 12.496 },
  { name: "Lisbon", country: "Portugal", lat: 38.722, lon: -9.139 },
  { name: "Amsterdam", country: "Netherlands", lat: 52.368, lon: 4.904 },
  { name: "Stockholm", country: "Sweden", lat: 59.329, lon: 18.069 },
  { name: "Oslo", country: "Norway", lat: 59.914, lon: 10.752 },
  { name: "Helsinki", country: "Finland", lat: 60.17, lon: 24.938 },
  { name: "Reykjavik", country: "Iceland", lat: 64.147, lon: -21.94 },
  { name: "Warsaw", country: "Poland", lat: 52.23, lon: 21.012 },
  { name: "Kyiv", country: "Ukraine", lat: 50.45, lon: 30.523 },
  { name: "Istanbul", country: "Turkey", lat: 41.008, lon: 28.978 },
  { name: "Athens", country: "Greece", lat: 37.983, lon: 23.727 },
  { name: "Moscow", country: "Russia", lat: 55.756, lon: 37.617 },
  { name: "Samara", country: "Russia", lat: 53.2, lon: 50.15 },
  { name: "Yekaterinburg", country: "Russia", lat: 56.838, lon: 60.605 },
  { name: "Omsk", country: "Russia", lat: 54.988, lon: 73.368, aliases: ["omsk siberia"] },
  { name: "Novosibirsk", country: "Russia", lat: 55.008, lon: 82.935 },
  { name: "Krasnoyarsk", country: "Russia", lat: 56.013, lon: 92.866 },
  { name: "Irkutsk", country: "Russia", lat: 52.287, lon: 104.305 },
  { name: "Yakutsk", country: "Russia", lat: 62.035, lon: 129.675 },
  { name: "Vladivostok", country: "Russia", lat: 43.115, lon: 131.886 },
  { name: "Almaty", country: "Kazakhstan", lat: 43.238, lon: 76.945 },
  { name: "Astana", country: "Kazakhstan", lat: 51.169, lon: 71.449 },
  { name: "Tashkent", country: "Uzbekistan", lat: 41.299, lon: 69.24 },
  { name: "Ulaanbaatar", country: "Mongolia", lat: 47.886, lon: 106.906 },
  { name: "Beijing", country: "China", lat: 39.904, lon: 116.407 },
  { name: "Shanghai", country: "China", lat: 31.23, lon: 121.474 },
  { name: "Hong Kong", country: "China", lat: 22.319, lon: 114.169 },
  { name: "Tokyo", country: "Japan", lat: 35.677, lon: 139.65 },
  { name: "Seoul", country: "South Korea", lat: 37.567, lon: 126.978 },
  { name: "Delhi", country: "India", lat: 28.704, lon: 77.102 },
  { name: "Mumbai", country: "India", lat: 19.076, lon: 72.877 },
  { name: "Kolkata", country: "India", lat: 22.573, lon: 88.364 },
  { name: "Bengaluru", country: "India", lat: 12.972, lon: 77.594 },
  { name: "Dhaka", country: "Bangladesh", lat: 23.811, lon: 90.413 },
  { name: "Bangkok", country: "Thailand", lat: 13.756, lon: 100.502 },
  { name: "Jakarta", country: "Indonesia", lat: -6.208, lon: 106.846 },
  { name: "Singapore", country: "Singapore", lat: 1.352, lon: 103.82 },
  { name: "Manila", country: "Philippines", lat: 14.599, lon: 120.984 },
  { name: "Hanoi", country: "Vietnam", lat: 21.028, lon: 105.854 },
  { name: "Tehran", country: "Iran", lat: 35.689, lon: 51.389 },
  { name: "Baghdad", country: "Iraq", lat: 33.315, lon: 44.366 },
  { name: "Riyadh", country: "Saudi Arabia", lat: 24.713, lon: 46.675 },
  { name: "Dubai", country: "United Arab Emirates", lat: 25.205, lon: 55.271 },
  { name: "Jerusalem", country: "Israel", lat: 31.769, lon: 35.214 },
  { name: "Karachi", country: "Pakistan", lat: 24.86, lon: 67.01 },
  { name: "Himalaya", country: "Asia", lat: 28.0, lon: 84.0, aliases: ["himalayas", "mount everest"] },
  { name: "New York", country: "United States", lat: 40.713, lon: -74.006, aliases: ["nyc"] },
  { name: "Washington DC", country: "United States", lat: 38.907, lon: -77.037 },
  { name: "Chicago", country: "United States", lat: 41.878, lon: -87.63 },
  { name: "Los Angeles", country: "United States", lat: 34.052, lon: -118.244 },
  { name: "San Francisco", country: "United States", lat: 37.775, lon: -122.419 },
  { name: "Seattle", country: "United States", lat: 47.606, lon: -122.332 },
  { name: "Miami", country: "United States", lat: 25.762, lon: -80.192 },
  { name: "Anchorage", country: "United States", lat: 61.218, lon: -149.9 },
  { name: "Honolulu", country: "United States", lat: 21.307, lon: -157.858 },
  { name: "Toronto", country: "Canada", lat: 43.653, lon: -79.383 },
  { name: "Vancouver", country: "Canada", lat: 49.283, lon: -123.121 },
  { name: "Montreal", country: "Canada", lat: 45.502, lon: -73.567 },
  { name: "Mexico City", country: "Mexico", lat: 19.433, lon: -99.133 },
  { name: "Havana", country: "Cuba", lat: 23.114, lon: -82.366 },
  { name: "Panama City", country: "Panama", lat: 8.983, lon: -79.517 },
  { name: "Bogotá", country: "Colombia", lat: 4.711, lon: -74.072 },
  { name: "Lima", country: "Peru", lat: -12.046, lon: -77.043 },
  { name: "Quito", country: "Ecuador", lat: -0.181, lon: -78.467 },
  { name: "La Paz", country: "Bolivia", lat: -16.49, lon: -68.119 },
  { name: "Santiago", country: "Chile", lat: -33.449, lon: -70.669 },
  { name: "Buenos Aires", country: "Argentina", lat: -34.604, lon: -58.382 },
  { name: "São Paulo", country: "Brazil", lat: -23.551, lon: -46.633 },
  { name: "Rio de Janeiro", country: "Brazil", lat: -22.907, lon: -43.173 },
  { name: "Manaus", country: "Brazil", lat: -3.119, lon: -60.022 },
  { name: "Brasília", country: "Brazil", lat: -15.794, lon: -47.882 },
  { name: "Amazon Basin", country: "South America", lat: -5.0, lon: -63.0, aliases: ["amazon rainforest", "amazonia"] },
  { name: "Sydney", country: "Australia", lat: -33.869, lon: 151.209 },
  { name: "Melbourne", country: "Australia", lat: -37.814, lon: 144.963 },
  { name: "Perth", country: "Australia", lat: -31.953, lon: 115.857 },
  { name: "Darwin", country: "Australia", lat: -12.463, lon: 130.846 },
  { name: "Auckland", country: "New Zealand", lat: -36.848, lon: 174.763 },
  { name: "Wellington", country: "New Zealand", lat: -41.287, lon: 174.776 },
  { name: "Suva", country: "Fiji", lat: -18.141, lon: 178.442 },
  { name: "Antarctic Peninsula", country: "Antarctica", lat: -65.0, lon: -62.0, aliases: ["antarctica"] },
  { name: "Greenland ice sheet", country: "Greenland", lat: 72.0, lon: -40.0, aliases: ["greenland"] },
  { name: "Arctic Ocean", country: "Ocean", lat: 80.0, lon: 0.0, aliases: ["north pole"] },
  { name: "Pacific Ocean", country: "Ocean", lat: 0.0, lon: -150.0, aliases: ["pacific"] },
  { name: "Atlantic Ocean", country: "Ocean", lat: 25.0, lon: -40.0, aliases: ["atlantic"] },
  { name: "Indian Ocean", country: "Ocean", lat: -20.0, lon: 80.0, aliases: ["indian ocean"] },
  { name: "Mediterranean Sea", country: "Sea", lat: 35.0, lon: 18.0 },
  { name: "Great Barrier Reef", country: "Australia", lat: -18.287, lon: 147.699 },
];

export function searchPlaces(query, limit = 8) {
  const q = query.trim().toLowerCase();
  if (!q) return [];
  const scored = [];
  for (const place of PLACES) {
    const haystack = `${place.name} ${place.country} ${(place.aliases || []).join(" ")}`.toLowerCase();
    const name = place.name.toLowerCase();
    let score = -1;
    if (name === q) score = 100;
    else if (name.startsWith(q)) score = 80;
    else if (name.includes(q)) score = 60;
    else if (haystack.includes(q)) score = 40;
    if (score >= 0) scored.push({ place, score });
  }
  return scored
    .sort((a, b) => b.score - a.score || a.place.name.localeCompare(b.place.name))
    .slice(0, limit)
    .map((entry) => entry.place);
}

export function findPlace(name) {
  if (!name) return null;
  const q = name.trim().toLowerCase();
  return PLACES.find((p) => p.name.toLowerCase() === q) || null;
}
