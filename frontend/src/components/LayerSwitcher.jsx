import { useMemo } from "react";

function layerLabel(layer) {
  if (layer.kind === "change_score") return layer.display_name;
  if (layer.kind === "class") return `${layer.display_name} — direction & significance`;
  return `${layer.display_name} — trend strength`;
}

export default function LayerSwitcher({
  metadata,
  selectedId,
  onChange,
  opacity,
  onOpacityChange,
}) {
  const groups = useMemo(() => {
    if (!metadata?.layers) return { top: [], variables: [] };
    const top = [];
    const byVariable = new Map();
    for (const layer of Object.values(metadata.layers)) {
      if (!layer.variable) {
        top.push(layer);
        continue;
      }
      if (!byVariable.has(layer.variable)) {
        byVariable.set(layer.variable, []);
      }
      byVariable.get(layer.variable).push(layer);
    }
    return { top, variables: [...byVariable.entries()] };
  }, [metadata]);

  return (
    <div className="layer-switcher" aria-label="Map layer controls">
      <div className="layer-switcher__head">
        <h2>Map layer</h2>
        <span className="sr-only" id="layer-help">
          Choose the precomputed trend layer drawn over the base map.
        </span>
      </div>
      <select
        value={selectedId}
        onChange={(event) => onChange(event.target.value)}
        aria-describedby="layer-help"
      >
        {groups.top.map((layer) => (
          <option key={layer.id} value={layer.id}>
            {layerLabel(layer)}
          </option>
        ))}
        {groups.variables.map(([key, entries]) => (
          <optgroup key={key} label={entries[0]?.display_name || key}>
            {entries.map((layer) => (
              <option key={layer.id} value={layer.id}>
                {layer.kind === "class" ? "Direction & significance" : "Trend strength"}
              </option>
            ))}
          </optgroup>
        ))}
      </select>
      <label className="opacity-row" htmlFor="overlay-opacity">
        <span>Opacity</span>
        <input
          id="overlay-opacity"
          type="range"
          min="0.15"
          max="1"
          step="0.05"
          value={opacity}
          onChange={(event) => onOpacityChange(Number(event.target.value))}
        />
        <output htmlFor="overlay-opacity">{Math.round(opacity * 100)}%</output>
      </label>
    </div>
  );
}
