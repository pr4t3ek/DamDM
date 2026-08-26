(function () {
  const form = document.getElementById("explorer-filters");
  const tbody = document.getElementById("explorer-tbody");
  const countLabel = document.getElementById("explorer-count");
  const pageLabel = document.getElementById("explorer-page-label");
  const prevBtn = document.getElementById("explorer-prev");
  const nextBtn = document.getElementById("explorer-next");
  const pageSize = 25;
  let page = 1;
  let total = 0;

  function buildQuery(extra) {
    const params = new URLSearchParams(new FormData(form));
    params.set("page", extra.page || page);
    params.set("page_size", pageSize);
    return params.toString();
  }

  function renderRows(rows) {
    if (!rows.length) {
      tbody.innerHTML = '<tr><td colspan="9" style="text-align:center;color:var(--text-muted);padding:20px;">No matching observations.</td></tr>';
      return;
    }
    tbody.innerHTML = rows.map(function (r) {
      const badge = r.roll_to_90p_6m === 1 ? '<span class="badge badge-red">Rolls 90p</span>' : '<span class="badge badge-green">No roll</span>';
      return `<tr>
        <td>${r.month_end_date}</td>
        <td>${r.customer_id}</td>
        <td>${r.trade_id}</td>
        <td>${r.lender_id}</td>
        <td>${r.product}</td>
        <td>${r.state}, ${r.city_tier}</td>
        <td>${Number(r.current_balance).toLocaleString(undefined, {maximumFractionDigits: 0})}</td>
        <td>${(Number(r.utilization_ratio) * 100).toFixed(1)}%</td>
        <td>${r.dpd}</td>
        <td>${r.account_status}</td>
        <td>${badge}</td>
      </tr>`;
    }).join("");
  }

  function load() {
    const qs = buildQuery({page: page});
    fetch(`${window.EXPLORER_QUERY_URL}?${qs}`)
      .then(function (res) { return res.json(); })
      .then(function (data) {
        total = data.total;
        renderRows(data.rows);
        const lastPage = Math.max(Math.ceil(total / pageSize), 1);
        countLabel.textContent = `${total.toLocaleString()} matching observation(s)`;
        pageLabel.textContent = `Page ${page} of ${lastPage}`;
        prevBtn.disabled = page <= 1;
        nextBtn.disabled = page >= lastPage;
      });
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    page = 1;
    load();
  });
  form.addEventListener("reset", function () {
    page = 1;
    setTimeout(load, 0);
  });
  prevBtn.addEventListener("click", function () {
    if (page > 1) { page -= 1; load(); }
  });
  nextBtn.addEventListener("click", function () {
    page += 1;
    load();
  });
})();
