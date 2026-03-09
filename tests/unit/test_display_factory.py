import logging
from unittest.mock import MagicMock, patch
import pytest

# Hardware stubs (board, busio, adafruit_ssd1306, spidev, RPi.GPIO) are set up
# in conftest.py before this module is collected.

from monitoring_service.outputs.display.factory import DisplayFactory
from monitoring_service.outputs.display.base import BaseDisplay
from monitoring_service.outputs.display.models import DisplayBundle


def make_logger():
    return MagicMock(spec=logging.Logger)


def make_mock_driver(system_screen=False, show_startup=False):
    driver = MagicMock(spec=BaseDisplay)
    driver.system_screen = system_screen
    driver.show_startup = show_startup
    return driver


def make_mock_driver_class(system_screen=False, show_startup=False):
    driver = make_mock_driver(system_screen=system_screen, show_startup=show_startup)
    return MagicMock(return_value=driver)


def test_empty_config_returns_empty_list():
    logger = make_logger()
    factory = DisplayFactory()
    result = factory.build_all([], logger)
    assert result == []
    logger.info.assert_called()


def test_disabled_display_is_skipped():
    logger = make_logger()
    factory = DisplayFactory(registry={"logging": make_mock_driver_class()})
    config = [{"type": "logging", "enabled": False}]
    result = factory.build_all(config, logger)
    assert result == []


def test_missing_type_is_skipped_with_warning():
    logger = make_logger()
    factory = DisplayFactory()
    config = [{"enabled": True}]
    result = factory.build_all(config, logger)
    assert result == []
    logger.warning.assert_called_once()


def test_unknown_type_is_skipped_with_warning():
    logger = make_logger()
    factory = DisplayFactory()
    config = [{"type": "nonexistent", "enabled": True}]
    result = factory.build_all(config, logger)
    assert result == []
    logger.warning.assert_called_once()


def test_failed_init_is_skipped_with_warning():
    logger = make_logger()
    mock_class = MagicMock(side_effect=Exception("init failed"))
    factory = DisplayFactory(registry={"logging": mock_class})
    config = [{"type": "logging", "enabled": True}]
    result = factory.build_all(config, logger)
    assert result == []
    logger.warning.assert_called_once()


def test_valid_display_returns_bundle():
    logger = make_logger()
    mock_class = make_mock_driver_class()
    factory = DisplayFactory(registry={"logging": mock_class})
    config = [{"type": "logging", "enabled": True}]
    result = factory.build_all(config, logger)
    assert len(result) == 1
    assert isinstance(result[0], DisplayBundle)
    assert result[0].driver is mock_class.return_value


def test_mixed_valid_and_invalid_displays():
    logger = make_logger()
    mock_valid = make_mock_driver_class()
    mock_invalid = MagicMock(side_effect=Exception("fail"))
    factory = DisplayFactory(registry={"valid": mock_valid, "broken": mock_invalid})
    config = [
        {"type": "valid", "enabled": True},
        {"type": "broken", "enabled": True},
    ]
    result = factory.build_all(config, logger)
    assert len(result) == 1
    assert result[0].driver is mock_valid.return_value


def test_version_header_injected_into_system_screen_display():
    logger = make_logger()
    received_config = {}

    def capture_config(cfg):
        received_config.update(cfg)
        return make_mock_driver(system_screen=True, show_startup=True)

    factory = DisplayFactory(registry={"logging": capture_config})
    config = [{"type": "logging", "enabled": True, "system_screen": True}]
    factory.build_all(config, logger, version="2.6.0")

    assert received_config.get("_version_header") == "Aquasense v2.6.0"


def test_version_header_not_injected_without_system_screen():
    logger = make_logger()
    received_config = {}

    def capture_config(cfg):
        received_config.update(cfg)
        return make_mock_driver()

    factory = DisplayFactory(registry={"logging": capture_config})
    config = [{"type": "logging", "enabled": True}]
    factory.build_all(config, logger, version="2.6.0")

    assert "_version_header" not in received_config


def test_bundle_carries_system_screen_from_driver():
    logger = make_logger()
    mock_class = make_mock_driver_class(system_screen=True, show_startup=True)
    factory = DisplayFactory(registry={"sys": mock_class})
    config = [{"type": "sys", "enabled": True, "system_screen": True}]
    result = factory.build_all(config, logger)
    assert result[0].system_screen is True
    assert result[0].show_startup is True


def test_bundle_carries_show_startup_from_driver():
    logger = make_logger()
    mock_class = make_mock_driver_class(show_startup=True)
    factory = DisplayFactory(registry={"startup": mock_class})
    config = [{"type": "startup", "enabled": True, "show_startup": True}]
    result = factory.build_all(config, logger)
    assert result[0].show_startup is True
    assert result[0].system_screen is False


def test_register_adds_new_type():
    logger = make_logger()
    factory = DisplayFactory(registry={})

    class CustomDisplay(BaseDisplay):
        def render(self, content):
            pass

        def render_startup(self, message):
            pass

        def close(self):
            pass

    factory.register("custom", CustomDisplay)
    config = [{"type": "custom", "enabled": True}]
    result = factory.build_all(config, logger)
    assert len(result) == 1
    assert isinstance(result[0].driver, CustomDisplay)


def test_register_rejects_non_string_type():
    factory = DisplayFactory()
    with pytest.raises(ValueError):
        factory.register(123, MagicMock())


def test_register_rejects_non_base_display_subclass():
    factory = DisplayFactory()
    with pytest.raises(ValueError):
        factory.register("bad", object)


def test_build_raises_on_missing_type():
    factory = DisplayFactory()
    with pytest.raises(ValueError):
        factory.build({"enabled": True})


def test_build_raises_on_unknown_type():
    factory = DisplayFactory()
    with pytest.raises(ValueError):
        factory.build({"type": "unknown", "enabled": True})