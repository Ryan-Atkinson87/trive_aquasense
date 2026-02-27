import sys
from unittest.mock import MagicMock

# tb_device_mqtt imports pkg_resources internally, which is unavailable in Python 3.13+
# with modern setuptools. All tests mock TBDeviceMqttClient anyway, so we stub the
# module here to prevent the import from failing.
sys.modules.setdefault("tb_device_mqtt", MagicMock())

import pytest
from unittest.mock import patch
from monitoring_service.TBClientWrapper import TBClientWrapper


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
    return TBClientWrapper(tb_server="test_server", tb_token="test_token", logger=dummy_logger)


def test_connect_success(dummy_logger):
    mock_client = MagicMock()
    client = TBClientWrapper("server", "token", dummy_logger, client_class=lambda *args, **kwargs: mock_client)
    client.connect()
    mock_client.connect.assert_called_once()


def test_connect_failure_logs_and_raises(dummy_logger):
    mock_client = MagicMock()
    mock_client.connect.side_effect = Exception("connection failed")
    client = TBClientWrapper("server", "token", dummy_logger, client_class=lambda *args, **kwargs: mock_client)

    with pytest.raises(Exception):
        client.connect()


@patch("monitoring_service.TBClientWrapper.TBDeviceMqttClient")
def test_send_telemetry_skips_empty(mock_mqtt, client):
    client.send_telemetry({})
    mock_mqtt.return_value.send_telemetry.assert_not_called()


def test_send_telemetry_success(dummy_logger):
    mock_client = MagicMock()
    client = TBClientWrapper("server", "token", dummy_logger, client_class=lambda *args, **kwargs: mock_client)
    client.send_telemetry({"cpu": 50})
    mock_client.send_telemetry.assert_called_once()


def test_send_attributes_success(dummy_logger):
    mock_client = MagicMock()
    client = TBClientWrapper("server", "token", dummy_logger, client_class=lambda *args, **kwargs: mock_client)
    client.send_attributes({"device_name": "test_device"})
    mock_client.send_attributes.assert_called_once_with({"device_name": "test_device"})


def test_disconnect_success(dummy_logger):
    mock_client = MagicMock()
    client = TBClientWrapper("server", "token", dummy_logger, client_class=lambda *args, **kwargs: mock_client)
    client.disconnect()
    mock_client.disconnect.assert_called_once()
