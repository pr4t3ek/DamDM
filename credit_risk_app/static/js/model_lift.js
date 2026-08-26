(function () {
  const rows = window.DECILE_TABLE;
  const deciles = rows.map(r => "D" + r.decile);

  CHART.draw("chart-lift", [
    {
      type: "bar", x: deciles, y: rows.map(r => r.lift),
      marker: { color: CHART.PALETTE.primary },
      hovertemplate: "%{x}<br>lift %{y:.2f}x<extra></extra>",
    },
  ], {
    xaxis: { title: "Decile (1 = riskiest)", gridcolor: CHART.PALETTE.grid },
    yaxis: { title: "Lift", gridcolor: CHART.PALETTE.grid },
    shapes: [{
      type: "line", xref: "paper", yref: "y", x0: 0, x1: 1, y0: 1, y1: 1,
      line: { color: CHART.PALETTE.risk, width: 1.5, dash: "dash" },
    }],
  });

  const gainsX = [0, ...rows.map(r => r.decile * 10)];
  const gainsY = [0, ...rows.map(r => r.capture_rate)];
  CHART.draw("chart-gains", [
    {
      type: "scatter", mode: "lines+markers", x: gainsX, y: gainsY,
      line: { color: CHART.PALETTE.primary, width: 3 },
      hovertemplate: "%{x}% of accounts<br>%{y:.1f}% of bads captured<extra></extra>",
    },
    {
      type: "scatter", mode: "lines", x: [0, 100], y: [0, 100],
      line: { color: "#b6bfd1", width: 1.5, dash: "dash" }, hoverinfo: "skip",
    },
  ], {
    xaxis: { title: "% of accounts (ranked by risk)", gridcolor: CHART.PALETTE.grid, range: [0, 100] },
    yaxis: { title: "% of bad accounts captured", gridcolor: CHART.PALETTE.grid, range: [0, 100] },
  });
})();
