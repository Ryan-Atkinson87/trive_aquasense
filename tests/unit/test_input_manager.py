import logging
from unittest.mock import MagicMock, patch
from monitoring_service.inputs.input_manager import InputManager


def make_logger():
    return MagicMock(spec=logging.Logger)


def test_collect_delegates_to_collector():
    logger = make_logger()
    mock_bundle = MagicMock()
    mock_telemetry = {"water_temperature": 24.5}

    with patch("monitoring_service.inputs.input_manager.SensorFactory") as MockFactory, \
         patch("monitoring_service.inputs.input_manager.TelemetryCollector") as MockCollector:
        MockFactory.return_value.build_all.return_value = [mock_bundle]
        MockCollector.return_value.as_dict.return_value = mock_telemetry

        manager = InputManager(sensors_config=[{"type": "ds18b20", "id": "28-abc"}], logger=logger)
        result = manager.collect()

    assert result == mock_telemetry
    MockCollector.return_value.as_dict.assert_called_once()


def test_empty_config_logs_warning():
    logger = make_logger()

    with patch("monitoring_service.inputs.input_manager.SensorFactory") as MockFactory, \
         patch("monitoring_service.inputs.input_manager.TelemetryCollector"):
        MockFactory.return_value.build_all.return_value = []
        InputManager(sensors_config=[], logger=logger)

    logger.warning.assert_called_once()


def test_collect_returns_empty_when_no_bundles():
    logger = make_logger()

    with patch("monitoring_service.inputs.input_manager.SensorFactory") as MockFactory, \
         patch("monitoring_service.inputs.input_manager.TelemetryCollector") as MockCollector:
        MockFactory.return_value.build_all.return_value = []
        MockCollector.return_value.as_dict.return_value = {}

        manager = InputManager(sensors_config=[], logger=logger)
        result = manager.collect()

    assert result == {}