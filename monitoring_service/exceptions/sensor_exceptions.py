"""
sensors.py

Shared base exception classes for all sensor drivers.

Each driver module (dht22, ds18b20, water_flow, etc.) defines its own
sensor-specific exception names (e.g. DHT22ReadError) as thin subclasses of
these bases.  This lets callers catch at either level:

    # Driver-specific (precise):
    except DHT22ReadError: ...

    # Cross-sensor (broad):
    except SensorReadError: ...
"""


class SensorInitError(Exception):
    """Raised when a sensor cannot be initialised."""


class SensorReadError(Exception):
    """Raised when a sensor read fails."""


class SensorValueError(Exception):
    """Raised when a sensor receives or produces an invalid value."""


class SensorStopError(Exception):
    """Raised when a sensor cannot be cleanly stopped or released."""


class SensorDataOutOfRangeError(SensorReadError):
    """Raised when a sensor returns a value outside its configured range."""
