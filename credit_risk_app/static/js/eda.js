(function () {
  const filtersForm = document.getElementById("eda-filters");
  const tabs = document.querySelectorAll(".tab-btn");
  const panels = document.querySelectorAll(".tab-panel");
  const loaded = {};
  let activeTab = "target";

  function filterQuery() {
    return new URLSearchParams(new FormData(filtersForm)).toString();
  }

  function setLoading(panelId, isLoading) {
    const el = document.querySelector(`#panel-${panelId} .panel-loading`);
    if (el) el.style.display = isLoading ? "block" : "none";
  }

  function fetchSection(name) {
    setLoading(name, true);
    return fetch(`${window.EDA_DATA_URL}/${name}?${filterQuery()}`)
      .then(function (r) { return r.json(); })
      .then(function (d) { setLoading(name, false); return d; })
      .catch(function (e) { setLoading(name, false); throw e; });
  }

  const renderers = {
    target: function (d) {
      document.getElementById("target-n").textContent = d.n.toLocaleString();
      document.getElementById("target-events").textContent = d.positive.toLocaleString();
      document.getElementById("target-nonevents").textContent = d.negative.toLocaleString();
      document.getElementById("target-rate").textContent = (d.event_rate === null ? "n/a" : d.event_rate + "%");
      CHART.draw("chart-target-class", [{
        type: "bar",
        x: ["No roll (0)", "Rolls to 90+ DPD (1)"],
        y: [d.negative, d.positive],
        marker: { color: [CHART.PALETTE.good, CHART.PALETTE.risk] },
        hovertemplate: "%{x}<br>%{y:,} obs<extra></extra>",
      }], { yaxis: { title: "Observations", gridcolor: CHART.PALETTE.grid } });

      const m = d.monthly_roll_rate;
      CHART.timeSeries("chart-target-monthly",
        m.map(r => r.month), m.map(r => r.observations), m.map(r => r.event_rate));

      const p = d.product_roll_rate;
      CHART.volumeVsRate("chart-target-product",
        p.map(r => r.product), p.map(r => r.observations), p.map(r => r.event_rate),
        { tickangle: -30, bottomMargin: 110 });
    },

    delinquency: function (d) {
      const dpd = d.dpd_distribution;
      CHART.volumeVsRate("chart-dpd-dist",
        dpd.map(r => r.bucket), dpd.map(r => r.observations), dpd.map(r => r.event_rate),
        { xTitle: "DPD bucket" });
      const st = d.account_status_distribution;
      CHART.volumeVsRate("chart-status-dist",
        st.map(r => r.account_status), st.map(r => r.observations), st.map(r => r.event_rate),
        { tickangle: -25, bottomMargin: 90 });
      CHART.histogram("chart-apd-hist", d.amount_past_due_histogram,
        { xTitle: "Amount past due", color: CHART.PALETTE.riskLight });
    },

    payment: function (d) {
      document.getElementById("payment-bounce-rate").textContent =
        (d.bounce_rate === null ? "n/a" : d.bounce_rate + "%");
      document.getElementById("payment-partial-rate").textContent =
        (d.partial_payment_rate === null ? "n/a" : d.partial_payment_rate + "%");
      CHART.histogram("chart-payment-ratio-hist", d.payment_ratio_histogram,
        { xTitle: "Payment ratio" });
      const b = d.risk_by_payment_ratio_bucket;
      CHART.volumeVsRate("chart-payment-buckets",
        b.map(r => r.bucket), b.map(r => r.observations), b.map(r => r.event_rate),
        { xTitle: "Payment ratio bucket" });
      const rb = d.recent_bounce_count_distribution;
      CHART.draw("chart-bounce-count", [{
        type: "bar", x: rb.map(r => String(r.count)), y: rb.map(r => r.observations),
        marker: { color: CHART.PALETTE.primary },
        hovertemplate: "%{x} bounces<br>%{y:,} obs<extra></extra>",
      }], {
        xaxis: { title: "Bounces in last 3 months", gridcolor: CHART.PALETTE.grid },
        yaxis: { title: "Observations", gridcolor: CHART.PALETTE.grid },
      });
    },

    utilization: function (d) {
      CHART.histogram("chart-util-hist", d.utilization_histogram, { xTitle: "Utilization ratio" });
      const b = d.risk_by_utilization_bucket;
      CHART.volumeVsRate("chart-util-buckets",
        b.map(r => r.bucket), b.map(r => r.observations), b.map(r => r.event_rate),
        { xTitle: "Utilization bucket" });
      const dp = d.avg_dpd_by_utilization_bucket;
      CHART.draw("chart-util-dpd", [{
        type: "bar", x: dp.map(r => r.bucket), y: dp.map(r => r.avg_dpd),
        marker: { color: CHART.PALETTE.riskLight },
        hovertemplate: "%{x}<br>avg DPD %{y:.2f}<extra></extra>",
      }], {
        xaxis: { title: "Utilization bucket", gridcolor: CHART.PALETTE.grid },
        yaxis: { title: "Average DPD", gridcolor: CHART.PALETTE.grid },
      });
    },

    affordability: function (d) {
      CHART.histogram("chart-bti-hist", d.balance_to_income_histogram, { xTitle: "Balance-to-income ratio" });
      CHART.histogram("chart-emi-hist", d.emi_due_histogram, { xTitle: "EMI due" });
      CHART.histogram("chart-balance-hist", d.current_balance_histogram, { xTitle: "Current balance" });
      CHART.histogram("chart-ead-hist", d.ead_estimate_histogram,
        { xTitle: "EAD estimate", color: CHART.PALETTE.neutral });
    },

    portfolio: function (d) {
      CHART.horizontalRate("chart-pf-product", d.by_product.map(r => r.product), d.by_product.map(r => r.event_rate));
      CHART.horizontalRate("chart-pf-state", d.by_state.map(r => r.state), d.by_state.map(r => r.event_rate));
      CHART.horizontalRate("chart-pf-tier", d.by_city_tier.map(r => r.city_tier), d.by_city_tier.map(r => r.event_rate));
      CHART.horizontalRate("chart-pf-ctype", d.by_customer_type.map(r => r.customer_type), d.by_customer_type.map(r => r.event_rate));
      CHART.horizontalRate("chart-pf-lender", d.by_lender.map(r => r.lender_id), d.by_lender.map(r => r.event_rate));
      const mob = d.by_months_on_book;
      CHART.volumeVsRate("chart-pf-mob",
        mob.map(r => r.bucket), mob.map(r => r.observations), mob.map(r => r.event_rate),
        { xTitle: "Months on book" });
    },

    correlation: function (d) {
      CHART.heatmap("chart-corr", d.columns, d.matrix);
    },
  };

  function loadTab(name, force) {
    if (loaded[name] && !force) return;
    fetchSection(name).then(function (d) {
      renderers[name](d);
      loaded[name] = true;
    });
  }

  function activate(name) {
    activeTab = name;
    tabs.forEach(function (t) { t.classList.toggle("active", t.dataset.tab === name); });
    panels.forEach(function (p) { p.classList.toggle("active", p.id === `panel-${name}`); });
    loadTab(name);
  }

  tabs.forEach(function (t) {
    t.addEventListener("click", function () { activate(t.dataset.tab); });
  });

  // Variable explorer (6.7) — pick any variable, see its relationship to the target.
  const varSelect = document.getElementById("var-select");
  function loadVariable() {
    const v = varSelect.value;
    setLoading("correlation", true);
    fetch(`${window.EDA_VAR_URL}/${v}?${filterQuery()}`)
      .then(r => r.json())
      .then(function (d) {
        setLoading("correlation", false);
        const rows = d.data;
        const labels = rows.map(r => r.bucket !== undefined ? r.bucket : r[Object.keys(r)[0]]);
        CHART.volumeVsRate("chart-var-target", labels,
          rows.map(r => r.observations), rows.map(r => r.event_rate),
          { xTitle: v, tickangle: -30, bottomMargin: 130 });
      });
  }
  varSelect.addEventListener("change", loadVariable);

  filtersForm.addEventListener("submit", function (e) {
    e.preventDefault();
    Object.keys(loaded).forEach(function (k) { loaded[k] = false; });
    loadTab(activeTab, true);
    if (activeTab === "correlation") loadVariable();
  });
  filtersForm.addEventListener("reset", function () {
    setTimeout(function () {
      Object.keys(loaded).forEach(function (k) { loaded[k] = false; });
      loadTab(activeTab, true);
      if (activeTab === "correlation") loadVariable();
    }, 0);
  });

  activate("target");
  loadVariable();
})();
