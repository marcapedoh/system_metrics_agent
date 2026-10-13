import threading
from unittest.mock import patch

from app import agent
from app.config import Settings
from app.sender import MetricsDeliveryError

SETTINGS = Settings(
    metrics_endpoint="http://api:8000/metrics",
    collection_interval=0.01,
    request_timeout=1,
)


@patch("app.agent.send_metrics")
@patch("app.agent.collect_system_metrics")
def test_run_once_chains_collect_format_send(mock_collect, mock_send):
    mock_collect.return_value = {
        "timestamp": "t",
        "hostname": "h",
        "cpu": {},
        "memory": {},
        "system": {},
    }
    mock_send.return_value = {"status_code": 201, "response": {}}

    result = agent.run_once(SETTINGS)

    assert result["status_code"] == 201
    sent_payload = mock_send.call_args.kwargs["payload"]
    assert sent_payload["event_type"] == "system_metrics"
    assert mock_send.call_args.kwargs["endpoint"] == SETTINGS.metrics_endpoint


@patch("app.agent.Settings.from_env", return_value=SETTINGS)
@patch("app.agent.run_once")
def test_run_forever_stops_on_event_and_survives_errors(mock_run_once, _settings):
    event = threading.Event()
    calls = []

    def fake_run_once(_settings):
        calls.append(1)
        if len(calls) == 1:
            raise MetricsDeliveryError("API indisponible")
        event.set()
        return {"status_code": 201}

    mock_run_once.side_effect = fake_run_once

    agent.run_forever(event)

    assert len(calls) == 2


def test_signal_handler_sets_stop_event():
    agent.stop_event.clear()

    agent._request_stop(15, None)

    assert agent.stop_event.is_set()
    agent.stop_event.clear()
