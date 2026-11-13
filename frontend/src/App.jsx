import { useCallback, useEffect, useState } from "react";
import { api } from "./api.js";
import Explorer from "./components/Explorer.jsx";
import Footer from "./components/Footer.jsx";
import Header from "./components/Header.jsx";
import SyntheticBanner from "./components/SyntheticBanner.jsx";
import { NOT_A_FORECAST } from "./lib/format.js";

function LoadingScreen() {
  return (
    <div className="status-screen" role="status" aria-live="polite">
      <div className="spinner" aria-hidden="true" />
      <h1>Loading the change layers…</h1>
      <p>Looking up the precomputed trend and significance grids.</p>
    </div>
  );
}

function ConnectionScreen({ message, onRetry }) {
  return (
    <div className="status-screen status-screen--error" role="alert">
      <h1>The map data could not be loaded</h1>
      <p>{message}</p>
      <div className="status-screen__actions">
        <button type="button" className="button button--primary" onClick={onRetry}>
          Retry
        </button>
      </div>
      <details>
        <summary>Run the demo locally</summary>
        <pre>
          <code>{`make synthetic
make pipeline
make api

# then open http://127.0.0.1:8000`}</code>
        </pre>
      </details>
    </div>
  );
}

function HelpDialog({ open, onClose }) {
  useEffect(() => {
    if (!open) return undefined;
    const onKey = (event) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;
  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={onClose}>
      <section
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="help-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="modal__head">
          <h2 id="help-title">How to read this</h2>
          <button
            type="button"
            className="button button--icon"
            onClick={onClose}
            aria-label="Close help"
          >
            ×
          </button>
        </div>
        <div className="modal__body">
          <h3>1. Pick a place</h3>
          <p>
            Click the map, search the built-in gazetteer, or type coordinates.
            The report describes the nearest 0.5° grid cell, not an exact point.
          </p>
          <h3>2. Read the verdict</h3>
          <p>
            “Significant increase” or “significant decrease” means the
            FDR-corrected Mann–Kendall result passed α = 0.05. “No statistically
            significant change detected” means the evidence was not strong
            enough — not that the variable stayed constant.
          </p>
          <h3>3. Check the rate</h3>
          <p>
            Rates are per decade. A rate without a significant verdict is still
            shown as an estimate, but it should be treated as uncertain.
          </p>
          <h3>4. Compare with neighbours</h3>
          <p>
            The nearby comparison shows whether surrounding cells trend in the
            same direction. Opposite directions are a warning that a single
            regional story does not fit the whole area.
          </p>
          <h3>Scope</h3>
          <p>
            {NOT_A_FORECAST} Model-based variables are labelled; they are
            reanalyses, not direct observations.
          </p>
        </div>
      </section>
    </div>
  );
}

export default function App() {
  const [state, setState] = useState({
    status: "loading",
    error: null,
    health: null,
    variables: null,
    layers: null,
  });
  const [helpOpen, setHelpOpen] = useState(false);

  const load = useCallback(async () => {
    setState((prev) => ({ ...prev, status: "loading", error: null }));
    try {
      const [health, variables, layers] = await Promise.all([
        api.health(),
        api.variables(),
        api.layers(),
      ]);
      setState({ status: "ready", error: null, health, variables, layers });
    } catch (error) {
      setState((prev) => ({
        ...prev,
        status: "error",
        error: error?.message || "Unknown API error.",
      }));
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    document.title = state.health?.synthetic
      ? "Global Change Explorer — synthetic demo"
      : "Global Change Explorer";
  }, [state.health]);

  if (state.status === "loading") return <LoadingScreen />;
  if (state.status === "error") {
    return (
      <ConnectionScreen message={state.error} onRetry={load} />
    );
  }

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main">
        Skip to the explorer
      </a>
      <Header health={state.health} onShowHelp={() => setHelpOpen(true)} />
      <SyntheticBanner
        synthetic={state.health?.synthetic}
        mode={state.health?.mode}
      />
      <main id="main" className="app-main">
        <Explorer
          health={state.health}
          layers={state.layers}
          variables={state.variables}
        />
      </main>
      <Footer
        health={state.health}
        variables={state.variables}
        layerMeta={state.layers}
      />
      <HelpDialog open={helpOpen} onClose={() => setHelpOpen(false)} />
    </div>
  );
}
