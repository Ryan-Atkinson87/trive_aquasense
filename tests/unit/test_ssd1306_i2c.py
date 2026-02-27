import sys
import time
from unittest.mock import MagicMock

# Hardware stubs (board, busio, adafruit_ssd1306) are set up in conftest.py
# before this module is collected.  Tests configure the shared mock directly
# via sys.modules["adafruit_ssd1306"] so the driver module's captured
# reference is used when SSD1306I2CDisplay instantiates the hardware object.

from monitoring_service.outputs.display.ssd1306_i2c import SSD1306I2CDisplay


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

    snapshot = {
        "ts": int(time.time() * 1000),
        "device_name": "test_device",
        "values": {
            "water_temperature": 24.5,
            "air_temperature": 19.2,
            "air_humidity": 45.0,
        },
    }

    display.render(snapshot)

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

    display.render({"ts": 0, "device_name": "test", "values": {}})

    mock_oled.image.assert_not_called()


def test_ssd1306_render_with_none_values_uses_placeholders():
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

    snapshot = {
        "ts": int(time.time() * 1000),
        "device_name": "test",
        "values": {},
    }

    display.render(snapshot)

    mock_oled.image.assert_called_once()
    mock_oled.show.assert_called()
