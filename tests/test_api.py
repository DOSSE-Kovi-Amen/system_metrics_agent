"""Tests de l'API app.api."""
import pytest
from fastapi.testclient import TestClient

from app.api import app, received_metrics


@pytest.fixture(autouse=True)
def _reset_state():
    received_metrics.clear()
    yield
    received_metrics.clear()


@pytest.fixture
def client():
    return TestClient(app)


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_get_metrics_empty(client):
    response = client.get("/metrics")

    assert response.status_code == 200
    assert response.json() == {"total": 0, "metrics": []}


def test_post_then_get_metrics(client):
    payload = {
        "agent": "test-agent",
        "event_type": "system_metrics",
        "data": {"cpu": {"percent": 12.5}},
    }

    post_response = client.post("/metrics", json=payload)
    assert post_response.status_code == 201
    assert post_response.json()["total_received"] == 1

    get_response = client.get("/metrics")
    assert get_response.json()["total"] == 1


def test_latest_metrics_returns_404_when_empty(client):
    response = client.get("/metrics/latest")

    assert response.status_code == 404


def test_latest_metrics_returns_last_item(client):
    client.post(
        "/metrics",
        json={"agent": "a1", "event_type": "system_metrics", "data": {}},
    )
    client.post(
        "/metrics",
        json={"agent": "a2", "event_type": "system_metrics", "data": {}},
    )

    response = client.get("/metrics/latest")

    assert response.status_code == 200
    assert response.json()["agent"] == "a2"
