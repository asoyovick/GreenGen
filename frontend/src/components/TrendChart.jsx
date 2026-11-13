import { useMemo } from "react";
import createPlotlyComponent from "react-plotly.js/factory";
import Plotly from "plotly.js-basic-dist-min";
import {
  formatNumber,
  formatRate,
  unitLabel,
  verdictText,
} from "../lib/format.js";

const Plot = createPlotlyComponent(Plotly);

export default function TrendChart({ series }) {
  const data = useMemo(() => {
    if (!series) return [];
    return [
      {
        x: series.years,
        y: series.annual_anomaly,
        type: "scatter",
        mode: "lines+markers",
        name: "Annual anomaly",
        line: { color: "#62e6bb", width: 2 },
        marker: { color: "#62e6bb", size: 5 },
        hovertemplate: `%{x}: %{y:.4g} ${unitLabel(series.unit)}<extra></extra>`,
        connectgaps: false,
      },
      {
        x: series.years,
        y: series.trend_line,
        type: "scatter",
        mode: "lines",
        name: "Theil–Sen trend",
        line: { color: "#ffd166", width: 2, dash: "dash" },
        hoverinfo: "skip",
      },
    ];
  }, [series]);

  const layout = useMemo(
    () => ({
      autosize: true,
      height: 300,
      margin: { l: 62, r: 14, t: 12, b: 42 },
      paper_bgcolor: "rgba(0,0,0,0)",
      plot_bgcolor: "rgba(0,0,0,0)",
      font: {
        color: "#a8beb5",
        size: 11,
        family:
          'Inter, "Segoe UI", system-ui, -apple-system, BlinkMacSystemFont, sans-serif',
      },
      hovermode: "x unified",
      hoverlabel: {
        bgcolor: "#0f241f",
        bordercolor: "#2a5146",
        font: { color: "#f1f7f4", size: 11 },
      },
      xaxis: {
        title: { text: "Year", standoff: 8 },
        gridcolor: "rgba(168,190,181,0.12)",
        zeroline: false,
        tickmode: "linear",
        dtick: 2,
        fixedrange: true,
      },
      yaxis: {
        title: { text: unitLabel(series?.unit) || "Anomaly", standoff: 8 },
        gridcolor: "rgba(168,190,181,0.12)",
        zerolinecolor: "rgba(241,247,244,0.35)",
        fixedrange: true,
      },
      showlegend: false,
    }),
    [series],
  );

  if (!series) return null;

  const label = `Time series of ${series.variable} annual anomalies from ${
    series.years[0]
  } to ${series.years[series.years.length - 1]}. ${verdictText(series)} at ${
    series.slope_per_decade
      ? formatRate(series.slope_per_decade, series.unit)
      : "no stored rate"
  }.`;

  return (
    <div className="chart-wrap" role="group" aria-label={label}>
      <div className="chart-legend" aria-hidden="true">
        <span>
          <i className="chart-key" /> Annual anomaly
        </span>
        <span>
          <i className="chart-key chart-key--line" /> Theil–Sen trend
        </span>
      </div>
      <Plot
        data={data}
        layout={layout}
        config={{
          displayModeBar: false,
          responsive: true,
          scrollZoom: false,
        }}
        style={{ width: "100%", height: "300px" }}
        useResizeHandler
      />
      <details className="chart-fallback">
        <summary>Data table for the chart</summary>
        <table>
          <caption className="sr-only">
            Annual anomalies and reconstructed trend for {series.variable}
          </caption>
          <thead>
            <tr>
              <th scope="col">Year</th>
              <th scope="col">Anomaly ({unitLabel(series.unit)})</th>
              <th scope="col">Trend ({unitLabel(series.unit)})</th>
            </tr>
          </thead>
          <tbody>
            {series.years.map((year, index) => (
              <tr key={year}>
                <th scope="row">{year}</th>
                <td>{formatNumber(series.annual_anomaly[index])}</td>
                <td>{formatNumber(series.trend_line[index])}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </div>
  );
}
