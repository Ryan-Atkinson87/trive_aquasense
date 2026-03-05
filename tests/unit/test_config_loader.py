import os
import json
from pathlib import Path
import pytest
from unittest.mock import patch, mock_open

from monitoring_service.config_loader import ConfigLoader
from monitoring_service.exceptions import (
    ConfigurationError,
    MissingEnvironmentVarError,
    InvalidConfigValueError,
    MissingConfigKeyError,
    ConfigFileNotFoundError,
)


class DummyLogger:
    """Minimal logger substitute for testing."""

    def __init__(self):
        self.messages = []

    def info(self, msg):
        self.messages.append(msg)

    def warning(self, msg):
        self.messages.append(msg)

    def error(self, msg):
        self.messages.append(msg)


# Minimal valid config used as the baseline across tests.
_VALID_CONFIG = {
    "poll_period": 10,
    "device_name": "TestDevice",
    "mount_path": "/",
    "log_level": "INFO",
    "sensors": [{"id": "sensor_01", "type": "ds18b20", "interval": 5}],
}

_VALID_CONFIG_JSON = json.dumps(_VALID_CONFIG)


def _config_json(**overrides):
    """Return a JSON string of _VALID_CONFIG with the given keys overridden or removed."""
    config = dict(_VALID_CONFIG)
    for key, value in overrides.items():
        if value is None:
            config.pop(key, None)
        else:
            config[key] = value
    return json.dumps(config)


# ----------------------------
# Valid configuration
# ----------------------------

@patch.dict(os.environ, {"ACCESS_TOKEN": "test_token", "THINGSBOARD_SERVER": "test_server"})
@patch("monitoring_service.config_loader.ConfigLoader._resolve_config_path")
@patch("builtins.open", new_callable=mock_open, read_data=_VALID_CONFIG_JSON)
def test_config_loader_valid(mock_file, mock_resolve_path):
    mock_resolve_path.return_value = Path("/fake/config.json")

    loader = ConfigLoader(DummyLogger())
    config = loader.as_dict()

    assert config["token"] == "test_token"
    assert config["server"] == "test_server"
    assert config["poll_period"] == 10
    assert config["device_name"] == "TestDevice"
    assert config["mount_path"] == "/"
    assert config["log_level"] == "INFO"


# ----------------------------
# Missing environment variables
# ----------------------------

@patch.dict(os.environ, {}, clear=True)
@patch("monitoring_service.config_loader.ConfigLoader._resolve_config_path")
@patch("builtins.open", new_callable=mock_open, read_data=_VALID_CONFIG_JSON)
def test_missing_env_vars_raises_error(mock_file, mock_resolve_path):
    mock_resolve_path.return_value = Path("/fake/config.json")

    with pytest.raises(MissingEnvironmentVarError):
        ConfigLoader(DummyLogger())


# ----------------------------
# Missing config file entirely
# ----------------------------

@patch.dict(os.environ, {"ACCESS_TOKEN": "test_token", "THINGSBOARD_SERVER": "test_server"})
@patch("monitoring_service.config_loader.ConfigLoader._resolve_config_path")
def test_missing_config_file_raises_filenotfound(mock_resolve_path):
    mock_resolve_path.side_effect = FileNotFoundError("No config found")

    with pytest.raises(FileNotFoundError):
        ConfigLoader(DummyLogger())


# ----------------------------
# Top-level required fields
# ----------------------------

@patch.dict(os.environ, {"ACCESS_TOKEN": "test_token", "THINGSBOARD_SERVER": "test_server"})
@patch("monitoring_service.config_loader.ConfigLoader._resolve_config_path")
@patch("builtins.open", new_callable=mock_open,
       read_data=_config_json(poll_period=None))
def test_missing_poll_period_raises_key_error(mock_file, mock_resolve_path):
    mock_resolve_path.return_value = Path("/fake/config.json")
    with pytest.raises(MissingConfigKeyError):
        ConfigLoader(DummyLogger())


@patch.dict(os.environ, {"ACCESS_TOKEN": "test_token", "THINGSBOARD_SERVER": "test_server"})
@patch("monitoring_service.config_loader.ConfigLoader._resolve_config_path")
@patch("builtins.open", new_callable=mock_open,
       read_data=_config_json(device_name=None))
def test_missing_device_name_raises_key_error(mock_file, mock_resolve_path):
    mock_resolve_path.return_value = Path("/fake/config.json")
    with pytest.raises(MissingConfigKeyError):
        ConfigLoader(DummyLogger())


@patch.dict(os.environ, {"ACCESS_TOKEN": "test_token", "THINGSBOARD_SERVER": "test_server"})
@patch("monitoring_service.config_loader.ConfigLoader._resolve_config_path")
@patch("builtins.open", new_callable=mock_open,
       read_data=_config_json(mount_path=None))
def test_missing_mount_path_raises_key_error(mock_file, mock_resolve_path):
    mock_resolve_path.return_value = Path("/fake/config.json")
    with pytest.raises(MissingConfigKeyError):
        ConfigLoader(DummyLogger())


@patch.dict(os.environ, {"ACCESS_TOKEN": "test_token", "THINGSBOARD_SERVER": "test_server"})
@patch("monitoring_service.config_loader.ConfigLoader._resolve_config_path")
@patch("builtins.open", new_callable=mock_open,
       read_data=_config_json(sensors=None))
def test_missing_sensors_raises_key_error(mock_file, mock_resolve_path):
    mock_resolve_path.return_value = Path("/fake/config.json")
    with pytest.raises(MissingConfigKeyError):
        ConfigLoader(DummyLogger())


# ----------------------------
# Top-level value validation
# ----------------------------

@patch.dict(os.environ, {"ACCESS_TOKEN": "test_token", "THINGSBOARD_SERVER": "test_server"})
@patch("monitoring_service.config_loader.ConfigLoader._resolve_config_path")
@patch("builtins.open", new_callable=mock_open,
       read_data=_config_json(poll_period="not_an_int"))
def test_invalid_poll_period_type_raises_value_error(mock_file, mock_resolve_path):
    mock_resolve_path.return_value = Path("/fake/config.json")
    with pytest.raises(InvalidConfigValueError):
        ConfigLoader(DummyLogger())


@patch.dict(os.environ, {"ACCESS_TOKEN": "test_token", "THINGSBOARD_SERVER": "test_server"})
@patch("monitoring_service.config_loader.ConfigLoader._resolve_config_path")
@patch("builtins.open", new_callable=mock_open,
       read_data=_config_json(poll_period=0))
def test_poll_period_below_minimum_raises_value_error(mock_file, mock_resolve_path):
    mock_resolve_path.return_value = Path("/fake/config.json")
    with pytest.raises(InvalidConfigValueError):
        ConfigLoader(DummyLogger())


@patch.dict(os.environ, {"ACCESS_TOKEN": "test_token", "THINGSBOARD_SERVER": "test_server"})
@patch("monitoring_service.config_loader.ConfigLoader._resolve_config_path")
@patch("builtins.open", new_callable=mock_open,
       read_data=_config_json(log_level="VERBOSE"))
def test_invalid_log_level_raises_value_error(mock_file, mock_resolve_path):
    mock_resolve_path.return_value = Path("/fake/config.json")
    with pytest.raises(InvalidConfigValueError):
        ConfigLoader(DummyLogger())


@patch.dict(os.environ, {"ACCESS_TOKEN": "test_token", "THINGSBOARD_SERVER": "test_server"})
@patch("monitoring_service.config_loader.ConfigLoader._resolve_config_path")
@patch("builtins.open", new_callable=mock_open,
       read_data=_config_json(sensors=[]))
def test_empty_sensors_array_raises_value_error(mock_file, mock_resolve_path):
    mock_resolve_path.return_value = Path("/fake/config.json")
    with pytest.raises(InvalidConfigValueError):
        ConfigLoader(DummyLogger())


# ----------------------------
# Sensor entry validation
# ----------------------------

@patch.dict(os.environ, {"ACCESS_TOKEN": "test_token", "THINGSBOARD_SERVER": "test_server"})
@patch("monitoring_service.config_loader.ConfigLoader._resolve_config_path")
@patch("builtins.open", new_callable=mock_open,
       read_data=_config_json(sensors=[{"type": "ds18b20", "interval": 5}]))
def test_sensor_missing_id_raises_key_error(mock_file, mock_resolve_path):
    mock_resolve_path.return_value = Path("/fake/config.json")
    with pytest.raises(MissingConfigKeyError):
        ConfigLoader(DummyLogger())


@patch.dict(os.environ, {"ACCESS_TOKEN": "test_token", "THINGSBOARD_SERVER": "test_server"})
@patch("monitoring_service.config_loader.ConfigLoader._resolve_config_path")
@patch("builtins.open", new_callable=mock_open,
       read_data=_config_json(sensors=[{"id": "sensor_01", "interval": 5}]))
def test_sensor_missing_type_raises_key_error(mock_file, mock_resolve_path):
    mock_resolve_path.return_value = Path("/fake/config.json")
    with pytest.raises(MissingConfigKeyError):
        ConfigLoader(DummyLogger())


@patch.dict(os.environ, {"ACCESS_TOKEN": "test_token", "THINGSBOARD_SERVER": "test_server"})
@patch("monitoring_service.config_loader.ConfigLoader._resolve_config_path")
@patch("builtins.open", new_callable=mock_open,
       read_data=_config_json(sensors=[{"id": "sensor_01", "type": "ds18b20"}]))
def test_sensor_missing_interval_raises_key_error(mock_file, mock_resolve_path):
    mock_resolve_path.return_value = Path("/fake/config.json")
    with pytest.raises(MissingConfigKeyError):
        ConfigLoader(DummyLogger())


@patch.dict(os.environ, {"ACCESS_TOKEN": "test_token", "THINGSBOARD_SERVER": "test_server"})
@patch("monitoring_service.config_loader.ConfigLoader._resolve_config_path")
@patch("builtins.open", new_callable=mock_open,
       read_data=_config_json(sensors=[{"id": "sensor_01", "type": "ds18b20", "interval": 0}]))
def test_sensor_interval_below_minimum_raises_value_error(mock_file, mock_resolve_path):
    mock_resolve_path.return_value = Path("/fake/config.json")
    with pytest.raises(InvalidConfigValueError):
        ConfigLoader(DummyLogger())