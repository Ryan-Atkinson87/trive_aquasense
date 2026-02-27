"""
test_sensor_exceptions.py

Verify the sensor exception hierarchy introduced by issue #62.

Each driver-specific exception must be a subclass of the appropriate shared
base so callers can catch at either the driver level (precise) or the sensor
level (broad).
"""

import pytest
from monitoring_service.exceptions.sensors import (
    SensorInitError,
    SensorReadError,
    SensorValueError,
    SensorStopError,
    SensorDataOutOfRangeError,
)
from monitoring_service.inputs.sensors.gpio_sensor import GPIOValueError
from monitoring_service.inputs.sensors.dht22 import (
    DHT22InitError,
    DHT22ReadError,
    DHT22ValueError,
)
from monitoring_service.inputs.sensors.ds18b20 import DS18B20ReadError
from monitoring_service.inputs.sensors.water_flow import (
    WaterFlowInitError,
    WaterFlowReadError,
    WaterFlowStopError,
    WaterFlowValueError,
)


# ── Base classes are Exception subclasses ─────────────────────────────────────

def test_sensor_init_error_is_exception():
    assert issubclass(SensorInitError, Exception)


def test_sensor_read_error_is_exception():
    assert issubclass(SensorReadError, Exception)


def test_sensor_value_error_is_exception():
    assert issubclass(SensorValueError, Exception)


def test_sensor_stop_error_is_exception():
    assert issubclass(SensorStopError, Exception)


def test_sensor_data_out_of_range_error_is_sensor_read_error():
    assert issubclass(SensorDataOutOfRangeError, SensorReadError)


# ── gpio_sensor ───────────────────────────────────────────────────────────────

def test_gpio_value_error_is_sensor_value_error():
    assert issubclass(GPIOValueError, SensorValueError)


# ── dht22 ─────────────────────────────────────────────────────────────────────

def test_dht22_init_error_is_sensor_init_error():
    assert issubclass(DHT22InitError, SensorInitError)


def test_dht22_read_error_is_sensor_read_error():
    assert issubclass(DHT22ReadError, SensorReadError)


def test_dht22_value_error_is_sensor_value_error():
    assert issubclass(DHT22ValueError, SensorValueError)


# ── ds18b20 ───────────────────────────────────────────────────────────────────

def test_ds18b20_read_error_is_sensor_read_error():
    assert issubclass(DS18B20ReadError, SensorReadError)


# ── water_flow ────────────────────────────────────────────────────────────────

def test_water_flow_init_error_is_sensor_init_error():
    assert issubclass(WaterFlowInitError, SensorInitError)


def test_water_flow_read_error_is_sensor_read_error():
    assert issubclass(WaterFlowReadError, SensorReadError)


def test_water_flow_value_error_is_sensor_value_error():
    assert issubclass(WaterFlowValueError, SensorValueError)


def test_water_flow_stop_error_is_sensor_stop_error():
    assert issubclass(WaterFlowStopError, SensorStopError)


# ── Cross-sensor catch ────────────────────────────────────────────────────────

def test_dht22_read_error_caught_as_sensor_read_error():
    with pytest.raises(SensorReadError):
        raise DHT22ReadError("test")


def test_ds18b20_read_error_caught_as_sensor_read_error():
    with pytest.raises(SensorReadError):
        raise DS18B20ReadError("test")


def test_water_flow_init_error_caught_as_sensor_init_error():
    with pytest.raises(SensorInitError):
        raise WaterFlowInitError("test")