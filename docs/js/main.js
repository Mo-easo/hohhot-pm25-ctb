/**
 * 静态站公共逻辑（读取 docs/api/*.json）
 */
(function () {
  async function getJSON(name) {
    const url = window.QINGCHENG_STATIC.api(name);
    const res = await fetch(url);
    if (!res.ok) throw new Error(`加载失败 ${url} (${res.status})`);
    const json = await res.json();
    if (json.ok === false) throw new Error(json.error?.message || "数据错误");
    return json;
  }

  function riskClass(risk) {
    if (!risk) return "";
    if (risk.includes("高")) return "color:#d4654a";
    if (risk.includes("中")) return "color:#e0a045";
    return "color:#5cb88a";
  }

  async function loadHomeMetrics() {
    const json = await getJSON("latest");
    const city = json.data.city;
    const strip = document.getElementById("metric-strip");
    if (!strip) return city;
    strip.querySelectorAll("[data-field]").forEach((el) => {
      const key = el.getAttribute("data-field");
      let val = city[key];
      if (key === "AQI" && typeof val === "number") val = Math.round(val);
      el.textContent = val ?? "--";
      if (key === "level" && city.color) el.style.color = city.color;
    });
    const t = document.getElementById("snapshot-time");
    if (t) {
      t.textContent = `数据时间 ${city.datetime || "—"} · ${city.data_mode || "DEMO"}`;
    }
    const banner = document.getElementById("live-banner");
    if (banner && json.banner) {
      banner.innerHTML = `<span class="data-banner__tag">${json.banner.data_mode}</span>
        <span>${json.banner.data_mode_label}</span>
        <span class="data-banner__sep">·</span>
        <span>${json.banner.disclaimer}</span>`;
    }
    return city;
  }

  async function loadRiskBands() {
    const json = await getJSON("risk");
    const bands = json.data.bands || {};
    document.querySelectorAll("[data-band]").forEach((el) => {
      const key = el.getAttribute("data-band");
      const v = bands[key] || "--";
      el.textContent = v;
      el.setAttribute("style", riskClass(v));
    });
    return json.data;
  }

  async function loadHealth() {
    const list = document.getElementById("status-list");
    if (!list) return;
    try {
      const json = await getJSON("health");
      const d = json.data;
      list.innerHTML = `
        <li>状态：${d.status}</li>
        <li>托管：${d.hosting || "GitHub Pages"}</li>
        <li>阶段：Phase ${d.phase}</li>
        <li>站点数：${d.stations}</li>
      `;
    } catch (err) {
      list.innerHTML = `<li>加载失败：${err.message}</li>`;
    }
  }

  window.Qingcheng = { getJSON, riskClass };

  window.QingchengHome = {
    async init() {
      try {
        await loadHomeMetrics();
        await loadRiskBands();
        await loadHealth();
        if (window.QingchengMap) await window.QingchengMap.initHomeMap("home-map");
        if (window.QingchengCharts) {
          await window.QingchengCharts.renderTrend("chart-24h", 24);
          await window.QingchengCharts.renderTrend("chart-7d", 168);
        }
      } catch (err) {
        console.error(err);
        const t = document.getElementById("snapshot-time");
        if (t) t.textContent = "数据加载失败：" + err.message;
      }
    },
  };
})();
