from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app, raise_server_exceptions=False)


def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_invalid_horizon():
    res = client.get("/api/forecast", params={"horizon": 9})
    assert res.status_code == 422


def test_dashboard_json_or_untrained():
    res = client.get("/api/dashboard")
    assert res.status_code in (200, 503)
    if res.status_code == 200:
        body = res.json()
        assert "kpis" in body
        assert "total_revenue" in body["kpis"]
        assert "inventory_risk" in body


def test_inventory_json_or_untrained():
    res = client.get("/api/inventory/risk")
    assert res.status_code in (200, 503)
    if res.status_code == 200:
        body = res.json()
        assert body["table"]
        assert "Needs attention" in body["plain_rule"]
