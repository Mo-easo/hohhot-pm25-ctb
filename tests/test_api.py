"""Phase 1 API smoke tests."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import app


def test_health_ok():
    client = app.test_client()
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    assert data["data"]["status"] == "healthy"


def test_latest_has_banner_and_not_realtime():
    client = app.test_client()
    res = client.get("/api/latest")
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    assert "banner" in data
    assert data["banner"]["is_realtime"] is False
    assert data["data"]["city"]["PM25"] is not None


def test_trend_invalid_hours():
    client = app.test_client()
    res = client.get("/api/trend?hours=10")
    assert res.status_code == 400
    data = res.get_json()
    assert data["ok"] is False
    assert data["error"]["code"] == "invalid_param"


def test_stations():
    client = app.test_client()
    res = client.get("/api/stations")
    assert res.status_code == 200
    data = res.get_json()
    assert len(data["data"]) >= 1


def test_pages_render():
    client = app.test_client()
    for path in ["/", "/monitor", "/map", "/analysis", "/prediction", "/research", "/about", "/data-source"]:
        res = client.get(path)
        assert res.status_code == 200, path
