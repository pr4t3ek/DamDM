(function () {
  const d = window.CLASS_DIST;
  const ks = window.KS_STAT;
  // bin_edges has N+1 points for N bins; use the right edge of each bin as the CDF x-value.
  const x = d.bin_edges.slice(1);

  CHART.draw("chart-ks", [
    {
      type: "scatter", mode: "lines", x: x, y: d.good.cdf.map(v => v * 100), name: "Cumulative % — stayed current",
      line: { color: CHART.PALETTE.good, width: 3 },
      hovertemplate: "score &le; %{x:.2f}<br>%{y:.1f}% of goods<extra></extra>",
    },
    {
      type: "scatter", mode: "lines", x: x, y: d.bad.cdf.map(v => v * 100), name: "Cumulative % — rolled to 90+",
      line: { color: CHART.PALETTE.risk, width: 3 },
      hovertemplate: "score &le; %{x:.2f}<br>%{y:.1f}% of bads<extra></extra>",
    },
  ], {
    xaxis: { title: "Predicted probability", gridcolor: CHART.PALETTE.grid, range: [0, 1] },
    yaxis: { title: "Cumulative %", gridcolor: CHART.PALETTE.grid, range: [0, 100] },
    showlegend: true,
    legend: { orientation: "h", y: 1.12, x: 0 },
    margin: { l: 65, r: 24, t: 44, b: 55 },
    shapes: ks.threshold === null ? [] : [{
      type: "line", xref: "x", yref: "paper", x0: ks.threshold, x1: ks.threshold, y0: 0, y1: 1,
      line: { color: CHART.PALETTE.text, width: 2, dash: "dash" },
    }],
    annotations: ks.threshold === null ? [] : [{
      x: ks.threshold, y: 50, yref: "y", xref: "x", showarrow: false,
      text: `KS = ${(ks.ks * 100).toFixed(1)}%`, font: { size: 12, color: CHART.PALETTE.text },
      bgcolor: "#ffffff", bordercolor: CHART.PALETTE.grid, borderwidth: 1, borderpad: 4,
      xanchor: ks.threshold > 0.5 ? "right" : "left", xshift: ks.threshold > 0.5 ? -10 : 10,
    }],
  });
})();
