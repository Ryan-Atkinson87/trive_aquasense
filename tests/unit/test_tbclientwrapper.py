import sys
from unittest.mock import MagicMock

# tb_device_mqtt imports pkg_resources internally, which is unavailable in Python 3.13+
# with modern setuptools. All tests mock TBDeviceMqttClient anyway, so we stub the
# module here to prevent the import from failing.
sys.modules.setdefault("tb_device_mqtt", MagicMock())

import pytest
from unittest.mock import patch
from monitoring_service.transport.thingsboard_client import ThingsboardClient


@pytest.fixture
def dummy_logger():
    class DummyLogger:
        def error(self, msg):
            print(f"LOG ERROR: {msg}")

        def warning(self, msg):
            print(f"LOG WARNING: {msg}")

        def info(self, msg):
            print(f"LOG INFO: {msg}")

    return DummyLogger()


@pytest.fixture
def client(dummy_logger):
    return ThingsboardClient(tb_server="test_server", tb_token="test_token", logger=dummy_logger)


def test_connect_success(dummy_logger):
    mock_client = MagicMock()
    client = ThingsboardClient("server", "token", dummy_logger, client_class=lambda *args, **kwargs: mock_client)
    client.connect()
    mock_client.connect.assert_called_once()


def test_connect_failure_logs_and_raises(dummy_logger):
    mock_client = MagicMock()
    mock_client.connect.side_effect = Exception("connection failed")
    client = ThingsboardClient("server", "token", dummy_logger, client_class=lambda *args, **kwargs: mock_client)

    with pytest.raises(Exception):
        client.connect()


@patch("monitoring_service.transport.thingsboard_client.TBDeviceMqttClient")
def test_send_telemetry_skips_empty(mock_mqtt, client):
    client.send_telemetry({})
    mock_mqtt.return_value.send_telemetry.assert_not_called()


def test_send_telemetry_success(dummy_logger):
    mock_client = MagicMock()
    client = ThingsboardClient("server", "token", dummy_logger, client_class=lambda *args, **kwargs: mock_client)
    client.send_telemetry({"cpu": 50})
    mock_client.send_telemetry.assert_called_once()


def test_send_attributes_success(dummy_logger):
    mock_client = MagicMock()
    client = ThingsboardClient("server", "token", dummy_logger, client_class=lambda *args, **kwargs: mock_client)
    client.send_attributes({"device_name": "test_device"})
    mock_client.send_attributes.assert_called_once_with({"device_name": "test_device"})


def test_disconnect_success(dummy_logger):
    mock_client = MagicMock()
    client = ThingsboardClient("server", "token", dummy_logger, client_class=lambda *args, **kwargs: mock_client)
    client.disconnect()
    mock_client.disconnect.assert_called_once()


# ---------- Retry / back-off ----------

def _make_client(dummy_logger, mock_client, max_retries=2, retry_base_delay=0.0):
    return ThingsboardClient(
        "server", "token", dummy_logger,
        client_class=lambda *args, **kwargs: mock_client,
        max_retries=max_retries,
        retry_base_delay=retry_base_delay,
    )


def test_send_telemetry_retries_on_failure(dummy_logger, monkeypatch):
    monkeypatch.setattr("monitoring_service.transport.thingsboard_client.time.sleep", lambda _: None)
    mock_client = MagicMock()
    mock_client.send_telemetry.side_effect = [Exception("fail"), Exception("fail"), None]
    client = _make_client(dummy_logger, mock_client, max_retries=2)
    client.send_telemetry({"cpu": 50})
    assert mock_client.send_telemetry.call_count == 3


def test_send_telemetry_exhausts_retries_and_logs_error(dummy_logger, monkeypatch):
    monkeypatch.setattr("monitoring_service.transport.thingsboard_client.time.sleep", lambda _: None)
    mock_client = MagicMock()
    mock_client.send_telemetry.side_effect = Exception("always fails")
    client = _make_client(dummy_logger, mock_client, max_retries=2)
    client.send_telemetry({"cpu": 50})
    assert mock_client.send_telemetry.call_count == 3


def test_send_attributes_retries_on_failure(dummy_logger, monkeypatch):
    monkeypatch.setattr("monitoring_service.transport.thingsboard_client.time.sleep", lambda _: None)
    mock_client = MagicMock()
    mock_client.send_attributes.side_effect = [Exception("fail"), None]
    client = _make_client(dummy_logger, mock_client, max_retries=2)
    client.send_attributes({"device_name": "test"})
    assert mock_client.send_attributes.call_count == 2


def test_send_retry_sleeps_with_exponential_backoff(dummy_logger, monkeypatch):
    sleep_calls = []
    monkeypatch.setattr(
        "monitoring_service.transport.thingsboard_client.time.sleep",
        lambda d: sleep_calls.append(d),
    )
    mock_client = MagicMock()
    mock_client.send_telemetry.side_effect = Exception("always fails")
    client = _make_client(dummy_logger, mock_client, max_retries=3, retry_base_delay=1.0)
    client.send_telemetry({"cpu": 50})
    assert sleep_calls == [1.0, 2.0, 4.0]


def test_send_no_retry_when_max_retries_zero(dummy_logger, monkeypatch):
    sleep_calls = []
    monkeypatch.setattr(
        "monitoring_service.transport.thingsboard_client.time.sleep",
        lambda d: sleep_calls.append(d),
    )
    mock_client = MagicMock()
    mock_client.send_telemetry.side_effect = Exception("fail")
    client = _make_client(dummy_logger, mock_client, max_retries=0)
    client.send_telemetry({"cpu": 50})
    assert mock_client.send_telemetry.call_count == 1
    assert sleep_calls == []
