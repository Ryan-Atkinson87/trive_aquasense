"""
logging_display.py

Provides a logging based display implementation for development and testing.
"""

import logging
from typing import Mapping, Any

from monitoring_service.outputs.display.base import BaseDisplay
from monitoring_service.outputs.status_model import DisplayStatus


class LoggingDisplay(BaseDisplay):
    """
    Display implementation that logs selected telemetry values instead of
    rendering them to physical hardware.
    """

    def __init__(self, config: Mapping[str, Any]) -> None:
        """
        Initialise the logging display.

        Args:
            config: Display specific configuration mapping.
        """
        super().__init__(config)
        self._logger = logging.getLogger("display.logging")

    def render(self, snapshot: Mapping[str, Any]) -> None:
        """
        Log selected telemetry values from a snapshot.

        Args:
            snapshot: Telemetry snapshot containing ts, device_name, and values.
        """
        if not self._should_render():
            return

        try:
            status = DisplayStatus.from_snapshot(snapshot)

            self._logger.info(
                "Display update | water_temperature=%s | air_temperature=%s"
                " | air_humidity=%s | water_flow=%s",
                status.water_temperature,
                status.air_temperature,
                status.air_humidity,
                status.water_flow,
            )

        except Exception:
            self._logger.warning(
                "Failed to render snapshot on logging display",
                exc_info=True,
            )

    def render_startup(self, message: str) -> None:
        """Log a bootstrap progress message at INFO level."""
        self._logger.info("Startup: %s", message)

    def close(self) -> None:
        """No hardware resources to release."""
        pass