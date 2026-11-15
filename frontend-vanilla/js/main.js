import { initNavigation } from "./components/navigation.js";
import { notify } from "./components/notifications.js";
import { getApiHealth } from "./api/investigations.js";

async function showHealthBanner() {
  const el = document.getElementById("global-status");
  if (!el) return;
  try {
    const health = await getApiHealth();
    if (health?.synthetic) {
      // No synthetic data is used.
      el.hidden = true;
    } else if (health?.status && health.status !== "ok") {
      el.hidden = false;
      el.className = "banner";
      el.textContent = `Backend status: ${health.status}. Some features may be unavailable.`;
    }
  } catch (err) {
    // Health check is best-effort; pages handle their own errors.
    el.hidden = false;
    el.className = "banner";
    el.textContent = "Backend API not reachable. Configure the API base URL and ensure the server is running to load live data.";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  initNavigation();
  showHealthBanner();
  window.GreenGenUI = window.GreenGenUI || {};
  window.GreenGenUI.notify = notify;
});
