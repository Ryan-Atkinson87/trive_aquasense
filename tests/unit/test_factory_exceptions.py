import pytest
from monitoring_service.exceptions.factory_exceptions import (
    FactoryError,
    UnknownSensorTypeError,
    InvalidSensorConfigError,
)


def test_factory_error_basic_message():
    err = FactoryError("something went wrong")
    assert str(err) == "something went wrong"


def test_factory_error_with_sensor_type_and_id():
    err = FactoryError("bad config", sensor_type="dht22", sensor_id="sensor_1")
    s = str(err)
    assert "sensor_type=dht22" in s
    assert "sensor_id=sensor_1" in s


def test_factory_error_with_sensor_type_only():
    err = FactoryError("bad config", sensor_type="ds18b20")
    s = str(err)
    assert "sensor_type=ds18b20" in s
    assert "sensor_id" not in s


def test_factory_error_with_sensor_id_only():
    err = FactoryError("bad config", sensor_id="my_sensor")
    s = str(err)
    assert "sensor_id=my_sensor" in s
    assert "sensor_type" not in s


def test_factory_error_stores_cause():
    cause = ValueError("root cause")
    err = FactoryError("wrapper", cause=cause)
    assert err.__cause__ is cause


def test_unknown_sensor_type_error_message():
    err = UnknownSensorTypeError("mystery_type", ["dht22", "ds18b20"])
    s = str(err)
    assert "mystery_type" in s
    assert "dht22" in s
    assert "ds18b20" in s


def test_unknown_sensor_type_error_is_factory_error():
    err = UnknownSensorTypeError("x", [])
    assert isinstance(err, FactoryError)


def test_unknown_sensor_type_empty_known_types_shows_empty_symbol():
    err = UnknownSensorTypeError("x", [])
    assert "∅" in str(err)


def test_invalid_sensor_config_error_is_factory_error():
    err = InvalidSensorConfigError("invalid pin", sensor_id="s1", sensor_type="dht22")
    assert isinstance(err, FactoryError)
    assert "s1" in str(err)
    assert "dht22" in str(err)


def test_invalid_sensor_config_error_stores_cause():
    cause = TypeError("bad type")
    err = InvalidSensorConfigError("msg", cause=cause)
    assert err.__cause__ is cause