import pytest
from unittest.mock import patch, mock_open
from monitoring_service.inputs.sensors.ds18b20 import DS18B20Sensor, DS18B20ReadError


def test_init_with_id_only():
    sensor = DS18B20Sensor(id="28-abc123")
    assert sensor.device_file == "/sys/bus/w1/devices/28-abc123/w1_slave"
    assert sensor.sensor_id == "28-abc123"


def test_init_with_file_path():
    with patch("os.path.isfile", return_value=True):
        sensor = DS18B20Sensor(path="/sys/bus/w1/devices/28-abc123/w1_slave")
    assert sensor.device_file == "/sys/bus/w1/devices/28-abc123/w1_slave"


def test_init_with_dir_path_and_id():
    with patch("os.path.isfile", return_value=False):
        sensor = DS18B20Sensor(id="28-abc123", path="/custom/w1/devices")
    assert sensor.device_file == "/custom/w1/devices/28-abc123/w1_slave"


def test_init_with_dir_path_no_id():
    with patch("os.path.isfile", return_value=False):
        sensor = DS18B20Sensor(path="/custom/w1/devices")
    assert sensor.device_file is None


def test_read_success():
    sensor = DS18B20Sensor(id="28-abc123")
    file_data = "5e 01 4b 46 7f ff 0c 10 1c : crc=1c YES\n5e 01 4b 46 7f ff 0c 10 1c t=22500\n"
    with patch("builtins.open", mock_open(read_data=file_data)):
        result = sensor.read()
    assert result == {"temperature": 22.5}


def test_read_crc_failure_raises():
    sensor = DS18B20Sensor(id="28-abc123")
    file_data = "5e 01 4b 46 7f ff 0c 10 1c : crc=1c NO\n5e 01 4b 46 7f ff 0c 10 1c t=22500\n"
    with patch("builtins.open", mock_open(read_data=file_data)):
        with pytest.raises(DS18B20ReadError, match="CRC"):
            sensor.read()


def test_read_missing_t_raises():
    sensor = DS18B20Sensor(id="28-abc123")
    file_data = "crc=1c YES\nno temp here\n"
    with patch("builtins.open", mock_open(read_data=file_data)):
        with pytest.raises(DS18B20ReadError, match="not found"):
            sensor.read()


def test_read_malformed_value_raises():
    sensor = DS18B20Sensor(id="28-abc123")
    file_data = "crc=1c YES\nt=notanumber\n"
    with patch("builtins.open", mock_open(read_data=file_data)):
        with pytest.raises(DS18B20ReadError, match="Malformed"):
            sensor.read()


def test_discover_no_candidates_raises():
    with patch("os.path.isfile", return_value=False):
        sensor = DS18B20Sensor(path="/custom/w1/devices")
    with patch("glob.glob", return_value=[]):
        with pytest.raises(DS18B20ReadError, match="No DS18B20"):
            sensor._discover_device_file()


def test_discover_returns_first_candidate():
    with patch("os.path.isfile", return_value=False):
        sensor = DS18B20Sensor(path="/sys/bus/w1/devices")
    with patch("glob.glob", return_value=["/sys/bus/w1/devices/28-abc/w1_slave"]):
        result = sensor._get_device_file()
    assert result == "/sys/bus/w1/devices/28-abc/w1_slave"


def test_properties():
    sensor = DS18B20Sensor(id="28-abc123")
    assert sensor.name == "ds18b20"
    assert sensor.kind == "Temperature"
    assert sensor.units == "C"