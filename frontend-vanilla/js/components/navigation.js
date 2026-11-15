import { qs, qsa } from "../utils/helpers.js";

export function initNavigation() {
  const path = window.location.pathname.replace(/\/+$/, "") || "/";
  qsa(".primary-nav a").forEach((a) => {
    const href = (a.getAttribute("href") || "").replace(/\/+$/, "") || "/";
    const current = href === path || (href !== "/" && path.endsWith(href));
    if (current) a.setAttribute("aria-current", "page");
    else a.removeAttribute("aria-current");
  });

  const toggle = qs(".nav-toggle");
  const nav = qs("#primary-nav") || qs(".primary-nav");
  if (toggle && nav) {
    toggle.addEventListener("click", () => {
      const open = nav.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }
}
