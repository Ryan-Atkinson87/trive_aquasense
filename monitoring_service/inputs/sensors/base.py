"""
base.py

Defines the BaseSensor abstract class, which all sensor drivers must implement.
"""


from abc import ABC, abstractmethod
from typing import Mapping, Any


class BaseSensor(ABC):
    """
    Abstract base class for all sensor drivers.

    Concrete subclasses must implement:
      - name:  human-readable sensor model identifier
      - kind:  sensor category (e.g. "Temperature", "Flow")
      - units: unit string for the primary reading (e.g. "C", "l/min")
      - read(): returns raw sensor readings as a key-value mapping
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name identifying the sensor model."""

    @property
    @abstractmethod
    def kind(self) -> str:
        """Sensor category, e.g. 'Temperature' or 'Flow'."""

    @property
    @abstractmethod
    def units(self) -> str:
        """Unit string for the primary reading, e.g. 'C' or 'l/min'."""

    @abstractmethod
    def read(self) -> Mapping[str, Any]:
        """
        Return raw sensor readings as a mapping of key-value pairs.
        """
