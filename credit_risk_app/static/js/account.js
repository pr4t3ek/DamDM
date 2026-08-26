(function () {
  const rows = window.ACCOUNT_TIMELINE;
  const x = rows.map(r => r.month_end_date);
  CHART.draw("chart-timeline", [
    {
      type: "scatter", mode: "lines", x: x, y: rows.map(r => r.dpd), name: "DPD", yaxis: "y2",
      line: { color: CHART.PALETTE.risk, width: 2 },
    },
    {
      type: "scatter", mode: "lines", x: x, y: rows.map(r => r.utilization_ratio * 100), name: "Utilization %",
      line: { color: CHART.PALETTE.primary, width: 2 },
    },
    {
      type: "scatter", mode: "lines", x: x, y: rows.map(r => r.payment_ratio * 100), name: "Payment Ratio %",
      line: { color: CHART.PALETTE.good, width: 2 },
    },
  ], {
    xaxis: { title: "Month", gridcolor: CHART.PALETTE.grid, tickangle: -45 },
    yaxis: { title: "Utilization / Payment Ratio (%)", gridcolor: CHART.PALETTE.grid },
    yaxis2: { title: "DPD", overlaying: "y", side: "right", gridcolor: "rgba(0,0,0,0)", rangemode: "tozero" },
    showlegend: true,
    legend: { orientation: "h", y: 1.12, x: 0 },
    margin: { l: 65, r: 65, t: 44, b: 90 },
  });
})();
