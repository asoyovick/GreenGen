import { listInvestigations } from "../api/investigations.js";
import { qs, clear, el } from "../utils/helpers.js";
import { classificationLabel, titleCase } from "../utils/formatting.js";

function availabilityBadge(status) {
  const s = String(status || "").toLowerCase();
  if (["available", "implemented", "active", "available_precomputed"].includes(s)) return el("span", { class: "badge badge-available", text: s === "available_precomputed" ? "Precomputed (prototype)" : "Available" });
  if (["planned", "future"].includes(s)) return el("span", { class: "badge badge-planned", text: "Planned" });
  return el("span", { class: "badge badge-unavailable", text: titleCase(s || "Unavailable") });
}

function normInvestigation(inv = {}) {
  const availability = inv.availability || inv.availability_status || inv.status || "";
  const coverage = inv.coverage || {
    spatial: inv.supported_geographical_coverage || inv.geographical_coverage || inv.spatial_coverage || inv.spatial,
    temporal: inv.supported_temporal_coverage || inv.temporal_coverage || inv.temporal || inv.period,
  };
  return {
    ...inv,
    id: inv.id || inv.investigation_id || inv.code || inv.key,
    title: inv.title || inv.name || inv.display_name || inv.id,
    question: inv.question || inv.scientific_question || inv.description,
    availability,
    coverage,
    variables: inv.variables || (inv.scientific_variable ? [inv.scientific_variable] : (inv.environmental_variable ? [inv.environmental_variable] : [])),
    dataset: inv.dataset || (inv.dataset_name ? { name: inv.dataset_name } : null),
  };
}

function renderCard(raw) {
  const inv = normInvestigation(raw);
  const id = inv.id;
  const coverage = inv.coverage || {};
  const temporal = coverage.temporal || inv.temporal_coverage || inv.period;
  const spatial = coverage.spatial || inv.geographical_coverage || inv.spatial_coverage;
  const detailsHref = `./investigation-details.html?id=${encodeURIComponent(id ?? "")}`;
  const canExecute = ["available", "implemented", "active"].includes(String(inv.availability || "").toLowerCase());
  const vars = Array.isArray(inv.variables) ? inv.variables.join(", ") : (inv.variables || "—");
  const dataset = inv.dataset?.name || inv.dataset?.short_name || (typeof inv.dataset === "string" ? inv.dataset : "—");
  const card = el("article", { class: "card stack" }, [
    el("div", { class: "inline-actions", style: "justify-content:space-between;align-items:flex-start;" }, [
      el("h3", { text: inv.title || id || "Investigation" }),
      availabilityBadge(inv.availability),
    ]),
    inv.question ? el("p", { text: inv.question }) : (inv.description ? el("p", { text: inv.description }) : null),
    el("dl", { class: "dl" }, [
      el("dt", { text: "Variable" }), el("dd", { text: vars || "—" }),
      el("dt", { text: "Dataset" }), el("dd", { text: dataset || "—" }),
      el("dt", { text: "Geographical coverage" }), el("dd", { text: typeof spatial === "string" ? spatial : (spatial ? JSON.stringify(spatial) : "—") }),
      el("dt", { text: "Historical coverage" }), el("dd", { text: Array.isArray(temporal) ? temporal.join(" to ") : (typeof temporal === "string" ? temporal : (temporal ? JSON.stringify(temporal) : "—")) }),
    ]),
    inv.synthetic ? el("p", { class: "field-hint warning-text", text: "Unavailable: synthetic data is not used." }) : null,
    el("div", { class: "inline-actions" }, [
      el("a", { class: "btn btn-secondary", href: detailsHref, text: "View details" }),
      canExecute ? el("a", { class: "btn btn-primary", href: `./configure-investigation.html?id=${encodeURIComponent(id ?? "")}`, text: "Configure" }) : el("button", { class: "btn btn-secondary", disabled: true, type: "button", text: "Execution unavailable" }),
    ]),
  ]);
  return card;
}

function plannedFallback() {
  return [
    {
      id: "INV-001",
      title: "Historical precipitation trends in Kenya",
      question: "How has precipitation changed across different geographical locations in Kenya over a selected historical period, and where are those changes statistically significant?",
      variables: ["precipitation"],
      dataset: { name: "NASA GPM IMERG (planned/selected per integration)" },
      coverage: { spatial: "Kenya (initial focus)", temporal: "To be constrained by dataset coverage" },
      availability: "planned",
    },
    { id: "INV-002", title: "Temperature trends", question: "How have temperature conditions changed geographically over time?", variables: ["temperature"], dataset: { name: "TBD" }, coverage: { spatial: "TBD", temporal: "TBD" }, availability: "planned" },
    { id: "INV-003", title: "Soil moisture trends", question: "How has soil moisture changed across geographical locations?", variables: ["soil_moisture"], dataset: { name: "TBD" }, coverage: { spatial: "TBD", temporal: "TBD" }, availability: "planned" },
    { id: "INV-004", title: "Vegetation trends", question: "How has vegetation greenness changed geographically?", variables: ["ndvi", "evi"], dataset: { name: "TBD" }, coverage: { spatial: "TBD", temporal: "TBD" }, availability: "planned" },
  ];
}

document.addEventListener("DOMContentLoaded", async () => {
  const status = qs("#catalogue-status");
  const list = qs("#catalogue-list");
  if (!status || !list) return;
  try {
    const data = await listInvestigations();
    const items = Array.isArray(data) ? data : (data?.investigations || []);
    clear(list);
    if (!items.length) {
      status.className = "notice notice-warning";
      status.textContent = "No investigations returned by the backend. Showing documented catalogue placeholders (planned).";
      plannedFallback().forEach((i) => list.appendChild(renderCard(i)));
      return;
    }
    status.className = "notice notice-success";
    status.textContent = data?.note || `Loaded ${items.length} investigation(s) from the backend.`;
    items.forEach((i) => list.appendChild(renderCard(i)));
  } catch (err) {
    status.className = "notice notice-error";
    status.textContent = `Unable to load investigations from the backend: ${err.message}. Showing documented catalogue placeholders (planned).`;
    clear(list);
    plannedFallback().forEach((i) => list.appendChild(renderCard(i)));
  }
});
