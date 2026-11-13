import { NOT_A_FORECAST, SYNTHETIC_WARNING } from "../lib/format.js";

export default function Header({ health, onShowHelp }) {
  return (
    <header className="site-header">
      <div className="brand">
        <div className="brand__globe" aria-hidden="true">
          <span />
        </div>
        <div>
          <h1>Global Change Explorer</h1>
          <p>
            Click a place. See what changed, how fast, and whether the change is
            statistically significant.
          </p>
        </div>
      </div>
      <div className="header-actions">
        <span
          className={`mode-badge ${health?.synthetic ? "mode-badge--synthetic" : "mode-badge--real"}`}
        >
          {health?.synthetic ? "Synthetic demo" : "Real observations"}
        </span>
        <button type="button" className="button button--ghost" onClick={onShowHelp}>
          How to read this
        </button>
        <span className="sr-only" id="not-a-forecast">
          {NOT_A_FORECAST}
        </span>
        {health?.synthetic ? (
          <span className="sr-only">{SYNTHETIC_WARNING}</span>
        ) : null}
      </div>
    </header>
  );
}
