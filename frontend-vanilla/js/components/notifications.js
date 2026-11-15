import { el } from "../utils/helpers.js";

let container;

function ensure() {
  if (container && document.body.contains(container)) return container;
  container = document.getElementById("notifications");
  if (!container) {
    container = el("div", { id: "notifications", class: "notifications", "aria-live": "polite", "aria-atomic": "false" });
    document.body.appendChild(container);
  }
  return container;
}

export function notify(message, { type = "info", timeout = 5000, title } = {}) {
  const root = ensure();
  const note = el("div", { class: `notice notice-${type}`, role: type === "error" ? "alert" : "status" }, [
    title ? el("strong", { text: title }) : null,
    title ? document.createTextNode(" ") : null,
    el("span", { text: message }),
  ]);
  root.appendChild(note);
  if (timeout > 0) setTimeout(() => note.remove(), timeout);
  return note;
}

export function clearNotifications() { ensure().innerHTML = ""; }
