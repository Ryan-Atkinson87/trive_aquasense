"""
output_manager.py

Manages output devices such as displays. Responsible for fanning out
telemetry snapshots to outputs while isolating failures so outputs can
never crash the agent.
"""

import logging
from typing import Mapping, Any

from monitoring_service.outputs.display.base import BaseDisplay


class OutputManager:
    """
    Manages output devices such as displays.

    Responsible for fanning out telemetry snapshots to outputs while
    isolating failures so outputs can never crash the agent.
    """

    def __init__(
        self,
        outputs: list[BaseDisplay],
        logger: logging.Logger,
    ) -> None:
        self._outputs: list[BaseDisplay] = list(outputs)
        self._logger = logger

    def render(self, snapshot: Mapping[str, Any]) -> None:
        """
        Render a telemetry snapshot to all configured outputs.

        Args:
            snapshot: Telemetry snapshot containing ts, device_name, and values.
        """
        failed: list[BaseDisplay] = []

        for output in self._outputs:
            try:
                output.render(snapshot)
            except Exception:
                self._logger.warning(
                    "Output render failed, disabling output",
                    exc_info=True,
                )
                failed.append(output)

        for output in failed:
            self._outputs.remove(output)

    def close(self) -> None:
        """Close all managed outputs, releasing hardware resources."""
        for output in self._outputs:
            try:
                output.close()
            except Exception:
                self._logger.warning(
                    "Output close failed",
                    exc_info=True,
                )