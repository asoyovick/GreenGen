import { getInvestigation } from "../api/investigations.js";
import { qs, clear, el, getParam } from "../utils/helpers.js";
import { titleCase } from "../utils/formatting.js";

const fallbackDetails = {
  "INV-001": {
    id: "INV-001",
    title: "Historical precipitation trends in Kenya",
    question: "How has precipitation changed across different geographical locations in Kenya over a selected historical period, and where are those changes statistically significant?",
    objective: "Detect, measure, and explain spatial patterns of precipitation change with statistical evidence and uncertainty.",
    dataset: "NASA GPM IMERG (monthly product; version finalized in data integration)",
    variable: "Precipitation (mm/month, mm/year or as provided by source/processing)",
    spatial: "Kenya (initial MVP focus), native grid preserved where practical (~0.1° for IMERG)",
    temporal: "User-selected period within supported dataset coverage",
    methodology: "Temporal aggregation (monthly/annual/seasonal as configured), grid-level Mann–Kendall trend testing with appropriate assumptions, Sen’s slope magnitude and confidence intervals, multiple-testing correction (e.g. FDR) as defined by methodology, and quality/completeness checks.",
    outputs: ["Trend direction and magnitude per eligible grid cell", "Significance and uncertainty metrics", "Classifications: significant increase/decrease, no significant trend detected, insufficient data, inconclusive", "Time series and provenance metadata"],
    limitations: ["Dataset and retrieval limitations/quality flags apply", "Statistical significance does not imply causation", "Non-significant trend does not mean stability", "Results depend on selected period, completeness, and methodological assumptions"],
    availability: "planned",
  },
};

function section(title, body) {
  return el("section", { class: "panel stack" }, [el("h2", { style: "margin:0;", text: title }), body]);
}

document.addEventListener("DOMContentLoaded", async () => {
  const status = qs("#details-status");
  const root = qs("#details-root");
  const id = getParam("id") || "INV-001";
  try {
    const res = await getInvestigation(id);
    const inv = res?.investigation || res;
    render(inv || fallbackDetails[id] || { id, title: id, availability: "unavailable" }, res?.source);
    status.hidden = true;
    root.hidden = false;
  } catch (err) {
    const fb = fallbackDetails[id] || { id, title: id, question: "Details unavailable.", availability: "unavailable", limitations: [err.message] };
    status.className = "notice notice-warning";
    status.textContent = `Backend details unavailable (${err.message}). Showing documented information where available.`;
    render(fb, "fallback");
    root.hidden = false;
  }

  function render(inv, source) {
    clear(root);
    const canExecute = ["available", "implemented", "active"].includes(String(inv.availability || "").toLowerCase());
    root.append(
      el("div", { class: "inline-actions", style: "justify-content:space-between;align-items:flex-start;" }, [
        el("div", {}, [
          el("p", { class: "badge", text: inv.id || id }),
          el("h1", { style: "margin:0.25rem 0 0;", text: inv.title || id }),
        ]),
        el("span", { class: `badge ${canExecute ? "badge-available" : "badge-planned"}`, text: canExecute ? "Available" : titleCase(inv.availability || "Planned/Unavailable") }),
      ]),
      section("Scientific objective and research question", el("div", {}, [
        inv.objective ? el("p", { text: inv.objective }) : null,
        el("p", {}, [el("strong", { text: "Research question: " }), document.createTextNode(inv.question || "—")]),
      ])),
      section("Dataset and variable", el("dl", { class: "dl" }, [
        el("dt", { text: "Dataset" }), el("dd", { text: inv.dataset?.name || inv.dataset || "—" }),
        el("dt", { text: "Environmental variable / units" }), el("dd", { text: inv.variable || (inv.variables || []).join(", ") || inv.units || "—" }),
        el("dt", { text: "Spatial coverage" }), el("dd", { text: typeof inv.spatial === "string" ? inv.spatial : (inv.coverage?.spatial ? JSON.stringify(inv.coverage.spatial) : "—") }),
        el("dt", { text: "Temporal coverage" }), el("dd", { text: typeof inv.temporal === "string" ? inv.temporal : (Array.isArray(inv.coverage?.temporal) ? inv.coverage.temporal.join(" to ") : (inv.coverage?.temporal ? JSON.stringify(inv.coverage.temporal) : "—")) }),
      ])),
      section("Methodology summary", el("p", { text: inv.methodology || inv.methodology_summary || "Methodology details will be provided by the scientific engine/backend documentation for implemented analyses." })),
      section("Expected scientific outputs", (() => {
        const outs = inv.outputs || inv.expected_outputs || [];
        if (!outs.length) return el("p", { class: "muted", text: "Output fields will be displayed when provided by the backend." });
        const ul = el("ul"); outs.forEach((o) => ul.appendChild(el("li", { text: typeof o === "string" ? o : JSON.stringify(o) }))); return ul;
      })()),
      section("Known limitations", (() => {
        const lim = inv.limitations || ["Dataset quality/completeness constraints apply.", "Statistical trends do not imply causation.", "Uncertainty and methodological assumptions must be considered."];
        const ul = el("ul"); lim.forEach((o) => ul.appendChild(el("li", { text: typeof o === "string" ? o : JSON.stringify(o) }))); return ul;
      })()),
      section("Configure and execute", el("div", { class: "stack" }, [
        source === "prototype" ? el("p", { class: "notice notice-warning", text: "This view is based on precomputed prototype data, not a live execution workflow." }) : null,
        el("div", { class: "inline-actions" }, [
          canExecute ? el("a", { class: "btn btn-primary", href: `./explore.html?investigation=${encodeURIComponent(inv.id || id)}`, text: "Configure and run investigation" }) : el("button", { class: "btn btn-secondary", type: "button", disabled: true, text: "Execution not available for this investigation" }),
          el("a", { class: "btn btn-secondary", href: "./investigations.html", text: "Back to catalogue" }),
        ]),
      ])),
    );
  }
});
