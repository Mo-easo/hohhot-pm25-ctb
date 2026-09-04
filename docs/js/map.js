(function () {
  function markerHtml(pm25, color) {
    return `<div class="station-marker" style="background:${color || "#9E9E9E"}">${Math.round(pm25 ?? 0)}</div>`;
  }

  function createMap(domId, center) {
    const map = L.map(domId, { zoomControl: true, attributionControl: true });
    map.setView([center.lat, center.lng], center.zoom || 11);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 18,
      attribution: "&copy; OpenStreetMap",
    }).addTo(map);
    return map;
  }

  async function addStations(map, onClick) {
    const json = await window.Qingcheng.getJSON("latest");
    const stations = json.data.stations || [];
    stations.forEach((s) => {
      const icon = L.divIcon({
        className: "",
        html: markerHtml(s.PM25, s.color),
        iconSize: [28, 28],
        iconAnchor: [14, 14],
      });
      const m = L.marker([s.latitude, s.longitude], { icon }).addTo(map);
      m.bindTooltip(`${s.station_name}<br>PM2.5 ${s.PM25} · ${s.level}`);
      if (onClick) m.on("click", () => onClick(s));
    });
    return stations;
  }

  async function initHomeMap(domId) {
    const el = document.getElementById(domId);
    if (!el || !window.L) return;
    const center = window.QINGCHENG_STATIC.center;
    const map = createMap(domId, center);
    await addStations(map);
    setTimeout(() => map.invalidateSize(), 150);
  }

  async function initFullMap(domId, detailId) {
    const el = document.getElementById(domId);
    if (!el || !window.L) return;
    const center = window.QINGCHENG_STATIC.center;
    const map = createMap(domId, center);
    const detail = document.getElementById(detailId);
    await addStations(map, (s) => {
      if (!detail) return;
      detail.hidden = false;
      document.getElementById("detail-name").textContent = s.station_name;
      document.getElementById("detail-body").innerHTML = `
        <dt>城区</dt><dd>${s.district}</dd>
        <dt>PM2.5</dt><dd>${s.PM25} µg/m³（${s.level}）</dd>
        <dt>PM10</dt><dd>${s.PM10 ?? "—"}</dd>
        <dt>AQI</dt><dd>${s.AQI ?? "—"}</dd>
        <dt>风险</dt><dd>${s.risk}</dd>
        <dt>时间</dt><dd>${s.datetime}</dd>
        <dt>数据模式</dt><dd>${s.data_mode}</dd>
      `;
    });
    setTimeout(() => map.invalidateSize(), 150);
  }

  window.QingchengMap = { initHomeMap, initFullMap };
})();
