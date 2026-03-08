"""
models.py

Shared data structures for the sensor subsystem. Defined here so that both
the sensor factory (which creates bundles) and the telemetry collector (which
consumes them) can import the type without either depending on the other's
implementation module.
"""

from typing import Optional
from dataclasses import dataclass, field
from monitoring_service.inputs.sensors.base import BaseSensor


@dataclass
class SensorBundle:
    """
    Container object holding a sensor driver and its associated metadata.

    A SensorBundle combines the constructed driver instance with configuration
    used during telemetry processing, such as key mapping, calibration, smoothing,
    range limits, and read interval.
    """
    driver: BaseSensor
    keys: dict[str, str] = field(default_factory=dict)
    calibration: dict[str, dict[str,float]] = field(default_factory=dict)
    ranges: dict[str, dict[str,int]] = field(default_factory=dict)
    smoothing: dict[str, int] = field(default_factory=dict)
    interval: Optional[int] = None
    full_id: Optional[str] = None
    precision: dict[str, int] = field(default_factory=dict)
    max_retries: int = 0
    retry_base_delay: float = 0.5