"""
output_manager.py

Manages output devices such as displays. Responsible for assembling display
content from telemetry snapshots and fanning it out to outputs while isolating
failures so outputs can never crash the agent.
"""

import logging
from datetime import datetime
from typing import Mapping, Any

from monitoring_service.outputs.display.models import DisplayBundle, DisplayContent


class OutputManager:
    """
    Manages output devices such as displays.

    Responsible for assembling pre-formatted content from telemetry snapshots
    and fanning it out to outputs, while isolating failures so outputs can
    never crash the agent.
    """

    def __init__(
        self,
        outputs: list[DisplayBundle],
        logger: logging.Logger,
    ) -> None:
        self._outputs: list[DisplayBundle] = list(outputs)
        self._logger = logger

    # --- Internals ---

    def _assemble_content(self, snapshot: Mapping[str, Any]) -> DisplayContent:
        """
        Assemble a generic display content payload from a telemetry snapshot.

        Formats known telemetry values into labelled strings and produces a
        human-readable timestamp. The resulting DisplayContent is passed to
        display drivers, which render it without knowledge of telemetry keys.

        Args:
            snapshot: Telemetry snapshot containing ts, device_name, and values.

        Returns:
            DisplayContent with pre-formatted lines and a timestamp string.
        """
        values = snapshot.get("values", {})
        device_name = snapshot.get("device_name", "")
        ts = snapshot.get("ts")

        lines: list[str] = []

        if device_name:
            lines.append(device_name)

        water_temperature = values.get("water_temperature")
        if water_temperature is not None:
            lines.append(f"WATER:{water_temperature:.1f}C")

        air_temperature = values.get("air_temperature")
        if air_temperature is not None:
            lines.append(f"AIR:{air_temperature:.1f}C")

        air_humidity = values.get("air_humidity")
        if air_humidity is not None:
            lines.append(f"HUMID:{air_humidity:.1f}%")

        water_flow = values.get("water_flow")
        if water_flow is not None:
            lines.append(f"FLOW:{water_flow:.1f}L/M")

        if ts:
            timestamp_str = datetime.fromtimestamp(ts / 1000).strftime("%H:%M %d/%m/%Y")
        else:
            timestamp_str = "--:-- --/--/----"

        return DisplayContent(lines=lines, timestamp_str=timestamp_str)

    # --- Public API ---

    def render(self, snapshot: Mapping[str, Any]) -> None:
        """
        Assemble display content from a snapshot and render it to all
        non-system-screen outputs.

        Args:
            snapshot: Telemetry snapshot containing ts, device_name, and values.
        """
        content = self._assemble_content(snapshot)
        failed: list[DisplayBundle] = []

        for bundle in self._outputs:
            if bundle.system_screen:
                continue
            try:
                bundle.driver.render(content)
            except Exception:
                self._logger.warning(
                    "Output render failed, disabling output",
                    exc_info=True,
                )
                failed.append(bundle)

        for bundle in failed:
            self._outputs.remove(bundle)

    def render_startup(self, message: str) -> None:
        """
        Render a bootstrap progress message to displays that opt in via show_startup.

        A display failure during startup is logged but does not remove the display
        from the active outputs list — startup rendering is best-effort.

        Args:
            message: Short status string (e.g. "Connecting...").
        """
        for bundle in self._outputs:
            if not bundle.show_startup:
                continue
            try:
                bundle.driver.render_startup(message)
            except Exception:
                self._logger.warning(
                    "Output render_startup failed",
                    exc_info=True,
                )

    def close(self) -> None:
        """Close all managed outputs, releasing hardware resources."""
        for bundle in self._outputs:
            try:
                bundle.driver.close()
            except Exception:
                self._logger.warning(
                    "Output close failed",
                    exc_info=True,
                )