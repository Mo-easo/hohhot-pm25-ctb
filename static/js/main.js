/**
 * 青城清气 — 公共工具与首页初始化
 */
(function () {
  async function getJSON(url) {
    const res = await fetch(url);
    const json = await res.json();
    if (!res.ok || json.ok === false) {
      const msg = json.error?.message || `请求失败: ${res.status}`;
      throw new Error(msg);
    }
    return json;
  }

  function setText(sel, value) {
    const el = document.querySelector(sel);
    if (el) el.textContent = value ?? "--";
  }

  function riskClass(risk) {
    if (!risk) return "";
    if (risk.includes("高")) return "color:#d4654a";
    if (risk.includes("中")) return "color:#e0a045";
    return "color:#5cb88a";
  }

  async function loadHomeMetrics() {
    const json = await getJSON("/api/latest");
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
    return city;
  }

  async function loadRiskBands() {
    const json = await getJSON("/api/risk/forecast-placeholder");
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
      const json = await getJSON("/api/health");
      const d = json.data;
      list.innerHTML = `
        <li>状态：${d.status}</li>
        <li>阶段：Phase ${d.phase}</li>
        <li>站点数：${d.stations}</li>
        <li>空气质量记录：${d.air_quality_rows}</li>
        <li>数据库：${d.database}</li>
      `;
    } catch (err) {
      list.innerHTML = `<li>健康检查失败：${err.message}</li>`;
    }
  }

  window.Qingcheng = { getJSON, setText, riskClass };

  window.QingchengHome = {
    async init() {
      try {
        await loadHomeMetrics();
        await loadRiskBands();
        await loadHealth();
        if (window.QingchengMap) {
          await window.QingchengMap.initHomeMap("home-map");
        }
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
