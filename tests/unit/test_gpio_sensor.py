"""
test_gpio_sensor.py

Tests the GPIOValueError raise paths in GPIOSensor._check_pin().

GPIOValueError is never visible to callers of DHT22Sensor or WaterFlowSensor
because those drivers wrap it as their own ValueError subclass.  These tests
exercise the raise conditions directly via a minimal concrete subclass.
"""

import pytest
from monitoring_service.inputs.sensors.gpio_sensor import GPIOSensor, GPIOValueError


class _ConcreteGPIO(GPIOSensor):
    """Minimal concrete subclass so we can instantiate GPIOSensor."""
    name = property(lambda self: "test")
    kind = property(lambda self: "test")
    units = property(lambda self: "test")

    def read(self):
        return {}


def _bare(pin=None):
    """Return an uninitialised sensor instance bypassing __init__."""
    sensor = _ConcreteGPIO.__new__(_ConcreteGPIO)
    if pin is not None:
        sensor.pin = pin
    return sensor


def test_gpio_value_error_missing_pin_attribute():
    sensor = _bare()  # no pin attribute at all
    with pytest.raises(GPIOValueError, match="missing required attribute 'pin'"):
        sensor._check_pin()


def test_gpio_value_error_non_int_pin_type():
    sensor = _bare(pin="17")  # string instead of int
    with pytest.raises(GPIOValueError, match="Invalid pin type"):
        sensor._check_pin()


def test_gpio_value_error_invalid_pin_number():
    sensor = _bare(pin=99999)  # out of range
    with pytest.raises(GPIOValueError, match="not a valid GPIO pin"):
        sensor._check_pin()


def test_gpio_check_pin_passes_for_valid_pin():
    from monitoring_service.inputs.sensors.constants import VALID_GPIO_PINS
    valid = next(iter(VALID_GPIO_PINS))
    sensor = _bare(pin=valid)
    sensor._check_pin()  # must not raise
