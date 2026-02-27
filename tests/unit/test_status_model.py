import time
import pytest
from monitoring_service.outputs.status_model import DisplayStatus


def test_from_snapshot_full():
    ts = int(time.time() * 1000)
    snapshot = {
        "ts": ts,
        "device_name": "test_tank",
        "values": {
            "water_temperature": 24.5,
            "air_temperature": 19.2,
            "air_humidity": 65.0,
            "water_flow": 1.3,
        },
    }
    status = DisplayStatus.from_snapshot(snapshot)

    assert status.device_name == "test_tank"
    assert status.water_temperature == 24.5
    assert status.air_temperature == 19.2
    assert status.air_humidity == 65.0
    assert status.water_flow == 1.3
    assert status.timestamp_utc == ts


def test_from_snapshot_empty_values_returns_none_fields():
    snapshot = {"ts": 1000, "device_name": "test", "values": {}}
    status = DisplayStatus.from_snapshot(snapshot)

    assert status.water_temperature is None
    assert status.air_temperature is None
    assert status.air_humidity is None
    assert status.water_flow is None


def test_from_snapshot_missing_device_name_defaults_to_unknown():
    snapshot = {"ts": 1000, "values": {}}
    status = DisplayStatus.from_snapshot(snapshot)
    assert status.device_name == "unknown"


def test_from_snapshot_missing_ts_falls_back_to_current_time():
    snapshot = {"device_name": "test", "values": {}}
    before = time.time()
    status = DisplayStatus.from_snapshot(snapshot)
    after = time.time()
    assert before <= status.timestamp_utc <= after


def test_from_snapshot_partial_values():
    snapshot = {
        "ts": 1000,
        "device_name": "test",
        "values": {"water_temperature": 22.0},
    }
    status = DisplayStatus.from_snapshot(snapshot)
    assert status.water_temperature == 22.0
    assert status.air_temperature is None
    assert status.air_humidity is None
    assert status.water_flow is None


def test_display_status_is_frozen():
    snapshot = {"ts": 1000, "device_name": "test", "values": {}}
    status = DisplayStatus.from_snapshot(snapshot)
    with pytest.raises(Exception):
        status.device_name = "changed"