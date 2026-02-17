"""
test_driver_kwargs_alignment.py

Verify that every registered sensor driver's ACCEPTED_KWARGS and
REQUIRED_KWARGS are consistent with its __init__ signature.
"""

import inspect
import sys
from unittest.mock import MagicMock

import pytest

# --- Mock hardware modules before importing drivers ---
mock_gpio = MagicMock()
mock_rpi = MagicMock()
mock_rpi.GPIO = mock_gpio
sys.modules.setdefault("RPi", mock_rpi)
sys.modules.setdefault("RPi.GPIO", mock_gpio)
sys.modules.setdefault("adafruit_dht", MagicMock())
sys.modules.setdefault("board", MagicMock())
sys.modules.setdefault("pigpio", MagicMock())
sys.modules.setdefault("smbus2", MagicMock())

from monitoring_service.inputs.sensors.factory import SensorFactory


@pytest.fixture
def registry():
    """Return the default sensor registry."""
    factory = SensorFactory(registry=None)
    return factory._registry


def _get_init_params(driver_class):
    """Return the set of keyword-only parameter names from __init__."""
    sig = inspect.signature(driver_class.__init__)
    return {
        name
        for name, param in sig.parameters.items()
        if name != "self"
        and param.kind in (param.KEYWORD_ONLY, param.POSITIONAL_OR_KEYWORD)
    }


def test_accepted_kwargs_are_valid_init_params(registry):
    """Every ACCEPTED_KWARGS entry must be a valid __init__ parameter."""
    for sensor_type, driver_class in registry.items():
        accepted = set(getattr(driver_class, "ACCEPTED_KWARGS", []))
        init_params = _get_init_params(driver_class)
        invalid = accepted - init_params
        assert not invalid, (
            f"{driver_class.__name__} ACCEPTED_KWARGS contains params "
            f"not in __init__: {sorted(invalid)}"
        )


def test_required_kwargs_subset_of_accepted(registry):
    """Every REQUIRED_KWARGS entry must also appear in ACCEPTED_KWARGS."""
    for sensor_type, driver_class in registry.items():
        required = set(getattr(driver_class, "REQUIRED_KWARGS", []))
        accepted = set(getattr(driver_class, "ACCEPTED_KWARGS", []))
        required_any_of = getattr(driver_class, "REQUIRED_ANY_OF", None)

        if required_any_of and not required:
            # For REQUIRED_ANY_OF drivers, check each group is in accepted
            for group in required_any_of:
                missing = group - accepted
                assert not missing, (
                    f"{driver_class.__name__} REQUIRED_ANY_OF group {group} "
                    f"contains params not in ACCEPTED_KWARGS: {sorted(missing)}"
                )
        elif required:
            missing = required - accepted
            assert not missing, (
                f"{driver_class.__name__} REQUIRED_KWARGS {sorted(required)} "
                f"not in ACCEPTED_KWARGS (missing: {sorted(missing)})"
            )


def test_coercers_target_accepted_kwargs(registry):
    """Every COERCERS key must be in ACCEPTED_KWARGS."""
    for sensor_type, driver_class in registry.items():
        coercers = set(getattr(driver_class, "COERCERS", {}).keys())
        accepted = set(getattr(driver_class, "ACCEPTED_KWARGS", []))
        invalid = coercers - accepted
        assert not invalid, (
            f"{driver_class.__name__} COERCERS references params "
            f"not in ACCEPTED_KWARGS: {sorted(invalid)}"
        )