import pytest

from app.config import Settings


def test_defaults(monkeypatch):
    for name in ("METRICS_ENDPOINT", "COLLECTION_INTERVAL", "REQUEST_TIMEOUT"):
        monkeypatch.delenv(name, raising=False)

    settings = Settings.from_env()

    assert settings.metrics_endpoint == "http://127.0.0.1:8000/metrics"
    assert settings.collection_interval == 5
    assert settings.request_timeout == 5


def test_values_from_environment(monkeypatch):
    monkeypatch.setenv("METRICS_ENDPOINT", "http://api:8000/metrics")
    monkeypatch.setenv("COLLECTION_INTERVAL", "2.5")
    monkeypatch.setenv("REQUEST_TIMEOUT", "3")

    settings = Settings.from_env()

    assert settings.metrics_endpoint == "http://api:8000/metrics"
    assert settings.collection_interval == 2.5
    assert settings.request_timeout == 3


@pytest.mark.parametrize("value", ["abc", "0", "-1"])
def test_invalid_interval(monkeypatch, value):
    monkeypatch.setenv("COLLECTION_INTERVAL", value)

    with pytest.raises(ValueError):
        Settings.from_env()
