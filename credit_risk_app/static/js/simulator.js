(function () {
  const sliders = Array.from(document.querySelectorAll('#sim-sliders input[type="range"]'));
  const toggles = Array.from(document.querySelectorAll('#sim-sliders input[type="checkbox"]'));
  const resetBtn = document.getElementById("sim-reset");
  const defaults = {};
  sliders.forEach(function (el) { defaults[el.dataset.name] = el.value; });

  const BAND_COLORS = { Low: "var(--green)", Medium: "var(--amber)", High: "#d3652f", "Very High": "var(--red)" };

  function formatValue(el) {
    const v = parseFloat(el.value);
    return el.dataset.pct === "true" ? (v * 100).toFixed(0) + "%" : v.toLocaleString();
  }

  function updateLabels() {
    sliders.forEach(function (el) {
      document.getElementById("val-" + el.dataset.name).textContent = formatValue(el);
    });
  }

  let lastResult = null;

  function fetchScore() {
    const params = new URLSearchParams();
    sliders.forEach(function (el) { params.set(el.dataset.name, el.value); });
    toggles.forEach(function (el) { params.set(el.dataset.name, el.checked ? "1" : "0"); });

    fetch(`${window.SCORE_URL}?${params.toString()}`)
      .then(r => r.json())
      .then(function (d) {
        document.getElementById("out-probability").textContent = (d.probability * 100).toFixed(1) + "%";
        document.getElementById("out-percentile").textContent = "Percentile " + d.percentile + " of OOT accounts";
        document.getElementById("out-band").textContent = d.band.label;
        document.getElementById("out-band").style.color = BAND_COLORS[d.band.label] || "var(--text)";
        document.getElementById("out-action").textContent = d.band.action;
        document.getElementById("out-probability-pct").innerHTML = `<strong>${(d.probability * 100).toFixed(1)}%</strong>`;
        document.getElementById("out-band-badge").innerHTML =
          `<span class="badge" style="background:${BAND_COLORS[d.band.label]}22; color:${BAND_COLORS[d.band.label]};">${d.band.label}</span>`;

        const baseline = window.BASELINE_PROBABILITY;
        const deltaEl = document.getElementById("out-delta");
        const diff = d.probability - baseline;
        if (Math.abs(diff) < 0.0005) {
          deltaEl.textContent = "No change from baseline.";
        } else {
          const dir = diff > 0 ? "higher" : "lower";
          deltaEl.textContent = `${Math.abs(diff * 100).toFixed(1)} percentage points ${dir} than the typical account, now derived account status: ${d.account_status}.`;
        }
        lastResult = d;
      });
  }

  updateLabels();
  fetchScore();

  sliders.forEach(function (el) {
    el.addEventListener("input", function () { updateLabels(); fetchScore(); });
  });
  toggles.forEach(function (el) {
    el.addEventListener("change", fetchScore);
  });
  resetBtn.addEventListener("click", function () {
    sliders.forEach(function (el) { el.value = defaults[el.dataset.name]; });
    toggles.forEach(function (el) { el.checked = false; });
    updateLabels();
    fetchScore();
  });
})();
