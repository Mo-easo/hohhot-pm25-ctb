"""Export Phase 1 DEMO APIs into docs/api/*.json for GitHub Pages."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config import DATA_MODE_LABELS, HOHHOT_CENTER, pm25_grade
from database import (
    get_data_range,
    get_latest_city_snapshot,
    get_meta,
    get_station_latest,
    get_stations,
    get_trend,
)

OUT = ROOT / "docs" / "api"


def banner():
    mode = get_meta("data_mode") or "DEMO"
    return {
        "data_mode": mode,
        "data_mode_label": DATA_MODE_LABELS.get(mode, mode),
        "disclaimer": get_meta("data_disclaimer")
        or "DEMO DATA — 演示数据，非实时监测。",
        "generated_at": get_meta("data_generated_at"),
        "is_realtime": False,
    }


def write(name: str, payload: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)}")


def main() -> None:
    b = banner()
    snap = get_latest_city_snapshot()
    if not snap:
        raise SystemExit("No air_quality data. Run scripts/generate_demo_data.py first.")

    grade = pm25_grade(snap.get("PM25"))
    city = {
        **{k: (round(v, 1) if isinstance(v, float) else v) for k, v in snap.items()},
        "level": grade["level"],
        "color": grade["color"],
        "risk": grade["risk"],
    }
    stations = get_station_latest()
    for s in stations:
        g = pm25_grade(s.get("PM25"))
        s["level"] = g["level"]
        s["color"] = g["color"]
        s["risk"] = g["risk"]

    write(
        "health.json",
        {
            "ok": True,
            "data": {
                "status": "healthy",
                "phase": "1",
                "stations": len(get_stations()),
                "air_quality_rows": "see data_range",
                "hosting": "GitHub Pages (static DEMO)",
            },
        },
    )
    write(
        "meta.json",
        {
            "ok": True,
            "data": {
                **b,
                "data_range": get_data_range(),
                "schema_version": get_meta("schema_version"),
                "city": "呼和浩特",
                "project": "青城清气",
                "center": HOHHOT_CENTER,
            },
        },
    )
    write("stations.json", {"ok": True, "data": get_stations(), "banner": b})
    write("latest.json", {"ok": True, "data": {"city": city, "stations": stations}, "banner": b})

    for hours in (24, 168):
        rows = get_trend(hours=hours)
        for r in rows:
            for k, v in list(r.items()):
                if isinstance(v, float):
                    r[k] = round(v, 1)
        write(
            f"trend_{hours}.json",
            {"ok": True, "data": {"hours": hours, "series": rows}, "banner": b},
        )

    # Risk placeholder (same logic as Flask Phase 1)
    trend = get_trend(hours=24)
    last_pm = (trend[-1].get("PM25") if trend else 40) or 40
    hours_out = []
    for i in range(1, 25):
        base = trend[min(i - 1, len(trend) - 1)].get("PM25") or last_pm
        pred = round(0.7 * last_pm + 0.3 * base, 1)
        g = pm25_grade(pred)
        hours_out.append(
            {
                "hour_ahead": i,
                "pm25_estimate": pred,
                "level": g["level"],
                "risk": g["risk"],
                "color": g["color"],
            }
        )
    write(
        "risk.json",
        {
            "ok": True,
            "data": {
                "method": "placeholder_diurnal_blend",
                "note": "静态演示站占位风险估计，非机器学习预测。",
                "bands": {
                    "h6": hours_out[5]["risk"],
                    "h12": hours_out[11]["risk"],
                    "h18": hours_out[17]["risk"],
                    "h24": hours_out[23]["risk"],
                },
                "hourly": hours_out,
            },
            "banner": b,
        },
    )
    print("export done")


if __name__ == "__main__":
    main()
