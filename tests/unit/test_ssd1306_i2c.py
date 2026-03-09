import sys
import time
from unittest.mock import MagicMock

# Hardware stubs (board, busio, adafruit_ssd1306) are set up in conftest.py
# before this module is collected.  Tests configure the shared mock directly
# via sys.modules["adafruit_ssd1306"] so the driver module's captured
# reference is used when SSD1306I2CDisplay instantiates the hardware object.

from monitoring_service.outputs.display.ssd1306_i2c import SSD1306I2CDisplay
from monitoring_service.outputs.display.models import DisplayContent


def make_content(lines=None, timestamp_str="12:34 08/03/2026"):
    return DisplayContent(
        lines=lines or ["WATER:24.5C", "AIR:19.2C", "HUMID:45.0%"],
        timestamp_str=timestamp_str,
    )


def test_ssd1306_display_init_and_render():
    mock_oled = MagicMock()
    sys.modules["adafruit_ssd1306"].SSD1306_I2C.return_value = mock_oled

    config = {
        "enabled": True,
        "refresh_period": 0,
        "width": 128,
        "height": 32,
        "address": 0x3C,
    }

    display = SSD1306I2CDisplay(config)
    display.render(make_content())

    mock_oled.image.assert_called_once()
    mock_oled.show.assert_called()


def test_ssd1306_render_skips_when_refresh_period_not_elapsed():
    mock_oled = MagicMock()
    sys.modules["adafruit_ssd1306"].SSD1306_I2C.return_value = mock_oled

    config = {
        "enabled": True,
        "refresh_period": 9999,
        "width": 128,
        "height": 32,
        "address": 0x3C,
    }

    display = SSD1306I2CDisplay(config)
    display._last_render_ts = time.time()  # simulate a recent render

    display.render(make_content())

    mock_oled.image.assert_not_called()


def test_ssd1306_render_with_empty_lines():
    mock_oled = MagicMock()
    sys.modules["adafruit_ssd1306"].SSD1306_I2C.return_value = mock_oled

    config = {
        "enabled": True,
        "refresh_period": 0,
        "width": 128,
        "height": 32,
        "address": 0x3C,
    }

    display = SSD1306I2CDisplay(config)
    display.render(DisplayContent(lines=[], timestamp_str=""))

    mock_oled.image.assert_called_once()
    mock_oled.show.assert_called()


def test_ssd1306_system_screen_render_is_noop():
    mock_oled = MagicMock()
    sys.modules["adafruit_ssd1306"].SSD1306_I2C.return_value = mock_oled

    config = {
        "enabled": True,
        "refresh_period": 0,
        "system_screen": True,
        "width": 128,
        "height": 32,
        "address": 0x3C,
    }

    display = SSD1306I2CDisplay(config)
    mock_oled.reset_mock()

    display.render(make_content())

    mock_oled.image.assert_not_called()
    mock_oled.show.assert_not_called()


def test_ssd1306_system_screen_render_startup_scrolls_messages():
    mock_oled = MagicMock()
    sys.modules["adafruit_ssd1306"].SSD1306_I2C.return_value = mock_oled

    config = {
        "enabled": True,
        "refresh_period": 0,
        "system_screen": True,
        "_version_header": "Aquasense v2.6.0",
        "width": 128,
        "height": 32,
        "address": 0x3C,
    }

    display = SSD1306I2CDisplay(config)
    assert display.system_screen is True
    assert display.show_startup is True

    display.render_startup("Connecting...")
    assert list(display._messages) == ["Connecting..."]

    display.render_startup("Connected")
    assert list(display._messages) == ["Connecting...", "Connected"]

    display.render_startup("Collected 14:32:00")
    assert list(display._messages) == ["Connected", "Collected 14:32:00"]

    # Each call should push to hardware
    assert mock_oled.show.call_count >= 3


def test_ssd1306_system_screen_uses_version_header_from_config():
    mock_oled = MagicMock()
    sys.modules["adafruit_ssd1306"].SSD1306_I2C.return_value = mock_oled

    config = {
        "enabled": True,
        "refresh_period": 0,
        "system_screen": True,
        "_version_header": "Aquasense v9.9.9",
        "width": 128,
        "height": 32,
        "address": 0x3C,
    }

    display = SSD1306I2CDisplay(config)
    assert display._header == "Aquasense v9.9.9"


def test_ssd1306_system_screen_falls_back_to_default_header():
    mock_oled = MagicMock()
    sys.modules["adafruit_ssd1306"].SSD1306_I2C.return_value = mock_oled

    config = {
        "enabled": True,
        "refresh_period": 0,
        "system_screen": True,
        "width": 128,
        "height": 32,
        "address": 0x3C,
    }

    display = SSD1306I2CDisplay(config)
    assert display._header == "Aquasense"