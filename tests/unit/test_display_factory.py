import logging
from unittest.mock import MagicMock, patch

# Hardware stubs (board, busio, adafruit_ssd1306, spidev, RPi.GPIO) are set up
# in conftest.py before this module is collected.

from monitoring_service.outputs.display import factory as display_factory


def make_logger():
    return MagicMock(spec=logging.Logger)


def test_empty_config_returns_empty_list():
    logger = make_logger()
    result = display_factory.build_displays([], logger)
    assert result == []
    logger.info.assert_called()


def test_disabled_display_is_skipped():
    logger = make_logger()
    config = [{"type": "logging", "enabled": False}]
    with patch.dict(display_factory._DISPLAY_TYPES, {"logging": MagicMock()}):
        result = display_factory.build_displays(config, logger)
    assert result == []


def test_missing_type_is_skipped_with_warning():
    logger = make_logger()
    config = [{"enabled": True}]
    result = display_factory.build_displays(config, logger)
    assert result == []
    logger.warning.assert_called_once()


def test_unknown_type_is_skipped_with_warning():
    logger = make_logger()
    config = [{"type": "nonexistent", "enabled": True}]
    result = display_factory.build_displays(config, logger)
    assert result == []
    logger.warning.assert_called_once()


def test_failed_init_is_skipped_with_warning():
    logger = make_logger()
    mock_class = MagicMock(side_effect=Exception("init failed"))
    config = [{"type": "logging", "enabled": True}]
    with patch.dict(display_factory._DISPLAY_TYPES, {"logging": mock_class}):
        result = display_factory.build_displays(config, logger)
    assert result == []
    logger.warning.assert_called_once()


def test_valid_display_is_built_and_returned():
    logger = make_logger()
    mock_instance = MagicMock()
    mock_class = MagicMock(return_value=mock_instance)
    config = [{"type": "logging", "enabled": True}]
    with patch.dict(display_factory._DISPLAY_TYPES, {"logging": mock_class}):
        result = display_factory.build_displays(config, logger)
    assert result == [mock_instance]


def test_mixed_valid_and_invalid_displays():
    logger = make_logger()
    mock_instance = MagicMock()
    mock_valid = MagicMock(return_value=mock_instance)
    mock_invalid = MagicMock(side_effect=Exception("fail"))
    config = [
        {"type": "valid", "enabled": True},
        {"type": "broken", "enabled": True},
    ]
    with patch.dict(display_factory._DISPLAY_TYPES, {"valid": mock_valid, "broken": mock_invalid}):
        result = display_factory.build_displays(config, logger)
    assert result == [mock_instance]