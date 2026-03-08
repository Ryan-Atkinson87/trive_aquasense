"""
models.py

Shared data structures for the display subsystem. Defined here so that both
the display factory (which creates bundles) and OutputManager (which consumes
them) can import the types without depending on each other's implementation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from monitoring_service.outputs.display.base import BaseDisplay


@dataclass
class DisplayContent:
    """
    Pre-formatted content payload passed to display drivers for rendering.

    Content assembly (key extraction, value formatting) is the responsibility
    of OutputManager. Display drivers receive this payload and are responsible
    only for rendering it to their output device.
    """

    lines: list[str] = field(default_factory=list)
    timestamp_str: str = ""


@dataclass
class DisplayBundle:
    """
    Container object holding a display driver and its routing metadata.

    The factory builds DisplayBundle instances from configuration. OutputManager
    consumes them to route content to the appropriate driver.
    """

    driver: BaseDisplay
    system_screen: bool = False
    show_startup: bool = False