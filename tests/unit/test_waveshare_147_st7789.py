import sys
import time
from unittest.mock import MagicMock, call

import pytest

# ---- Mock hardware modules BEFORE import ----
mock_gpio = MagicMock()
mock_spidev = MagicMock()
mock_rpi = MagicMock()
mock_rpi.GPIO = mock_gpio
sys.modules["RPi"] = mock_rpi
sys.modules["RPi.GPIO"] = mock_gpio
sys.modules["spidev"] = mock_spidev

from monitoring_service.outputs.display.waveshare_147_st7789 import (
    Waveshare147ST7789Display,
)


@pytest.fixture()
def valid_config():
    return {
        "refresh_period": 0,
        "spi": {
            "bus": 0,
            "device": 0,
            "mode": 0,
            "max_speed_hz": 40_000_000,
        },
        "pins": {
            "dc": 25,
            "reset": 27,
            "backlight": 18,
        },
    }


@pytest.fixture(autouse=True)
def _reset_mocks():
    """Reset mocks before each test so state doesn't leak."""
    mock_gpio.reset_mock()
    mock_spidev.reset_mock()
    mock_spidev.SpiDev.return_value = MagicMock()


@pytest.fixture()
def display(valid_config):
    return Waveshare147ST7789Display(valid_config)


@pytest.fixture()
def full_snapshot():
    return {
        "ts": time.time(),
        "device_name": "test_device",
        "values": {
            "water_temperature": 24.5,
            "air_temperature": 19.2,
            "air_humidity": 45.0,
            "water_flow": 1.5,
        },
    }


# ------------------------------------------------------------------
# Config validation
# ------------------------------------------------------------------


class TestConfigValidation:
    def test_missing_spi_key_raises(self, valid_config):
        del valid_config["spi"]
        with pytest.raises(ValueError, match="missing 'spi'"):
            Waveshare147ST7789Display(valid_config)

    def test_missing_pins_key_raises(self, valid_config):
        del valid_config["pins"]
        with pytest.raises(ValueError, match="missing 'pins'"):
            Waveshare147ST7789Display(valid_config)

    def test_missing_spi_bus_raises(self, valid_config):
        del valid_config["spi"]["bus"]
        with pytest.raises(ValueError, match="SPI config missing 'bus'"):
            Waveshare147ST7789Display(valid_config)

    def test_missing_spi_device_raises(self, valid_config):
        del valid_config["spi"]["device"]
        with pytest.raises(ValueError, match="SPI config missing 'device'"):
            Waveshare147ST7789Display(valid_config)

    def test_missing_pin_dc_raises(self, valid_config):
        del valid_config["pins"]["dc"]
        with pytest.raises(ValueError, match="Pin config missing 'dc'"):
            Waveshare147ST7789Display(valid_config)

    def test_missing_pin_reset_raises(self, valid_config):
        del valid_config["pins"]["reset"]
        with pytest.raises(ValueError, match="Pin config missing 'reset'"):
            Waveshare147ST7789Display(valid_config)

    def test_missing_pin_backlight_raises(self, valid_config):
        del valid_config["pins"]["backlight"]
        with pytest.raises(ValueError, match="Pin config missing 'backlight'"):
            Waveshare147ST7789Display(valid_config)


# ------------------------------------------------------------------
# Initialisation
# ------------------------------------------------------------------


class TestInit:
    def test_gpio_pins_configured(self, display):
        mock_gpio.setmode.assert_called_with(mock_gpio.BCM)
        mock_gpio.setup.assert_any_call(25, mock_gpio.OUT)
        mock_gpio.setup.assert_any_call(27, mock_gpio.OUT)
        mock_gpio.setup.assert_any_call(18, mock_gpio.OUT)

    def test_spi_opened_with_config(self, display):
        spi = mock_spidev.SpiDev.return_value
        spi.open.assert_called_once_with(0, 0)
        assert spi.mode == 0
        assert spi.max_speed_hz == 40_000_000

    def test_spi_defaults_applied(self, valid_config):
        del valid_config["spi"]["mode"]
        del valid_config["spi"]["max_speed_hz"]
        display = Waveshare147ST7789Display(valid_config)
        spi = mock_spidev.SpiDev.return_value
        assert spi.mode == 0
        assert spi.max_speed_hz == 10_000_000

    def test_backlight_enabled(self, display):
        mock_gpio.output.assert_any_call(18, mock_gpio.HIGH)

    def test_framebuffer_allocated(self, display):
        expected_size = 172 * 320 * 2
        assert len(display._framebuffer) == expected_size


# ------------------------------------------------------------------
# Drawing helpers
# ------------------------------------------------------------------


class TestDrawingHelpers:
    def test_rgb565_white(self):
        result = Waveshare147ST7789Display._rgb565(255, 255, 255)
        assert result == b"\xff\xff"

    def test_rgb565_black(self):
        result = Waveshare147ST7789Display._rgb565(0, 0, 0)
        assert result == b"\x00\x00"

    def test_rgb565_red(self):
        result = Waveshare147ST7789Display._rgb565(255, 0, 0)
        # Red: (0xF8 << 8) | 0 | 0 = 0xF800
        assert result == b"\xf8\x00"

    def test_text_width_single_char(self):
        assert Waveshare147ST7789Display._text_width("A", scale=1) == 5

    def test_text_width_multiple_chars(self):
        # 3 chars: 3 * 6 * 1 - 1 = 17
        assert Waveshare147ST7789Display._text_width("ABC", scale=1) == 17

    def test_text_width_with_scale(self):
        # 2 chars: 2 * 6 * 2 - 2 = 22
        assert Waveshare147ST7789Display._text_width("AB", scale=2) == 22

    def test_draw_pixel_out_of_bounds_ignored(self, display):
        # Should not raise
        display._draw_pixel(-1, 0, b"\xff\xff")
        display._draw_pixel(0, -1, b"\xff\xff")
        display._draw_pixel(172, 0, b"\xff\xff")
        display._draw_pixel(0, 320, b"\xff\xff")

    def test_draw_pixel_in_bounds_writes_framebuffer(self, display):
        color = b"\xab\xcd"
        display._draw_pixel(10, 20, color)
        idx = (20 * 172 + 10) * 2
        assert display._framebuffer[idx:idx + 2] == color

    def test_clear_framebuffer(self, display):
        black = Waveshare147ST7789Display._rgb565(0, 0, 0)
        white = Waveshare147ST7789Display._rgb565(255, 255, 255)
        display._clear_framebuffer(white)
        assert display._framebuffer[0:2] == white
        assert display._framebuffer[-2:] == white
        display._clear_framebuffer(black)
        assert display._framebuffer[0:2] == black


# ------------------------------------------------------------------
# Rendering
# ------------------------------------------------------------------


class TestRender:
    def test_render_full_snapshot(self, display, full_snapshot):
        display.render(full_snapshot)
        spi = mock_spidev.SpiDev.return_value
        # Framebuffer should be written via _write_data -> spi.writebytes
        assert spi.writebytes.call_count > 0

    def test_render_with_missing_values(self, display):
        snapshot = {
            "ts": time.time(),
            "device_name": "test_device",
            "values": {},
        }
        display.render(snapshot)
        spi = mock_spidev.SpiDev.return_value
        assert spi.writebytes.call_count > 0

    def test_render_with_partial_values(self, display):
        snapshot = {
            "ts": time.time(),
            "device_name": "test_device",
            "values": {
                "water_temperature": 22.0,
            },
        }
        display.render(snapshot)
        spi = mock_spidev.SpiDev.return_value
        assert spi.writebytes.call_count > 0

    def test_render_respects_refresh_period(self, valid_config):
        valid_config["refresh_period"] = 60
        display = Waveshare147ST7789Display(valid_config)
        spi = mock_spidev.SpiDev.return_value
        spi.reset_mock()

        snapshot = {
            "ts": time.time(),
            "device_name": "test_device",
            "values": {"water_temperature": 22.0},
        }
        display.render(snapshot)  # First render should go through
        call_count_after_first = spi.writebytes.call_count

        display.render(snapshot)  # Second render should be skipped
        assert spi.writebytes.call_count == call_count_after_first

    def test_render_exception_does_not_propagate(self, display):
        bad_snapshot = {"not": "valid"}
        # Should not raise — the driver catches and logs
        display.render(bad_snapshot)


# ------------------------------------------------------------------
# Cleanup
# ------------------------------------------------------------------


class TestClose:
    def test_close_turns_off_backlight(self, display):
        mock_gpio.reset_mock()
        display.close()
        mock_gpio.output.assert_any_call(18, mock_gpio.LOW)

    def test_close_releases_spi(self, display):
        spi = mock_spidev.SpiDev.return_value
        display.close()
        spi.close.assert_called_once()

    def test_close_cleans_up_gpio(self, display):
        mock_gpio.reset_mock()
        display.close()
        mock_gpio.cleanup.assert_called_once_with([25, 27, 18])