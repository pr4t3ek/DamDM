(function () {
  const form = document.getElementById("split-form");
  const tbody = document.getElementById("split-tbody");
  const warnBox = document.getElementById("split-warnings");
  const overlapBox = document.getElementById("overlap-box");

  const PERIOD_COLORS = {
    train: CHART.PALETTE.primary,
    validation: "#7c9fe8",
    test: CHART.PALETTE.risk,
  };

  function fmt(n) { return n === null || n === undefined ? "&mdash;" : Number(n).toLocaleString(); }

  function renderMaturityChart(monthly, maturity) {
    const x = monthly.map(r => r.month);
    const y = monthly.map(r => r.event_rate);
    const cutoff = maturity.last_mature_month;
    const mature = monthly.map(r => (r.month <= cutoff ? r.event_rate : null));
    const censored = monthly.map(r => (r.month >= cutoff ? r.event_rate : null));
    CHART.draw("chart-maturity", [
      {
        type: "scatter", mode: "lines", x: x, y: mature, name: "Mature labels",
        line: { color: CHART.PALETTE.primary, width: 3 },
        hovertemplate: "%{x}<br>%{y:.2f}%<extra></extra>",
      },
      {
        type: "scatter", mode: "lines", x: x, y: censored, name: "Right-censored (excluded)",
        line: { color: CHART.PALETTE.risk, width: 3, dash: "dot" },
        hovertemplate: "%{x}<br>%{y:.2f}% (censored)<extra></extra>",
      },
    ], {
      xaxis: { title: "Observation month", gridcolor: CHART.PALETTE.grid, tickangle: -45 },
      yaxis: { title: "Event rate (%)", gridcolor: CHART.PALETTE.grid, rangemode: "tozero" },
      showlegend: true,
      legend: { orientation: "h", y: 1.14, x: 0 },
      margin: { l: 65, r: 24, t: 44, b: 90 },
      shapes: [{
        type: "rect", xref: "x", yref: "paper",
        x0: cutoff, x1: x[x.length - 1], y0: 0, y1: 1,
        fillcolor: "rgba(192,57,43,0.07)", line: { width: 0 }, layer: "below",
      }],
    });
  }

  function render(d) {
    const order = [["train", "Training"], ["validation", "Validation"], ["test", "OOT Test"]];
    tbody.innerHTML = order.map(function ([key, label]) {
      const p = d.periods[key];
      return `<tr>
        <td><span class="badge" style="background:${PERIOD_COLORS[key]}22;color:${PERIOD_COLORS[key]};">${label}</span></td>
        <td>${p.start} &rarr; ${p.end}</td>
        <td>${p.n_months}</td>
        <td>${fmt(p.observations)}</td>
        <td>${fmt(p.accounts)}</td>
        <td>${fmt(p.customers)}</td>
        <td>${fmt(p.events)}</td>
        <td><strong>${p.event_rate === null ? "&mdash;" : p.event_rate + "%"}</strong></td>
      </tr>`;
    }).join("") + `<tr style="opacity:0.65;">
        <td><span class="badge badge-red">Excluded</span></td>
        <td>${d.excluded_immature.start} &rarr; ${d.excluded_immature.end}</td>
        <td>${d.excluded_immature.n_months}</td>
        <td>${fmt(d.excluded_immature.observations)}</td>
        <td>${fmt(d.excluded_immature.accounts)}</td>
        <td>${fmt(d.excluded_immature.customers)}</td>
        <td>${fmt(d.excluded_immature.events)}</td>
        <td>${d.excluded_immature.event_rate}% <span style="color:var(--text-muted);">(censored)</span></td>
      </tr>`;

    warnBox.innerHTML = d.warnings.length
      ? `<div class="coming-soon-note"><strong>Check your split:</strong><ul style="margin:6px 0 0 18px;">${
          d.warnings.map(w => `<li>${w}</li>`).join("")}</ul></div>`
      : "";

    CHART.draw("chart-split-rate", [{
      type: "bar",
      x: order.map(o => o[1]),
      y: order.map(o => d.periods[o[0]].event_rate),
      marker: { color: order.map(o => PERIOD_COLORS[o[0]]) },
      hovertemplate: "%{x}<br>%{y:.3f}% event rate<extra></extra>",
    }], {
      yaxis: { title: "Event rate (%)", gridcolor: CHART.PALETTE.grid, rangemode: "tozero" },
    });

    const o = d.overlap;
    overlapBox.innerHTML = `
      <div class="bar-row"><div class="bar-label">Train &cap; Validation</div><div class="bar-value" style="text-align:left;">${fmt(o.train_validation)} accounts</div></div>
      <div class="bar-row"><div class="bar-label">Train &cap; OOT Test</div><div class="bar-value" style="text-align:left;">${fmt(o.train_test)} accounts</div></div>
      <div class="bar-row"><div class="bar-label">Validation &cap; OOT Test</div><div class="bar-value" style="text-align:left;">${fmt(o.validation_test)} accounts</div></div>`;

    renderMaturityChart(d.monthly_roll_rate, d.maturity);
  }

  function load() {
    const qs = new URLSearchParams(new FormData(form)).toString();
    fetch(`${window.SPLIT_DATA_URL}?${qs}`).then(r => r.json()).then(render);
  }

  form.addEventListener("submit", function (e) { e.preventDefault(); load(); });
  form.addEventListener("reset", function () {
    setTimeout(function () {
      Object.entries(window.SPLIT_DEFAULTS).forEach(function ([k, v]) {
        const el = form.elements[k];
        if (el) el.value = v;
      });
      load();
    }, 0);
  });

  load();
})();
