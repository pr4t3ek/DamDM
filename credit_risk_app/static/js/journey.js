(function () {
  const controls = document.getElementById("sim-controls");
  const inputs = controls.querySelectorAll("select");
  const resetBtn = document.getElementById("sim-reset");
  const defaults = {};
  inputs.forEach(function (el) { defaults[el.name] = el.value; });

  const BANDS = [
    { max: 5, label: "Low", color: CHART.PALETTE.good, action: "Standard monitoring." },
    { max: 15, label: "Medium", color: CHART.PALETTE.amber || "#b8860b", action: "Watch-list; consider a reminder." },
    { max: 30, label: "High", color: "#d3652f", action: "Proactive outreach recommended." },
    { max: 101, label: "Very High", color: CHART.PALETTE.risk, action: "Priority intervention / restructuring review." },
  ];

  function bandFor(rate) {
    return BANDS.find(function (b) { return rate <= b.max; }) || BANDS[BANDS.length - 1];
  }

  function fmtPct(x) { return x === null || x === undefined ? "&mdash;" : x + "%"; }

  function render(d) {
    document.getElementById("sim-rate").textContent = d.cohort_roll_rate === null ? "n/a" : d.cohort_roll_rate + "%";
    document.getElementById("sim-n").textContent = d.cohort_observations.toLocaleString() + " matching observations";
    document.getElementById("sim-lift").textContent = d.lift === null ? "&mdash;" : d.lift + "x";

    const warnEl = document.getElementById("sim-sparse-warning");
    warnEl.innerHTML = d.sparse
      ? `<div class="coming-soon-note" style="margin-top:14px;">Small cohort (${d.cohort_observations.toLocaleString()} observations) &mdash; this rate is noisier than the well-populated combinations.</div>`
      : "";

    const bandEl = document.getElementById("sim-band");
    const actionEl = document.getElementById("sim-action");
    if (d.cohort_roll_rate === null) {
      bandEl.textContent = "n/a";
      actionEl.textContent = "";
    } else {
      const band = bandFor(d.cohort_roll_rate);
      bandEl.textContent = band.label;
      bandEl.style.color = band.color;
      actionEl.textContent = band.action;
    }

    const c = d.contributions;
    CHART.draw("chart-sim-factors", [{
      type: "bar", orientation: "h",
      x: c.map(f => f.roll_rate),
      y: c.map(f => f.factor),
      marker: { color: CHART.PALETTE.primary },
      hovertemplate: "%{y}<br>%{x:.2f}% roll rate<extra></extra>",
    }], {
      xaxis: { title: "Roll rate for accounts matching this factor alone (%)", gridcolor: CHART.PALETTE.grid },
      yaxis: { automargin: true, gridcolor: CHART.PALETTE.grid },
      margin: { l: 140, r: 24, t: 10, b: 50 },
      shapes: [{
        type: "line", xref: "x", yref: "paper", x0: d.baseline_roll_rate, x1: d.baseline_roll_rate, y0: 0, y1: 1,
        line: { color: CHART.PALETTE.risk, width: 2, dash: "dash" },
      }],
    });
  }

  function load() {
    const params = new URLSearchParams();
    inputs.forEach(function (el) { params.set(el.name, el.value); });
    fetch(`${window.COHORT_URL}?${params.toString()}`).then(r => r.json()).then(render);
  }

  inputs.forEach(function (el) { el.addEventListener("change", load); });
  resetBtn.addEventListener("click", function () {
    inputs.forEach(function (el) { el.value = defaults[el.name]; });
    load();
  });

  load();
})();
