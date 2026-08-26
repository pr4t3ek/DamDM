(function () {
  const FAMILY_COLORS = {
    Trend: "#2f6fed", Rolling: "#1a9c62", Volatility: "#b8860b",
    Stress: "#c0392b", Momentum: "#7c5cc4", Context: "#8fa3c8",
  };

  const entries = Object.entries(window.FEATURE_CACHE)
    .filter(([, f]) => f.target_corr !== null)
    .sort((a, b) => Math.abs(a[1].target_corr) - Math.abs(b[1].target_corr));

  CHART.draw("chart-signal", [{
    type: "bar", orientation: "h",
    x: entries.map(e => e[1].target_corr),
    y: entries.map(e => e[0]),
    marker: { color: entries.map(e => FAMILY_COLORS[e[1].family] || CHART.PALETTE.neutral) },
    hovertemplate: "%{y}<br>r = %{x:.4f}<extra></extra>",
  }], {
    xaxis: { title: "Correlation with roll_to_90p_6m", gridcolor: CHART.PALETTE.grid, zeroline: true, zerolinecolor: "#94a3b8" },
    yaxis: { automargin: true, gridcolor: CHART.PALETTE.grid },
    margin: { l: 210, r: 30, t: 20, b: 55 },
    height: Math.max(320, entries.length * 26 + 80),
  });

  const form = document.getElementById("sample-form");
  const tbody = document.getElementById("sample-tbody");
  const label = document.getElementById("sample-label");

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    const qs = new URLSearchParams(new FormData(form)).toString();
    fetch(`${window.SAMPLE_URL}?${qs}`).then(r => r.json()).then(function (d) {
      label.textContent = d.trade_id;
      if (!d.rows.length) {
        tbody.innerHTML = `<tr><td colspan="${window.FEATURE_NAMES.length + 1}" style="text-align:center;color:var(--text-muted);padding:18px;">No account found with that ID.</td></tr>`;
        return;
      }
      tbody.innerHTML = d.rows.map(function (r) {
        const cells = window.FEATURE_NAMES.map(n => `<td>${r[n] === null || r[n] === undefined ? "—" : r[n]}</td>`).join("");
        return `<tr><td>${r.month_end_date}</td>${cells}</tr>`;
      }).join("");
    });
  });
})();
