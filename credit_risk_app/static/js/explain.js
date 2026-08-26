(function () {
  function horizontalBar(elId, rows, valueKey, color) {
    const sorted = rows.slice().reverse();
    CHART.draw(elId, [{
      type: "bar", orientation: "h",
      x: sorted.map(r => r[valueKey]),
      y: sorted.map(r => r.feature),
      marker: { color: color },
      hovertemplate: "%{y}<br>%{x:.4f}<extra></extra>",
    }], {
      xaxis: { gridcolor: CHART.PALETTE.grid },
      yaxis: { automargin: true, gridcolor: CHART.PALETTE.grid },
      margin: { l: 190, r: 20, t: 10, b: 40 },
      height: Math.max(360, sorted.length * 24 + 60),
    });
  }

  horizontalBar("chart-native", window.NATIVE_IMPORTANCE, "importance", CHART.PALETTE.primary);
  horizontalBar("chart-permutation", window.PERMUTATION_IMPORTANCE, "auc_drop", CHART.PALETTE.risk);
  horizontalBar("chart-shap", window.SHAP_IMPORTANCE, "mean_abs_shap", CHART.PALETTE.good);
})();
