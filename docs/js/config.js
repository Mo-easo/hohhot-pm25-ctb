/**
 * GitHub Pages 静态站配置：自动识别仓库子路径。
 */
(function () {
  const parts = location.pathname.split("/").filter(Boolean);
  // https://mo-easo.github.io/hohhot-pm25-ctb/...
  const repoBase =
    parts.length && parts[0] === "hohhot-pm25-ctb" ? "/hohhot-pm25-ctb" : "";
  window.QINGCHENG_STATIC = {
    base: repoBase,
    api: (name) => `${repoBase}/api/${name}.json`,
    page: (name) => `${repoBase}/${name}`,
    center: { lat: 40.8421, lng: 111.749, zoom: 11 },
  };
})();
