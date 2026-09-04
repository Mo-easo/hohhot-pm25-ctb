/**
 * ECharts 趋势图
 */
(function () {
  function baseOption(title, labels, values) {
    return {
      title: {
        text: title,
        left: 0,
        top: 0,
        textStyle: { color: "#9bb5ad", fontSize: 12, fontWeight: 500 },
      },
      tooltip: { trigger: "axis" },
      grid: { left: 40, right: 16, top: 36, bottom: 28 },
      xAxis: {
        type: "category",
        data: labels,
        axisLabel: { color: "#9bb5ad", hideOverlap: true },
        axisLine: { lineStyle: { color: "rgba(180,210,200,0.2)" } },
      },
      yAxis: {
        type: "value",
        name: "PM2.5",
        nameTextStyle: { color: "#9bb5ad" },
        axisLabel: { color: "#9bb5ad" },
        splitLine: { lineStyle: { color: "rgba(180,210,200,0.08)" } },
      },
      series: [
        {
          name: "PM2.5",
          type: "line",
          smooth: true,
          showSymbol: false,
          data: values,
          lineStyle: { width: 2, color: "#5ec4a8" },
          areaStyle: {
            color: {
              type: "linear",
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: "rgba(94,196,168,0.35)" },
                { offset: 1, color: "rgba(94,196,168,0.02)" },
              ],
            },
          },
        },
      ],
    };
  }

  async function renderTrend(domId, hours) {
    const el = document.getElementById(domId);
    if (!el || !window.echarts) return;
    const json = await window.Qingcheng.getJSON(`/api/trend?hours=${hours}`);
    const series = json.data.series || [];
    const labels = series.map((r) => {
      const parts = (r.datetime || "").split(" ");
      return hours > 24 ? (parts[0] || "").slice(5) : (parts[1] || "").slice(0, 5);
    });
    const values = series.map((r) => r.PM25);
    const chart = echarts.init(el);
    chart.setOption(baseOption(hours === 24 ? "近24小时" : "近7日小时均值序列", labels, values));
    window.addEventListener("resize", () => chart.resize());
  }

  window.QingchengCharts = { renderTrend };
})();
