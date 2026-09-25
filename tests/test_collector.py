"""Tests du module app.collector."""
import subprocess

import pytest

from app.collector import (
    MetricsCollectionError,
    collect_system_metrics,
    get_load_average,
)


def test_collect_system_metrics_has_expected_shape():
    metrics = collect_system_metrics()

    assert {"timestamp", "hostname", "cpu", "memory", "system"} <= metrics.keys()
    assert "percent" in metrics["cpu"]
    assert "total_bytes" in metrics["memory"]


def test_get_load_average_raises_on_subprocess_failure(monkeypatch):
    def fake_run(*args, **kwargs):
        raise subprocess.CalledProcessError(returncode=1, cmd="uptime")

    monkeypatch.setattr("app.collector.platform.system", lambda: "Linux")
    monkeypatch.setattr("app.collector.subprocess.run", fake_run)

    with pytest.raises(MetricsCollectionError):
        get_load_average()


def test_get_load_average_returns_none_values_on_windows(monkeypatch):
    monkeypatch.setattr("app.collector.platform.system", lambda: "Windows")

    result = get_load_average()

    assert result == {"load_1m": None, "load_5m": None, "load_15m": None}


def test_get_load_average_raises_on_unparsable_output(monkeypatch):
    class FakeResult:
        stdout = "unexpected output without the expected marker"

    monkeypatch.setattr("app.collector.platform.system", lambda: "Linux")
    monkeypatch.setattr(
        "app.collector.subprocess.run", lambda *a, **k: FakeResult()
    )

    with pytest.raises(MetricsCollectionError):
        get_load_average()
