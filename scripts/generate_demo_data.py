"""
Phase 1 演示数据生成器。

明确标记为 DEMO DATA，不得在前端表述为“实时数据”。
生成呼和浩特多站点、多日小时级空气质量 + 气象模拟序列，用于联调。
"""
from __future__ import annotations

import argparse
import csv
import logging
import math
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import DATA_DIR, HOHHOT_STATIONS, PROCESSED_DIR, RAW_DIR
from database import init_database, set_meta, db_session, count_rows

logger = logging.getLogger(__name__)

DATA_MODE = "DEMO"


def _seasonal_base(month: int) -> float:
    """呼和浩特冬季污染偏高的简化季节基线。"""
    # Winter heating season higher PM2.5
    winter = {11: 78, 12: 95, 1: 100, 2: 88, 3: 65}
    summer = {6: 28, 7: 25, 8: 30}
    if month in winter:
        return winter[month]
    if month in summer:
        return summer[month]
    spring_fall = {4: 48, 5: 40, 9: 38, 10: 55}
    return spring_fall.get(month, 45)


def _hour_factor(hour: int) -> float:
    """早高峰 / 晚高峰略抬升。"""
    if 7 <= hour <= 9:
        return 1.18
    if 17 <= hour <= 20:
        return 1.22
    if 2 <= hour <= 5:
        return 0.85
    return 1.0


def _aqi_from_pm25(pm25: float) -> int:
    """粗略 IAQI 映射（演示用）。"""
    breakpoints = [
        (0, 35, 0, 50),
        (35, 75, 50, 100),
        (75, 115, 100, 150),
        (115, 150, 150, 200),
        (150, 250, 200, 300),
        (250, 350, 300, 400),
        (350, 500, 400, 500),
    ]
    for bp_lo, bp_hi, iaqi_lo, iaqi_hi in breakpoints:
        if pm25 <= bp_hi:
            return int(
                round(
                    (iaqi_hi - iaqi_lo) / (bp_hi - bp_lo) * (pm25 - bp_lo) + iaqi_lo
                )
            )
    return 500


def generate_records(
    days: int = 30,
    end_time: datetime | None = None,
    seed: int = 42,
) -> list[dict]:
    random.seed(seed)
    end = end_time or datetime.now().replace(minute=0, second=0, microsecond=0)
    start = end - timedelta(days=days - 1)
    start = start.replace(hour=0)

    records: list[dict] = []
    t = start
    while t <= end:
        month = t.month
        hour = t.hour
        base = _seasonal_base(month) * _hour_factor(hour)
        # Synoptic-ish wave
        synoptic = 8 * math.sin(2 * math.pi * (t.timetuple().tm_yday / 7.0))
        for i, st in enumerate(HOHHOT_STATIONS):
            station_bias = [-6, 4, 2, 8, -2, -10][i]
            noise = random.gauss(0, 6)
            pm25 = max(5.0, base + synoptic + station_bias + noise)
            wind = max(0.3, 2.8 + random.gauss(0, 1.2) - (0.015 * (pm25 - 40)))
            humidity = min(95, max(15, 45 + random.gauss(0, 12) + (0.08 * pm25)))
            temp = (
                -8
                if month in (12, 1, 2)
                else 22
                if month in (6, 7, 8)
                else 8
            ) + random.gauss(0, 3)
            pm10 = pm25 * (1.35 + random.uniform(-0.1, 0.15))
            no2 = max(5, 28 + 0.15 * pm25 + random.gauss(0, 5))
            so2 = max(2, 12 + 0.05 * pm25 + random.gauss(0, 3))
            o3 = max(5, 55 - 0.12 * pm25 + random.gauss(0, 8) + (8 if 11 <= hour <= 16 else 0))
            co = max(0.2, 0.6 + 0.008 * pm25 + random.gauss(0, 0.1))
            precip = 0.0 if random.random() > 0.08 else round(random.uniform(0.1, 4.0), 1)
            if precip > 0:
                pm25 *= 0.85
            pressure = 1012 + random.gauss(0, 4)
            wind_dir = (random.uniform(0, 360) + i * 20) % 360

            records.append(
                {
                    "datetime": t.strftime("%Y-%m-%d %H:%M:%S"),
                    "station_id": st["station_id"],
                    "station_name": st["station_name"],
                    "latitude": st["latitude"],
                    "longitude": st["longitude"],
                    "district": st["district"],
                    "PM25": round(pm25, 1),
                    "PM10": round(pm10, 1),
                    "SO2": round(so2, 1),
                    "NO2": round(no2, 1),
                    "O3": round(o3, 1),
                    "CO": round(co, 2),
                    "AQI": _aqi_from_pm25(pm25),
                    "temperature": round(temp, 1),
                    "humidity": round(humidity, 1),
                    "wind_speed": round(wind, 1),
                    "wind_direction": round(wind_dir, 1),
                    "precipitation": precip,
                    "pressure": round(pressure, 1),
                    "data_mode": DATA_MODE,
                }
            )
        t += timedelta(hours=1)
    return records


def export_csv(records: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not records:
        return
    fieldnames = list(records[0].keys())
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    logger.info("Wrote %s rows to %s", len(records), path)


def load_into_db(records: list[dict], db_path=None) -> int:
    init_database(db_path)
    with db_session(db_path) as conn:
        conn.execute("DELETE FROM air_quality")
        conn.executemany(
            """
            INSERT INTO air_quality (
                datetime, station_id, PM25, PM10, SO2, NO2, O3, CO, AQI,
                temperature, humidity, wind_speed, wind_direction,
                precipitation, pressure, data_mode
            ) VALUES (
                :datetime, :station_id, :PM25, :PM10, :SO2, :NO2, :O3, :CO, :AQI,
                :temperature, :humidity, :wind_speed, :wind_direction,
                :precipitation, :pressure, :data_mode
            )
            """,
            records,
        )
    set_meta("data_mode", DATA_MODE, db_path)
    set_meta("data_generated_at", datetime.now().isoformat(timespec="seconds"), db_path)
    set_meta(
        "data_disclaimer",
        "DEMO DATA — 演示数据，非实时监测值，仅用于 Phase 1 系统联调。",
        db_path,
    )
    return count_rows("air_quality", db_path)


def main(days: int = 30, seed: int = 42) -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    records = generate_records(days=days, seed=seed)
    raw_path = RAW_DIR / "demo_air_quality.csv"
    processed_path = PROCESSED_DIR / "demo_air_quality.csv"
    export_csv(records, raw_path)
    export_csv(records, processed_path)
    n = load_into_db(records)
    print(f"[OK] Generated {n} DEMO rows | stations={len(HOHHOT_STATIONS)} | days={days}")
    print(f"[OK] CSV: {raw_path}")
    print(f"[OK] DB loaded. data_mode={DATA_MODE}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Phase 1 DEMO air quality data")
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    main(days=args.days, seed=args.seed)
