import time

import pytest

from monitoring_service.outputs.display.waveshare_147_st7789 import (
    Waveshare147ST7789Display,
)

DISPLAY_CONFIG = {
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


@pytest.fixture()
def display():
    d = Waveshare147ST7789Display(DISPLAY_CONFIG)
    yield d
    d.close()


@pytest.mark.hardware
def test_waveshare_display_initializes_and_renders(display):
    """Verify that the display initialises and renders without raising."""
    snapshot = {
        "ts": time.time(),
        "device_name": "hw-test",
        "values": {
            "water_temperature": 24.5,
            "air_temperature": 19.2,
            "air_humidity": 45.0,
            "water_flow": 1.5,
        },
    }

    display.render(snapshot)
    time.sleep(2)


@pytest.mark.hardware
def test_waveshare_display_renders_missing_values(display):
    """Verify rendering with no telemetry values shows only device name."""
    snapshot = {
        "ts": time.time(),
        "device_name": "hw-test",
        "values": {},
    }

    display.render(snapshot)
    time.sleep(2)


@pytest.mark.hardware
def test_waveshare_display_renders_partial_values(display):
    """Verify rendering with partial telemetry values."""
    snapshot = {
        "ts": time.time(),
        "device_name": "hw-test",
        "values": {
            "water_temperature": 22.0,
        },
    }

    display.render(snapshot)
    time.sleep(2)


@pytest.mark.hardware
def test_waveshare_display_close():
    """Verify close() turns off backlight and releases resources."""
    d = Waveshare147ST7789Display(DISPLAY_CONFIG)
    snapshot = {
        "ts": time.time(),
        "device_name": "hw-test",
        "values": {"water_temperature": 22.0},
    }
    d.render(snapshot)
    time.sleep(1)

    d.close()
    # After close, backlight should be off (visual confirmation)
    time.sleep(1)