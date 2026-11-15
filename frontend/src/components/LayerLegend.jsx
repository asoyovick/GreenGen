export default function LayerLegend({ layer }) {
  if (!layer) return null;
  const legend = layer.legend;
  return (
    <div className="legend" aria-label={`Legend for ${layer.display_name}`}>
      <h2>{layer.display_name}</h2>
      {layer.meaning && <p className="legend__meaning">{layer.meaning}</p>}
      {Array.isArray(legend) && (
        <div className="legend__items">
          {legend.map((item) => (
            <div className="legend__item" key={item.label}>
              <span
                className={`legend__swatch ${
                  !item.color || item.color === "transparent"
                    ? "legend__swatch--transparent"
                    : ""
                }`}
                style={
                  item.color && item.color !== "transparent"
                    ? { background: item.color }
                    : undefined
                }
                aria-hidden="true"
              />
              <span>{item.label}</span>
            </div>
          ))}
        </div>
      )}
      {legend && !Array.isArray(legend) && legend.stops && (
        <>
          <div
            className="legend__gradient"
            style={{
              background: `linear-gradient(90deg, ${legend.stops
                .map((stop) => stop.color)
                .join(", ")})`,
            }}
            aria-hidden="true"
          />
          <div className="legend__gradient-labels">
            <span>{legend.stops[0]?.label || "decrease"}</span>
            <span>{legend.stops[legend.stops.length - 1]?.label || "increase"}</span>
          </div>
          {legend.note && <p className="legend__note">{legend.note}</p>}
        </>
      )}
      {layer.units && <p className="legend__note">Units: {layer.units}</p>}
      {layer.model_based && (
        <p className="legend__note">Model-based reanalysis, not direct observations.</p>
      )}
    </div>
  );
}
