export function normalizeInvestigation(inv = {}) {
  const availability = inv.availability || inv.availability_status || inv.status || "";
  const coverage = inv.coverage || {
    spatial: inv.supported_geographical_coverage || inv.geographical_coverage || inv.spatial_coverage || inv.spatial,
    temporal: inv.supported_temporal_coverage || inv.temporal_coverage || inv.temporal || inv.period,
  };
  return {
    ...inv,
    id: inv.id || inv.investigation_id || inv.code || inv.key,
    title: inv.title || inv.name || inv.display_name || inv.id || "",
    question: inv.question || inv.scientific_question || inv.description || "",
    description: inv.description || inv.summary || "",
    objective: inv.objective || inv.scientific_objective || "",
    methodology: inv.methodology || inv.methodology_summary || "",
    availability,
    coverage,
    variables: inv.variables || (inv.scientific_variable ? [inv.scientific_variable] : (inv.environmental_variable ? [inv.environmental_variable] : (inv.variable ? [inv.variable] : []))),
    dataset: inv.dataset || (inv.dataset_name ? { name: inv.dataset_name } : null),
    outputs: inv.outputs || inv.expected_outputs || [],
    limitations: inv.limitations || [],
  };
}

export function isExecutable(availability) {
  return ["available", "implemented", "active"].includes(String(availability || "").toLowerCase());
}

export function coverageText(coverage) {
  if (!coverage) return "—";
  if (typeof coverage === "string") return coverage;
  if (Array.isArray(coverage)) return coverage.join(" to ");
  try { return JSON.stringify(coverage); } catch { return String(coverage); }
}
