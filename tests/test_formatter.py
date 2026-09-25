"""Tests du module app.formatter."""
import pytest

from app.formatter import format_metrics


def _valid_metrics() -> dict:
    return {
        "timestamp": "2026-01-01T00:00:00+00:00",
        "hostname": "test-host",
        "cpu": {"percent": 10.0, "logical_cores": 4},
        "memory": {
            "total_bytes": 1000,
            "available_bytes": 500,
            "used_bytes": 500,
            "percent": 50.0,
        },
        "system": {"load_1m": 0.1, "load_5m": 0.2, "load_15m": 0.3},
    }


def test_format_metrics_returns_expected_envelope():
    payload = format_metrics(_valid_metrics())

    assert payload["agent"] == "system-metrics-agent"
    assert payload["event_type"] == "system_metrics"
    assert payload["data"] == _valid_metrics()


def test_format_metrics_accepts_custom_agent_name():
    payload = format_metrics(_valid_metrics(), agent_name="custom-agent")

    assert payload["agent"] == "custom-agent"


def test_format_metrics_raises_on_missing_keys():
    incomplete = _valid_metrics()
    del incomplete["cpu"]

    with pytest.raises(ValueError):
        format_metrics(incomplete)
