"""
青城清气 — Flask 应用入口（Phase 1）

职责：路由、API、页面渲染。业务逻辑保持在 database / analysis 模块。
"""
from __future__ import annotations

import logging
import time
from functools import wraps
from pathlib import Path

from flask import Flask, jsonify, render_template, request

import config
from config import DATA_MODE_LABELS, HOHHOT_CENTER, pm25_grade
from database import (
    count_rows,
    get_data_range,
    get_latest_city_snapshot,
    get_meta,
    get_station_latest,
    get_stations,
    get_trend,
    init_database,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(config.LOGS_DIR / "app.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("qingcheng")

app = Flask(__name__)
app.config["SECRET_KEY"] = config.SECRET_KEY
app.config["JSON_AS_ASCII"] = False

# Simple in-memory cache: key -> (expires_at, payload)
_cache: dict[str, tuple[float, object]] = {}


def cached(ttl: int | None = None):
    """Decorator for short-lived API response caching."""

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            key = f"{fn.__name__}:{request.full_path}"
            now = time.time()
            hit = _cache.get(key)
            if hit and hit[0] > now:
                return hit[1]
            result = fn(*args, **kwargs)
            _cache[key] = (now + (ttl or config.CACHE_TTL_SECONDS), result)
            return result

        return wrapper

    return decorator


def api_error(message: str, status: int = 400, code: str = "bad_request"):
    return jsonify({"ok": False, "error": {"code": code, "message": message}}), status


def api_ok(data, **extra):
    payload = {"ok": True, "data": data}
    payload.update(extra)
    return jsonify(payload)


def _data_banner() -> dict:
    mode = get_meta("data_mode") or config.DATA_MODE
    return {
        "data_mode": mode,
        "data_mode_label": DATA_MODE_LABELS.get(mode, mode),
        "disclaimer": get_meta("data_disclaimer")
        or "当前为演示数据，非实时监测。",
        "generated_at": get_meta("data_generated_at"),
        "is_realtime": False,
    }


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template(
        "index.html",
        banner=_data_banner(),
        center=HOHHOT_CENTER,
        phase="Phase 1",
    )


@app.route("/monitor")
def monitor():
    return render_template("monitor.html", banner=_data_banner(), phase="Phase 1")


@app.route("/map")
def map_page():
    return render_template("map.html", banner=_data_banner(), center=HOHHOT_CENTER, phase="Phase 1")


@app.route("/analysis")
def analysis_page():
    return render_template("analysis.html", banner=_data_banner(), phase="Phase 1")


@app.route("/prediction")
def prediction_page():
    return render_template("prediction.html", banner=_data_banner(), phase="Phase 1")


@app.route("/research")
def research_page():
    return render_template("research.html", banner=_data_banner(), phase="Phase 1")


@app.route("/about")
def about_page():
    return render_template("about.html", banner=_data_banner(), phase="Phase 1")


@app.route("/data-source")
def data_source_page():
    return render_template(
        "data_source.html",
        banner=_data_banner(),
        data_range=get_data_range(),
        phase="Phase 1",
    )


# ---------------------------------------------------------------------------
# APIs
# ---------------------------------------------------------------------------
@app.route("/api/health")
def api_health():
    try:
        stations = count_rows("stations")
        records = count_rows("air_quality")
        return api_ok(
            {
                "status": "healthy",
                "phase": "1",
                "stations": stations,
                "air_quality_rows": records,
                "database": str(config.DATABASE_PATH.name),
            }
        )
    except Exception as exc:
        logger.exception("Health check failed")
        return api_error(str(exc), status=500, code="health_failed")


@app.route("/api/meta")
@cached()
def api_meta():
    try:
        return api_ok(
            {
                **_data_banner(),
                "data_range": get_data_range(),
                "schema_version": get_meta("schema_version"),
                "city": "呼和浩特",
                "project": "青城清气",
            }
        )
    except Exception as exc:
        logger.exception("meta failed")
        return api_error(str(exc), status=500, code="meta_failed")


@app.route("/api/stations")
@cached()
def api_stations():
    try:
        return api_ok(get_stations(), banner=_data_banner())
    except Exception as exc:
        logger.exception("stations failed")
        return api_error(str(exc), status=500, code="stations_failed")


@app.route("/api/latest")
@cached()
def api_latest():
    """City snapshot + per-station latest. Marked as DEMO/SIMULATED, not realtime."""
    try:
        snap = get_latest_city_snapshot()
        if not snap:
            return api_error("暂无空气质量数据，请先运行演示数据生成脚本。", status=404, code="no_data")
        grade = pm25_grade(snap.get("PM25"))
        stations = get_station_latest()
        for s in stations:
            g = pm25_grade(s.get("PM25"))
            s["level"] = g["level"]
            s["color"] = g["color"]
            s["risk"] = g["risk"]
        return api_ok(
            {
                "city": {
                    **{k: (round(v, 1) if isinstance(v, float) else v) for k, v in snap.items()},
                    "level": grade["level"],
                    "color": grade["color"],
                    "risk": grade["risk"],
                },
                "stations": stations,
            },
            banner=_data_banner(),
        )
    except Exception as exc:
        logger.exception("latest failed")
        return api_error(str(exc), status=500, code="latest_failed")


@app.route("/api/trend")
@cached()
def api_trend():
    try:
        hours = request.args.get("hours", default=24, type=int)
        if hours not in (24, 48, 72, 168):
            return api_error("hours 仅支持 24 / 48 / 72 / 168", status=400, code="invalid_param")
        rows = get_trend(hours=hours)
        for r in rows:
            for k, v in list(r.items()):
                if isinstance(v, float):
                    r[k] = round(v, 1)
        return api_ok({"hours": hours, "series": rows}, banner=_data_banner())
    except Exception as exc:
        logger.exception("trend failed")
        return api_error(str(exc), status=500, code="trend_failed")


@app.route("/api/risk/forecast-placeholder")
@cached()
def api_risk_placeholder():
    """
    Phase 1 placeholder: risk bands derived from recent mean + diurnal pattern.
    NOT a trained ML forecast. Clearly labeled.
    """
    try:
        trend = get_trend(hours=24)
        if not trend:
            return api_error("暂无数据", status=404, code="no_data")
        last_pm = trend[-1].get("PM25") or 40
        # Naive echo of recent diurnal shape — demo only
        hours = []
        for i in range(1, 25):
            # slight continuation of last 24h pattern
            base = trend[min(i - 1, len(trend) - 1)].get("PM25") or last_pm
            pred = round(0.7 * last_pm + 0.3 * base, 1)
            g = pm25_grade(pred)
            hours.append(
                {
                    "hour_ahead": i,
                    "pm25_estimate": pred,
                    "level": g["level"],
                    "risk": g["risk"],
                    "color": g["color"],
                }
            )
        bands = {
            "h6": hours[5]["risk"],
            "h12": hours[11]["risk"],
            "h18": hours[17]["risk"],
            "h24": hours[23]["risk"],
        }
        return api_ok(
            {
                "method": "placeholder_diurnal_blend",
                "note": "Phase 1 占位风险估计，非机器学习预测。正式模型将在 Phase 5 训练。",
                "bands": bands,
                "hourly": hours,
            },
            banner=_data_banner(),
        )
    except Exception as exc:
        logger.exception("risk placeholder failed")
        return api_error(str(exc), status=500, code="risk_failed")


@app.errorhandler(404)
def not_found(e):
    if request.path.startswith("/api/"):
        return api_error("接口不存在", status=404, code="not_found")
    return render_template("about.html", banner=_data_banner(), phase="Phase 1"), 404


@app.errorhandler(500)
def server_error(e):
    if request.path.startswith("/api/"):
        return api_error("服务器内部错误", status=500, code="server_error")
    return "Internal Server Error", 500


def bootstrap():
    """Ensure DB exists; do not auto-generate fake 'realtime' claims."""
    init_database()
    n = count_rows("air_quality")
    if n == 0:
        logger.warning(
            "air_quality 表为空。请运行: python scripts/generate_demo_data.py"
        )
    else:
        logger.info("Loaded DB with %s air_quality rows", n)


bootstrap()


if __name__ == "__main__":
    logger.info("Starting 青城清气 Phase 1 on 0.0.0.0:5000 (LAN accessible)")
    # use_reloader=False: Windows debug reloader can hit WinError 10038
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
