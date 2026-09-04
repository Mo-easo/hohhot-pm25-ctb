(function () {
  async function renderPlaceholder(domId) {
    const el = document.getElementById(domId);
    if (!el || !window.echarts) return;
    const json = await window.Qingcheng.getJSON("risk");
    const hourly = json.data.hourly || [];
    const chart = echarts.init(el);
    chart.setOption({
      title: {
        text: "占位估计（非 ML）",
        left: 0,
        textStyle: { color: "#9bb5ad", fontSize: 12 },
      },
      tooltip: { trigger: "axis" },
      grid: { left: 40, right: 16, top: 48, bottom: 28 },
      xAxis: {
        type: "category",
        data: hourly.map((h) => `+${h.hour_ahead}h`),
        axisLabel: { color: "#9bb5ad" },
      },
      yAxis: {
        type: "value",
        name: "PM2.5",
        axisLabel: { color: "#9bb5ad" },
        splitLine: { lineStyle: { color: "rgba(180,210,200,0.08)" } },
      },
      series: [
        {
          type: "line",
          smooth: true,
          data: hourly.map((h) => h.pm25_estimate),
          lineStyle: { color: "#e0a045" },
          areaStyle: { color: "rgba(224,160,69,0.15)" },
        },
      ],
    });
    window.addEventListener("resize", () => chart.resize());
  }

  window.QingchengPrediction = { renderPlaceholder };
})();
