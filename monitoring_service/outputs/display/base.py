"""
base.py

Defines the BaseDisplay abstract class, which all display drivers must implement.
"""

from abc import ABC, abstractmethod
from typing import Mapping, Any
import time


class BaseDisplay(ABC):
    """
    Abstract base class for all display drivers.

    Display drivers consume already collected telemetry snapshots and render
    them to an output device. Displays do not own timing, polling, or data
    collection.
    """

    def __init__(self, config: Mapping[str, Any]) -> None:
        """
        Initialise the display with its configuration.

        Args:
            config: Display specific configuration mapping.
        """
        self._config = config
        self._refresh_period = int(config.get("refresh_period", 0))
        self._last_render_ts: float = 0.0
        self._show_startup: bool = bool(config.get("show_startup", False))

    @property
    def show_startup(self) -> bool:
        """Whether this display participates in bootstrap startup rendering."""
        return self._show_startup

    def _should_render(self) -> bool:
        """
        Determine whether enough time has passed to allow a render.

        Returns:
            True if rendering should proceed, False otherwise.
        """
        if self._refresh_period <= 0:
            return True

        now = time.time()
        if (now - self._last_render_ts) >= self._refresh_period:
            self._last_render_ts = now
            return True

        return False

    @abstractmethod
    def render(self, snapshot: Mapping[str, Any]) -> None:
        """
        Render a telemetry snapshot to the display.

        Args:
            snapshot: Telemetry snapshot containing ts, device_name, and values.
        """

    @abstractmethod
    def render_startup(self, message: str) -> None:
        """
        Render a bootstrap progress message to the display.

        Called by OutputManager during the service startup sequence for
        displays with show_startup=True. Drivers that have no useful startup
        view must implement this as a no-op.

        Args:
            message: Short status string to display (e.g. "Connecting...").
        """

    @abstractmethod
    def close(self) -> None:
        """
        Release any hardware resources acquired by this display.

        Drivers that hold no hardware resources must implement this as a no-op.
        This method is called by OutputManager during shutdown.
        """
