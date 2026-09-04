"""
数据库模块：SQLite 初始化、连接、索引与基础查询。
"""
from __future__ import annotations

import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import DATABASE_PATH, HOHHOT_STATIONS

logger = logging.getLogger(__name__)

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS stations (
    station_id   TEXT PRIMARY KEY,
    station_name TEXT NOT NULL,
    latitude     REAL NOT NULL,
    longitude    REAL NOT NULL,
    district     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS air_quality (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    datetime      TEXT NOT NULL,
    station_id    TEXT NOT NULL,
    PM25          REAL,
    PM10          REAL,
    SO2           REAL,
    NO2           REAL,
    O3            REAL,
    CO            REAL,
    AQI           INTEGER,
    temperature   REAL,
    humidity      REAL,
    wind_speed    REAL,
    wind_direction REAL,
    precipitation REAL,
    pressure      REAL,
    data_mode     TEXT NOT NULL DEFAULT 'DEMO',
    FOREIGN KEY (station_id) REFERENCES stations(station_id)
);

CREATE INDEX IF NOT EXISTS idx_aq_datetime ON air_quality(datetime);
CREATE INDEX IF NOT EXISTS idx_aq_station ON air_quality(station_id);
CREATE INDEX IF NOT EXISTS idx_aq_station_datetime ON air_quality(station_id, datetime);
CREATE INDEX IF NOT EXISTS idx_aq_data_mode ON air_quality(data_mode);

CREATE TABLE IF NOT EXISTS system_meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    path = str(db_path or DATABASE_PATH)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def db_session(db_path: Optional[Path] = None):
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database(db_path: Optional[Path] = None) -> None:
    """Create tables, indexes, and seed station metadata."""
    path = Path(db_path or DATABASE_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    with db_session(path) as conn:
        conn.executescript(SCHEMA_SQL)
        for s in HOHHOT_STATIONS:
            conn.execute(
                """
                INSERT OR REPLACE INTO stations
                (station_id, station_name, latitude, longitude, district)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    s["station_id"],
                    s["station_name"],
                    s["latitude"],
                    s["longitude"],
                    s["district"],
                ),
            )
        conn.execute(
            "INSERT OR REPLACE INTO system_meta (key, value) VALUES (?, ?)",
            ("schema_version", "1.0.0-phase1"),
        )
    logger.info("Database initialized at %s", path)


def count_rows(table: str, db_path: Optional[Path] = None) -> int:
    allowed = {"stations", "air_quality", "system_meta"}
    if table not in allowed:
        raise ValueError(f"Table not allowed: {table}")
    with db_session(db_path) as conn:
        row = conn.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()
        return int(row["c"])


def get_stations(db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    with db_session(db_path) as conn:
        rows = conn.execute(
            "SELECT station_id, station_name, latitude, longitude, district FROM stations ORDER BY station_id"
        ).fetchall()
        return [dict(r) for r in rows]


def get_latest_city_snapshot(db_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """City-wide average of the most recent timestamp."""
    with db_session(db_path) as conn:
        latest = conn.execute("SELECT MAX(datetime) AS dt FROM air_quality").fetchone()
        if not latest or not latest["dt"]:
            return None
        dt = latest["dt"]
        row = conn.execute(
            """
            SELECT
                datetime,
                AVG(PM25) AS PM25,
                AVG(PM10) AS PM10,
                AVG(SO2) AS SO2,
                AVG(NO2) AS NO2,
                AVG(O3) AS O3,
                AVG(CO) AS CO,
                AVG(AQI) AS AQI,
                AVG(temperature) AS temperature,
                AVG(humidity) AS humidity,
                AVG(wind_speed) AS wind_speed,
                data_mode
            FROM air_quality
            WHERE datetime = ?
            GROUP BY datetime, data_mode
            """,
            (dt,),
        ).fetchone()
        return dict(row) if row else None


def get_station_latest(db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Latest reading per station."""
    with db_session(db_path) as conn:
        rows = conn.execute(
            """
            SELECT a.*, s.station_name, s.latitude, s.longitude, s.district
            FROM air_quality a
            JOIN stations s ON s.station_id = a.station_id
            WHERE a.datetime = (SELECT MAX(datetime) FROM air_quality)
            ORDER BY a.station_id
            """
        ).fetchall()
        return [dict(r) for r in rows]


def get_trend(hours: int = 24, db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    with db_session(db_path) as conn:
        rows = conn.execute(
            """
            SELECT datetime,
                   AVG(PM25) AS PM25,
                   AVG(PM10) AS PM10,
                   AVG(AQI) AS AQI,
                   AVG(NO2) AS NO2,
                   AVG(O3) AS O3
            FROM air_quality
            WHERE datetime >= datetime((SELECT MAX(datetime) FROM air_quality), ?)
            GROUP BY datetime
            ORDER BY datetime
            """,
            (f"-{hours} hours",),
        ).fetchall()
        return [dict(r) for r in rows]


def get_data_range(db_path: Optional[Path] = None) -> Dict[str, Any]:
    with db_session(db_path) as conn:
        row = conn.execute(
            """
            SELECT MIN(datetime) AS start_time,
                   MAX(datetime) AS end_time,
                   COUNT(*) AS total_rows,
                   COUNT(DISTINCT station_id) AS station_count,
                   MAX(data_mode) AS data_mode
            FROM air_quality
            """
        ).fetchone()
        return dict(row) if row else {}


def get_meta(key: str, db_path: Optional[Path] = None) -> Optional[str]:
    with db_session(db_path) as conn:
        row = conn.execute(
            "SELECT value FROM system_meta WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else None


def set_meta(key: str, value: str, db_path: Optional[Path] = None) -> None:
    with db_session(db_path) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO system_meta (key, value) VALUES (?, ?)",
            (key, value),
        )
