"""
conftest.py

Session-scoped hardware module stubs for unit tests.

Hardware packages are either unavailable on macOS (spidev, RPi.GPIO) or broken
in Python 3.13 (Adafruit Blinka's board.py imports pkg_resources, which is
absent from modern setuptools).  All stubs are registered via
sys.modules.setdefault so they are only applied when the real package is not
already present — this preserves real installed packages such as pigpio, which
test_water_flow_sensor.py requires to be the genuine module.

Stubs are applied at module level here (not inside a fixture) so they are in
place before pytest imports any test module.  This prevents test files from
clobbering each other's module-level bindings: Python caches imported modules
in sys.modules, and the first import wins.  With conftest running first, every
import that happens during test collection uses these stubs consistently.

Shared mock objects (RPi.GPIO, spidev, adafruit_ssd1306) are purposely
exposed via sys.modules so that test files which need to make assertions on
GPIO or SPI calls can read them back with sys.modules["RPi.GPIO"] and be
guaranteed to reference the exact same object the driver module captured.
"""

import sys
import types
from unittest.mock import MagicMock


# ── adafruit_dht ─────────────────────────────────────────────────────────────
# Provides a DHT22 constructor that returns a device with concrete float
# temperature / humidity properties so DHT22Sensor.read() works correctly.
# Tests that need to override behaviour (e.g. force None) can monkeypatch the
# _FakeDHT22Device class directly — monkeypatch restores it after each test.

class _FakeDHT22Device:
    def __init__(self, pin):
        self._pin = pin

    @property
    def temperature(self):
        return 24.3

    @property
    def humidity(self):
        return 58.7

    def exit(self):
        pass


class _FakeAdafruitDHT(types.ModuleType):
    def __init__(self):
        super().__init__("adafruit_dht")

    def DHT22(self, pin):
        return _FakeDHT22Device(pin)


# ── RPi / spidev ─────────────────────────────────────────────────────────────
# Create a linked RPi.GPIO pair so both import paths resolve to the same object.
# test_waveshare_147_st7789.py reads _mock_gpio back via sys.modules["RPi.GPIO"]
# to ensure it references the exact same object the waveshare driver captured.

_mock_gpio = MagicMock()
_mock_rpi = MagicMock()
_mock_rpi.GPIO = _mock_gpio


# ── Apply stubs ───────────────────────────────────────────────────────────────

sys.modules.setdefault("board", MagicMock())           # broken Blinka on Py 3.13
sys.modules.setdefault("busio", MagicMock())
sys.modules.setdefault("adafruit_dht", _FakeAdafruitDHT())
sys.modules.setdefault("adafruit_ssd1306", MagicMock())
sys.modules.setdefault("tb_device_mqtt", MagicMock())
sys.modules.setdefault("spidev", MagicMock())
sys.modules.setdefault("RPi", _mock_rpi)
sys.modules.setdefault("RPi.GPIO", _mock_gpio)