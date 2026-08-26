(function () {
  const r = window.SCENARIO_RESULT;
  CHART.draw("chart-highrisk", [{
    type: "bar", x: ["Before", "After"],
    y: [r.before.high_risk_accounts, r.after.high_risk_accounts],
    marker: { color: [CHART.PALETTE.neutral, CHART.PALETTE.risk] },
    hovertemplate: "%{x}<br>%{y:,} accounts<extra></extra>",
  }], {
    yaxis: { title: "High/Very High risk accounts", gridcolor: CHART.PALETTE.grid, rangemode: "tozero" },
  });
})();
