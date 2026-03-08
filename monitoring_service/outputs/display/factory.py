"""
factory.py

Provides the DisplayFactory class for constructing display instances from
configuration.
"""

import logging
from typing import List, Mapping, Any

from monitoring_service.outputs.display.base import BaseDisplay
from monitoring_service.outputs.display.models import DisplayBundle
from monitoring_service.outputs.display.logging_display import LoggingDisplay
from monitoring_service.outputs.display.ssd1306_i2c import SSD1306I2CDisplay
from monitoring_service.outputs.display.waveshare_147_st7789 import Waveshare147ST7789Display


class DisplayFactory:
    """
    Construct display drivers from configuration and return DisplayBundle objects.

    The factory maintains a registry mapping display type strings to driver
    classes, and instantiates drivers from configuration. The factory is
    responsible for injecting role metadata (system_screen, show_startup)
    into the resulting bundles so that OutputManager can route content
    without inspecting driver internals.
    """

    def __init__(self, registry: dict[str, type[BaseDisplay]] | None = None) -> None:
        if registry is None:
            self._registry: dict[str, type[BaseDisplay]] = {
                "logging": LoggingDisplay,
                "ssd1306_i2c": SSD1306I2CDisplay,
                "waveshare_147_st7789": Waveshare147ST7789Display,
            }
        else:
            self._registry = dict(registry)

    def register(self, display_type: str, driver_class: type[BaseDisplay]) -> None:
        """
        Register or override a display driver class for a given display type.

        Args:
            display_type: Display type identifier used in configuration.
            driver_class: Driver class implementing the display.
        """
        if not isinstance(display_type, str) or not display_type.strip():
            raise ValueError("display_type must be a non-empty string")
        if not issubclass(driver_class, BaseDisplay):
            raise ValueError("driver_class must be a subclass of BaseDisplay")
        self._registry[display_type.strip().lower()] = driver_class

    def build(self, display_config: Mapping[str, Any]) -> DisplayBundle:
        """
        Build a single DisplayBundle from a display configuration dictionary.

        Args:
            display_config: Display configuration mapping.

        Returns:
            DisplayBundle: A fully constructed display bundle.

        Raises:
            ValueError: If the config is missing 'type' or the type is unknown.
            Exception: If the driver raises during initialisation.
        """
        display_type = display_config.get("type")
        if not display_type:
            raise ValueError("Display config missing 'type'")

        driver_class = self._registry.get(display_type)
        if driver_class is None:
            raise ValueError(f"Unknown display type '{display_type}'")

        driver = driver_class(display_config)
        return DisplayBundle(
            driver=driver,
            system_screen=driver.system_screen,
            show_startup=driver.show_startup,
        )

    def build_all(
        self,
        displays_config: list[Mapping[str, Any]],
        logger: logging.Logger,
        version: str = "",
    ) -> list[DisplayBundle]:
        """
        Build display bundles from a list of display configurations.

        Each display configuration is processed independently. Displays that
        fail validation or construction are logged and skipped.

        Args:
            displays_config: List of display configuration mappings.
            logger: Logger instance.
            version: Service version string injected into system-screen displays
                as the ``_version_header`` config key (e.g. "Aquasense v2.6.0").

        Returns:
            List of successfully initialised DisplayBundle instances.
        """
        bundles: list[DisplayBundle] = []

        if not displays_config:
            logger.info("No displays configured.")
            return bundles

        for index, display_config in enumerate(displays_config):
            if display_config.get("system_screen") and version:
                display_config = dict(display_config, _version_header=f"Aquasense v{version}")
            if not display_config.get("enabled", False):
                continue

            display_type = display_config.get("type")
            if not display_type:
                logger.warning(
                    "Display config at index %s missing type, skipping",
                    index,
                )
                continue

            if display_type not in self._registry:
                logger.warning(
                    "Unknown display type '%s', skipping",
                    display_type,
                )
                continue

            try:
                bundle = self.build(display_config)
                bundles.append(bundle)
                logger.info(
                    "Initialised display type '%s'",
                    display_type,
                )
            except Exception:
                logger.warning(
                    "Failed to initialise display type '%s'",
                    display_type,
                    exc_info=True,
                )

        return bundles