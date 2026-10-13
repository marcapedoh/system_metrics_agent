import pytest
from fastapi.testclient import TestClient

from app import api


@pytest.fixture
def client():
    api.received_metrics.clear()
    yield TestClient(api.app)
    api.received_metrics.clear()


def valid_payload():
    return {
        "agent": "system-metrics-agent",
        "event_type": "system_metrics",
        "data": {"hostname": "test-host", "cpu": {"percent": 12.5}},
    }


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_latest_without_metrics_returns_404(client):
    response = client.get("/metrics/latest")

    assert response.status_code == 404


def test_post_then_latest(client):
    created = client.post("/metrics", json=valid_payload())
    latest = client.get("/metrics/latest")

    assert created.status_code == 201
    assert created.json()["total_received"] == 1
    assert latest.status_code == 200
    assert latest.json()["data"]["hostname"] == "test-host"
    assert "received_at" in latest.json()


def test_list_metrics(client):
    client.post("/metrics", json=valid_payload())
    client.post("/metrics", json=valid_payload())

    response = client.get("/metrics")

    assert response.json()["total"] == 2


def test_invalid_payload_is_rejected(client):
    response = client.post("/metrics", json={"agent": "", "data": {}})

    assert response.status_code == 422