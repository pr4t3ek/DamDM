(function () {
  const rows = window.SCREENING_ROWS;
  const names = rows.map(r => r.display_name);
  CHART.draw("chart-auc", [{
    type: "bar", x: names, y: rows.map(r => r.auc),
    marker: { color: CHART.PALETTE.primary },
    hovertemplate: "%{x}<br>AUC %{y:.4f}<extra></extra>",
  }], {
    yaxis: { title: "OOT AUC", gridcolor: CHART.PALETTE.grid, range: [0.5, Math.max(...rows.map(r => r.auc)) + 0.05] },
  });
  CHART.draw("chart-capture", [{
    type: "bar", x: names, y: rows.map(r => r.top_decile_capture),
    marker: { color: CHART.PALETTE.risk },
    hovertemplate: "%{x}<br>%{y:.1f}% captured<extra></extra>",
  }], {
    yaxis: { title: "Top-decile capture (%)", gridcolor: CHART.PALETTE.grid, rangemode: "tozero" },
  });
})();
