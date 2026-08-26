// Shared Plotly styling so every chart in the dashboard reads as one system.
window.CHART = (function () {
  const PALETTE = {
    primary: "#2f6fed",
    primaryDark: "#1f4fb8",
    risk: "#c0392b",
    riskLight: "#e8897d",
    good: "#1a9c62",
    neutral: "#8fa3c8",
    grid: "#e2e7f0",
    text: "#16213a",
    textMuted: "#5b6b8c",
  };

  const LAYOUT = {
    font: { family: "Segoe UI, -apple-system, sans-serif", size: 12, color: PALETTE.text },
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    margin: { l: 60, r: 24, t: 30, b: 60 },
    xaxis: { gridcolor: PALETTE.grid, zerolinecolor: PALETTE.grid },
    yaxis: { gridcolor: PALETTE.grid, zerolinecolor: PALETTE.grid },
    hoverlabel: { bgcolor: "#fff", bordercolor: PALETTE.grid },
    showlegend: false,
  };

  const CONFIG = { displayModeBar: false, responsive: true };

  function merge(base, extra) {
    return Object.assign({}, base, extra || {});
  }

  function draw(elId, traces, layoutExtra) {
    const el = document.getElementById(elId);
    if (!el) return;
    Plotly.react(el, traces, merge(LAYOUT, layoutExtra), CONFIG);
  }

  // A bar of counts with a risk-rate line overlaid on a secondary axis —
  // the recurring "volume vs. risk" view used across the EDA sections.
  function volumeVsRate(elId, labels, counts, rates, opts) {
    opts = opts || {};
    draw(elId, [
      {
        type: "bar", x: labels, y: counts, name: "Observations",
        marker: { color: PALETTE.neutral }, hovertemplate: "%{x}<br>%{y:,} obs<extra></extra>",
      },
      {
        type: "scatter", mode: "lines+markers", x: labels, y: rates, name: "Roll rate %",
        yaxis: "y2", line: { color: PALETTE.risk, width: 3 }, marker: { size: 7 },
        hovertemplate: "%{x}<br>%{y:.2f}% roll rate<extra></extra>",
      },
    ], {
      xaxis: merge(LAYOUT.xaxis, { title: opts.xTitle || "", tickangle: opts.tickangle || 0 }),
      yaxis: merge(LAYOUT.yaxis, { title: "Observations" }),
      yaxis2: {
        title: "Roll rate (%)", overlaying: "y", side: "right",
        gridcolor: "rgba(0,0,0,0)", rangemode: "tozero",
      },
      showlegend: true,
      legend: { orientation: "h", y: 1.12, x: 0 },
      margin: { l: 70, r: 70, t: 40, b: opts.bottomMargin || 60 },
    });
  }

  function histogram(elId, hist, opts) {
    opts = opts || {};
    const edges = hist.bin_edges || [];
    const counts = hist.counts || [];
    const centers = counts.map(function (_, i) { return (edges[i] + edges[i + 1]) / 2; });
    draw(elId, [{
      type: "bar", x: centers, y: counts,
      marker: { color: opts.color || PALETTE.primary },
      hovertemplate: "%{x:.3f}<br>%{y:,} obs<extra></extra>",
    }], {
      bargap: 0.02,
      xaxis: merge(LAYOUT.xaxis, { title: opts.xTitle || "" }),
      yaxis: merge(LAYOUT.yaxis, { title: "Observations" }),
    });
  }

  function horizontalRate(elId, labels, rates, opts) {
    opts = opts || {};
    draw(elId, [{
      type: "bar", orientation: "h", x: rates, y: labels,
      marker: { color: PALETTE.primary },
      hovertemplate: "%{y}<br>%{x:.2f}% roll rate<extra></extra>",
    }], {
      xaxis: merge(LAYOUT.xaxis, { title: "Roll rate (%)" }),
      yaxis: merge(LAYOUT.yaxis, { automargin: true }),
      margin: { l: 140, r: 24, t: 20, b: 50 },
      height: opts.height || Math.max(220, labels.length * 26 + 80),
    });
  }

  function heatmap(elId, columns, matrix) {
    draw(elId, [{
      type: "heatmap", z: matrix, x: columns, y: columns,
      colorscale: [[0, "#c0392b"], [0.5, "#ffffff"], [1, PALETTE.primaryDark]],
      zmid: 0, zmin: -1, zmax: 1,
      hovertemplate: "%{y} vs %{x}<br>r = %{z:.3f}<extra></extra>",
      colorbar: { thickness: 12, len: 0.8 },
    }], {
      margin: { l: 190, r: 20, t: 20, b: 170 },
      height: 620,
      xaxis: { tickangle: -45, automargin: true },
      yaxis: { automargin: true },
    });
  }

  function timeSeries(elId, x, counts, rates) {
    draw(elId, [
      {
        type: "bar", x: x, y: counts, name: "Observations",
        marker: { color: "#dde4f2" }, hovertemplate: "%{x}<br>%{y:,} obs<extra></extra>",
      },
      {
        type: "scatter", mode: "lines", x: x, y: rates, name: "Roll rate %", yaxis: "y2",
        line: { color: PALETTE.risk, width: 3 },
        hovertemplate: "%{x}<br>%{y:.2f}%<extra></extra>",
      },
    ], {
      xaxis: merge(LAYOUT.xaxis, { title: "Observation month" }),
      yaxis: merge(LAYOUT.yaxis, { title: "Observations" }),
      yaxis2: { title: "Roll rate (%)", overlaying: "y", side: "right", gridcolor: "rgba(0,0,0,0)", rangemode: "tozero" },
      showlegend: true,
      legend: { orientation: "h", y: 1.12, x: 0 },
      margin: { l: 70, r: 70, t: 40, b: 60 },
    });
  }

  return { PALETTE, draw, volumeVsRate, histogram, horizontalRate, heatmap, timeSeries };
})();
