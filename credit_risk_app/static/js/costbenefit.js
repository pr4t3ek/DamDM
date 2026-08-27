(function () {
  const rows = window.NET_BENEFIT_ROWS;
  const best = window.BEST_CAPACITY_PCT;
  CHART.draw("chart-netbenefit", [
    {
      type: "bar", x: rows.map(r => r.capacity_pct + "%"), y: rows.map(r => r.net_benefit),
      name: "Net benefit (₹)",
      marker: { color: rows.map(r => r.capacity_pct === best ? CHART.PALETTE.good : CHART.PALETTE.neutral) },
      hovertemplate: "%{x} capacity<br>₹%{y:,.0f} net benefit<extra></extra>",
    },
    {
      type: "scatter", mode: "lines+markers", x: rows.map(r => r.capacity_pct + "%"), y: rows.map(r => r.roi_multiple),
      name: "ROI multiple", yaxis: "y2", line: { color: CHART.PALETTE.risk, width: 3 }, marker: { size: 8 },
      hovertemplate: "%{x} capacity<br>%{y:.2f}× ROI<extra></extra>",
    },
  ], {
    xaxis: { title: "Collection capacity", gridcolor: CHART.PALETTE.grid },
    yaxis: { title: "Net benefit (₹)", gridcolor: CHART.PALETTE.grid },
    yaxis2: { title: "ROI multiple", overlaying: "y", side: "right", gridcolor: "rgba(0,0,0,0)", rangemode: "tozero" },
    showlegend: true,
    legend: { orientation: "h", y: 1.12, x: 0 },
    margin: { l: 75, r: 65, t: 40, b: 50 },
  });

  const tRows = window.THRESHOLD_COST_ROWS;
  const bestT = window.BEST_THRESHOLD;
  CHART.draw("chart-thresholdcost", [
    {
      type: "scatter", mode: "lines+markers", x: tRows.map(r => r.threshold), y: tRows.map(r => r.total_cost),
      name: "Total cost (₹)",
      line: { color: CHART.PALETTE.risk, width: 3 },
      marker: {
        size: tRows.map(r => r.threshold === bestT ? 12 : 7),
        color: tRows.map(r => r.threshold === bestT ? CHART.PALETTE.good : CHART.PALETTE.risk),
      },
      hovertemplate: "threshold %{x}<br>₹%{y:,.0f} total cost<extra></extra>",
    },
    {
      type: "scatter", mode: "lines", x: tRows.map(r => r.threshold), y: tRows.map(r => r.recall),
      name: "Recall %", yaxis: "y2", line: { color: CHART.PALETTE.neutral, width: 2, dash: "dot" },
      hovertemplate: "threshold %{x}<br>%{y:.1f}% recall<extra></extra>",
    },
  ], {
    xaxis: { title: "Probability threshold", gridcolor: CHART.PALETTE.grid },
    yaxis: { title: "Total cost (₹)", gridcolor: CHART.PALETTE.grid },
    yaxis2: { title: "Recall (%)", overlaying: "y", side: "right", gridcolor: "rgba(0,0,0,0)", rangemode: "tozero" },
    showlegend: true,
    legend: { orientation: "h", y: 1.12, x: 0 },
    margin: { l: 75, r: 65, t: 40, b: 50 },
  });
})();
