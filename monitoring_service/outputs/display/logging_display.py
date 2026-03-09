"""
logging_display.py

Provides a logging based display implementation for development and testing.
"""

import logging
from typing import Mapping, Any

from monitoring_service.outputs.display.base import BaseDisplay
from monitoring_service.outputs.display.models import DisplayContent


class LoggingDisplay(BaseDisplay):
    """
    Display implementation that logs pre-formatted content lines instead of
    rendering them to physical hardware.
    """

    # --- Properties ---

    def __init__(self, config: Mapping[str, Any]) -> None:
        """
        Initialise the logging display.

        Args:
            config: Display specific configuration mapping.
        """
        super().__init__(config)
        self._logger = logging.getLogger("display.logging")

    # --- Public API ---

    def render(self, content: DisplayContent) -> None:
        """
        Log pre-formatted content lines.

        Args:
            content: Pre-formatted content payload from OutputManager.
        """
        if not self._should_render():
            return

        try:
            self._logger.info(
                "Display update | %s | ts=%s",
                " | ".join(content.lines),
                content.timestamp_str,
            )

        except Exception:
            self._logger.warning(
                "Failed to render content on logging display",
                exc_info=True,
            )

    def render_startup(self, message: str) -> None:
        """Log a bootstrap progress message at INFO level."""
        self._logger.info("Startup: %s", message)

    def close(self) -> None:
        """No hardware resources to release."""
        pass