(function () {
  const curve = window.CAPACITY_CURVE;
  CHART.draw("chart-capacity", [
    {
      type: "bar", x: curve.map(c => c.capacity_pct + "%"), y: curve.map(c => c.accounts_contacted),
      name: "Accounts contacted", marker: { color: CHART.PALETTE.neutral },
      hovertemplate: "%{x} capacity<br>%{y:,} accounts<extra></extra>",
    },
    {
      type: "scatter", mode: "lines+markers", x: curve.map(c => c.capacity_pct + "%"), y: curve.map(c => c.capture_rate),
      name: "Capture rate %", yaxis: "y2", line: { color: CHART.PALETTE.risk, width: 3 }, marker: { size: 8 },
      hovertemplate: "%{x} capacity<br>%{y:.1f}% of bads captured<extra></extra>",
    },
  ], {
    xaxis: { title: "Collection capacity", gridcolor: CHART.PALETTE.grid },
    yaxis: { title: "Accounts contacted", gridcolor: CHART.PALETTE.grid },
    yaxis2: { title: "Capture rate (%)", overlaying: "y", side: "right", gridcolor: "rgba(0,0,0,0)", rangemode: "tozero" },
    showlegend: true,
    legend: { orientation: "h", y: 1.12, x: 0 },
    margin: { l: 65, r: 65, t: 40, b: 50 },
  });

  const tbody = document.getElementById("queue-tbody");
  const countEl = document.getElementById("queue-count");
  const pageLabel = document.getElementById("queue-page-label");
  const prevBtn = document.getElementById("queue-prev");
  const nextBtn = document.getElementById("queue-next");
  const pageSize = 25;
  let page = 1;
  let nCapacity = 0;

  function badgeFor(band) {
    if (band === "Very High") return '<span class="badge badge-red">Very High</span>';
    if (band === "High") return '<span class="badge" style="background:#fdeee9;color:#d3652f;">High</span>';
    return `<span class="badge badge-amber">${band}</span>`;
  }

  function render(rows) {
    tbody.innerHTML = rows.map(r => `<tr>
      <td>${r.risk_rank}</td>
      <td><code>${r.trade_id}</code></td>
      <td>${r.product}</td>
      <td><strong>${(r.predicted_probability * 100).toFixed(1)}%</strong></td>
      <td>${badgeFor(r.risk_band)}</td>
      <td>${Number(r.current_balance).toLocaleString(undefined, {maximumFractionDigits: 0})}</td>
      <td>${r.dpd}</td>
      <td>${r.roll_to_90p_6m === 1 ? '<span class="badge badge-red">Yes</span>' : '<span class="badge badge-green">No</span>'}</td>
    </tr>`).join("");
  }

  function load() {
    const params = new URLSearchParams({ capacity: window.SELECTED_CAPACITY, page: page, page_size: pageSize });
    fetch(`${window.QUEUE_PAGE_URL}?${params.toString()}`).then(r => r.json()).then(function (d) {
      nCapacity = d.n_capacity;
      render(d.rows);
      const start = (page - 1) * pageSize + 1;
      const end = Math.min(page * pageSize, nCapacity);
      countEl.textContent = `Showing ${start.toLocaleString()}–${end.toLocaleString()} of ${nCapacity.toLocaleString()} in queue`;
      const lastPage = Math.max(Math.ceil(nCapacity / pageSize), 1);
      pageLabel.textContent = `Page ${page} of ${lastPage}`;
      prevBtn.disabled = page <= 1;
      nextBtn.disabled = page >= lastPage;
    });
  }

  prevBtn.addEventListener("click", function () { if (page > 1) { page -= 1; load(); } });
  nextBtn.addEventListener("click", function () { page += 1; load(); });
})();
