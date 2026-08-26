(function () {
  const curve = window.ROC_CURVE;
  const nPos = window.N_POS;
  const nNeg = window.N_NEG;
  const n = curve.fpr.length;
  const slider = document.getElementById("threshold-slider");
  slider.max = n - 1;

  function drawRoc(markerIdx) {
    CHART.draw("chart-roc", [
      {
        type: "scatter", mode: "lines", x: curve.fpr, y: curve.tpr,
        line: { color: CHART.PALETTE.primary, width: 3 },
        hovertemplate: "FPR %{x:.3f}<br>TPR %{y:.3f}<extra></extra>",
      },
      {
        type: "scatter", mode: "lines", x: [0, 1], y: [0, 1],
        line: { color: "#b6bfd1", width: 1.5, dash: "dash" },
        hoverinfo: "skip",
      },
      {
        type: "scatter", mode: "markers", x: [curve.fpr[markerIdx]], y: [curve.tpr[markerIdx]],
        marker: { color: CHART.PALETTE.risk, size: 12, line: { color: "#fff", width: 2 } },
        hovertemplate: `threshold ${curve.threshold[markerIdx].toFixed(3)}<extra></extra>`,
      },
    ], {
      xaxis: { title: "False Positive Rate", gridcolor: CHART.PALETTE.grid, range: [0, 1] },
      yaxis: { title: "True Positive Rate", gridcolor: CHART.PALETTE.grid, range: [0, 1] },
    });
  }

  function update() {
    const idx = parseInt(slider.value, 10);
    const fpr = curve.fpr[idx];
    const tpr = curve.tpr[idx];
    const thr = curve.threshold[idx];

    const tp = Math.round(tpr * nPos);
    const fn = nPos - tp;
    const fp = Math.round(fpr * nNeg);
    const tn = nNeg - fp;
    const precision = (tp + fp) > 0 ? tp / (tp + fp) : 0;
    const specificity = 1 - fpr;

    document.getElementById("threshold-value").textContent = "Threshold = " + thr.toFixed(3);
    document.getElementById("v-tp").textContent = tp.toLocaleString();
    document.getElementById("v-fp").textContent = fp.toLocaleString();
    document.getElementById("v-fn").textContent = fn.toLocaleString();
    document.getElementById("v-tn").textContent = tn.toLocaleString();
    document.getElementById("v-precision").textContent = (precision * 100).toFixed(2) + "%";
    document.getElementById("v-recall").textContent = (tpr * 100).toFixed(2) + "%";
    document.getElementById("v-specificity").textContent = (specificity * 100).toFixed(2) + "%";
    document.getElementById("v-volume").textContent = (tp + fp).toLocaleString() +
      " (" + (100 * (tp + fp) / (nPos + nNeg)).toFixed(1) + "% of the portfolio)";

    drawRoc(idx);
  }

  // Start near the 0.5 default threshold used elsewhere in the app, for continuity.
  let startIdx = 0;
  let bestDiff = Infinity;
  for (let i = 0; i < n; i++) {
    const diff = Math.abs(curve.threshold[i] - 0.5);
    if (diff < bestDiff) { bestDiff = diff; startIdx = i; }
  }
  slider.value = startIdx;

  slider.addEventListener("input", update);
  update();
})();
