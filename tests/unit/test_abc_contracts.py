"""
test_abc_contracts.py

Tests that BaseSensor and BaseDisplay ABC contracts are correctly enforced
at instantiation time — i.e. omitting any required interface element raises
TypeError before the object is created.
"""

import pytest

from monitoring_service.inputs.sensors.base import BaseSensor
from monitoring_service.outputs.display.base import BaseDisplay


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_sensor_class(*, name=True, kind=True, units=True, read=True):
    """Return a concrete BaseSensor subclass, omitting properties as requested."""
    attrs = {}
    if name:
        attrs["name"] = property(lambda self: "test_sensor")
    if kind:
        attrs["kind"] = property(lambda self: "Temperature")
    if units:
        attrs["units"] = property(lambda self: "C")
    if read:
        attrs["read"] = lambda self: {"temperature": 20.0}
    return type("ConcreteTestSensor", (BaseSensor,), attrs)


def _make_display_class(*, render=True, close=True, render_startup=True):
    """Return a concrete BaseDisplay subclass, omitting methods as requested."""
    attrs = {}
    if render:
        attrs["render"] = lambda self, snapshot: None
    if render_startup:
        attrs["render_startup"] = lambda self, message: None
    if close:
        attrs["close"] = lambda self: None
    return type("ConcreteTestDisplay", (BaseDisplay,), attrs)


# ---------------------------------------------------------------------------
# BaseSensor contract tests
# ---------------------------------------------------------------------------

class TestBaseSensorContracts:
    """Verify BaseSensor raises TypeError when a required interface element is missing."""

    def test_complete_implementation_instantiates(self):
        cls = _make_sensor_class()
        cls()  # must not raise

    def test_missing_read_raises(self):
        cls = _make_sensor_class(read=False)
        with pytest.raises(TypeError):
            cls()

    def test_missing_name_raises(self):
        cls = _make_sensor_class(name=False)
        with pytest.raises(TypeError):
            cls()

    def test_missing_kind_raises(self):
        cls = _make_sensor_class(kind=False)
        with pytest.raises(TypeError):
            cls()

    def test_missing_units_raises(self):
        cls = _make_sensor_class(units=False)
        with pytest.raises(TypeError):
            cls()


# ---------------------------------------------------------------------------
# BaseDisplay contract tests
# ---------------------------------------------------------------------------

class TestBaseDisplayContracts:
    """Verify BaseDisplay raises TypeError when a required interface element is missing."""

    def test_complete_implementation_instantiates(self):
        cls = _make_display_class()
        cls({})  # must not raise

    def test_missing_render_raises(self):
        cls = _make_display_class(render=False)
        with pytest.raises(TypeError):
            cls({})

    def test_missing_close_raises(self):
        cls = _make_display_class(close=False)
        with pytest.raises(TypeError):
            cls({})

    def test_missing_render_startup_raises(self):
        cls = _make_display_class(render_startup=False)
        with pytest.raises(TypeError):
            cls({})