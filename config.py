"""
青城清气 — 全局配置
Phase 1: 基础配置与环境变量读取（禁止硬编码密钥）
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Flask
# ---------------------------------------------------------------------------
SECRET_KEY = os.environ.get("HOHHOT_SECRET_KEY", "dev-only-change-me-in-production")
DEBUG = os.environ.get("HOHHOT_DEBUG", "1") == "1"
HOST = os.environ.get("HOHHOT_HOST", "127.0.0.1")
PORT = int(os.environ.get("HOHHOT_PORT", "5000"))

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
CLEANED_DIR = DATA_DIR / "cleaned"
PROCESSED_DIR = DATA_DIR / "processed"
MODELS_DIR = BASE_DIR / "models"
LOGS_DIR = BASE_DIR / "logs"

DATABASE_PATH = BASE_DIR / "hohhot_pm25.db"

# ---------------------------------------------------------------------------
# Data provenance labels (MUST be shown in UI — never fake "realtime")
# ---------------------------------------------------------------------------
DATA_MODE = os.environ.get("HOHHOT_DATA_MODE", "DEMO")  # REAL | SIMULATED | DEMO
DATA_MODE_LABELS = {
    "REAL": "REAL DATA — 真实数据",
    "SIMULATED": "SIMULATED DATA — 模拟数据（非实时）",
    "DEMO": "DEMO DATA — 演示数据（非实时，仅用于系统联调）",
}

# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------
CACHE_TTL_SECONDS = int(os.environ.get("HOHHOT_CACHE_TTL", "60"))

# ---------------------------------------------------------------------------
# Hohhot monitoring stations (approximate public locations for demo)
# ---------------------------------------------------------------------------
HOHHOT_STATIONS = [
    {
        "station_id": "HHHT001",
        "station_name": "呼和浩特市环境监测中心站",
        "latitude": 40.8421,
        "longitude": 111.7490,
        "district": "新城区",
    },
    {
        "station_id": "HHHT002",
        "station_name": "如意开发区",
        "latitude": 40.8250,
        "longitude": 111.8000,
        "district": "赛罕区",
    },
    {
        "station_id": "HHHT003",
        "station_name": "呼市一监",
        "latitude": 40.8100,
        "longitude": 111.6700,
        "district": "回民区",
    },
    {
        "station_id": "HHHT004",
        "station_name": "小召前街",
        "latitude": 40.8050,
        "longitude": 111.6650,
        "district": "回民区",
    },
    {
        "station_id": "HHHT005",
        "station_name": "二十九中",
        "latitude": 40.7800,
        "longitude": 111.7000,
        "district": "玉泉区",
    },
    {
        "station_id": "HHHT006",
        "station_name": "工大金川校区",
        "latitude": 40.7600,
        "longitude": 111.6200,
        "district": "土默特左旗",
    },
]

# City center for map default view
HOHHOT_CENTER = {"lat": 40.8421, "lng": 111.7490, "zoom": 11}

# PM2.5 grade thresholds (China AQI / air quality levels, µg/m³)
PM25_GRADES = [
    {"max": 35, "level": "优", "color": "#4CAF50", "risk": "低风险"},
    {"max": 75, "level": "良", "color": "#8BC34A", "risk": "低风险"},
    {"max": 115, "level": "轻度污染", "color": "#FFC107", "risk": "中风险"},
    {"max": 150, "level": "中度污染", "color": "#FF9800", "risk": "中风险"},
    {"max": 250, "level": "重度污染", "color": "#F44336", "risk": "高风险"},
    {"max": 9999, "level": "严重污染", "color": "#9C27B0", "risk": "高风险"},
]


def pm25_grade(value):
    """Return grade dict for a PM2.5 concentration."""
    if value is None:
        return {"level": "未知", "color": "#9E9E9E", "risk": "未知"}
    for g in PM25_GRADES:
        if value <= g["max"]:
            return g
    return PM25_GRADES[-1]
