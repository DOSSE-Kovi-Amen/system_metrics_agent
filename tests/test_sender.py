"""Tests du module app.sender."""
import requests
import pytest

from app.sender import MetricsDeliveryError, send_metrics


class FakeResponse:
    def __init__(self, status_code=200, json_body=None, raise_exc=None):
        self.status_code = status_code
        self._json_body = json_body or {"status": "received"}
        self._raise_exc = raise_exc

    def raise_for_status(self):
        if self._raise_exc:
            raise self._raise_exc

    def json(self):
        return self._json_body


def test_send_metrics_success(monkeypatch):
    def fake_post(url, json, timeout):
        assert url == "http://api:8000/metrics"
        return FakeResponse(status_code=201, json_body={"status": "received"})

    monkeypatch.setattr("app.sender.requests.post", fake_post)

    result = send_metrics("http://api:8000/metrics", {"agent": "x"})

    assert result["status_code"] == 201
    assert result["response"] == {"status": "received"}


def test_send_metrics_raises_on_connection_error(monkeypatch):
    def fake_post(url, json, timeout):
        raise requests.ConnectionError("boom")

    monkeypatch.setattr("app.sender.requests.post", fake_post)

    with pytest.raises(MetricsDeliveryError):
        send_metrics("http://api:8000/metrics", {"agent": "x"})


def test_send_metrics_raises_on_http_error(monkeypatch):
    def fake_post(url, json, timeout):
        return FakeResponse(
            status_code=500,
            raise_exc=requests.HTTPError("server error"),
        )

    monkeypatch.setattr("app.sender.requests.post", fake_post)

    with pytest.raises(MetricsDeliveryError):
        send_metrics("http://api:8000/metrics", {"agent": "x"})
