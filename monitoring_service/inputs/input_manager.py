"""
input_manager.py

Manages input devices such as sensors. Responsible for constructing sensor
bundles from configuration and collecting telemetry from all configured
sensors.
"""

import logging
from typing import Any

from monitoring_service.inputs.sensors.factory import SensorFactory
from monitoring_service.telemetry import TelemetryCollector


class InputManager:
    """
    Manages input devices such as sensors.

    Encapsulates sensor construction (via SensorFactory) and telemetry
    collection (via TelemetryCollector) behind a single interface.
    """

    def __init__(
        self,
        sensors_config: list[dict[str, Any]],
        logger: logging.Logger,
    ) -> None:
        self._logger = logger

        factory = SensorFactory()
        self._bundles = factory.build_all(sensors_config)
        self._collector = TelemetryCollector(bundles=self._bundles)

        if not self._bundles:
            self._logger.warning(
                "No sensors configured/built. Telemetry will be empty."
            )

    def collect(self) -> dict[str, Any]:
        """
        Collect telemetry from all configured sensors.

        Returns:
            Dict of canonical telemetry keys to their current values.
        """
        return self._collector.as_dict()