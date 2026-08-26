(function () {
  const fi = window.FEATURE_IMPORTANCE.slice().reverse();
  CHART.draw("chart-importance", [{
    type: "bar", orientation: "h",
    x: fi.map(f => f.importance),
    y: fi.map(f => f.feature),
    marker: { color: CHART.PALETTE.primary },
    hovertemplate: "%{y}<br>importance %{x:.4f}<extra></extra>",
  }], {
    xaxis: { title: "Importance", gridcolor: CHART.PALETTE.grid },
    yaxis: { automargin: true, gridcolor: CHART.PALETTE.grid },
    margin: { l: 200, r: 24, t: 10, b: 50 },
    height: Math.max(360, fi.length * 22 + 60),
  });

  const h = window.PRED_HIST;
  const edges = h.bin_edges;
  const centers = h.counts.map((_, i) => (edges[i] + edges[i + 1]) / 2);
  CHART.draw("chart-pred-dist", [{
    type: "bar", x: centers, y: h.counts,
    marker: { color: CHART.PALETTE.primary },
    hovertemplate: "score %{x:.3f}<br>%{y:,} obs<extra></extra>",
  }], {
    bargap: 0.02,
    xaxis: { title: "Predicted probability of rolling to 90+ DPD", gridcolor: CHART.PALETTE.grid, range: [0, 1] },
    yaxis: { title: "Observations", gridcolor: CHART.PALETTE.grid },
  });
})();
