import { SYNTHETIC_WARNING } from "../lib/format.js";

export default function SyntheticBanner({ synthetic, mode }) {
  if (!synthetic) {
    return (
      <div className="mode-strip mode-strip--real" role="status">
        <strong>Real NASA data.</strong> Observed change only, not a forecast.
      </div>
    );
  }
  return (
    <div className="synthetic-banner" role="status" aria-live="polite">
      <span className="synthetic-banner__mark" aria-hidden="true">
        !
      </span>
      <span>
        <strong>{SYNTHETIC_WARNING}</strong> Every number, map and chart on this
        page is generated demo data{mode ? ` (mode: ${mode})` : ""}. Do not cite
        it as NASA data.
      </span>
    </div>
  );
}
