"""
config_exceptions.py

Unified exception hierarchy for all configuration-related errors.

All exceptions here share a common base (ConfigurationError) so callers
can either catch broadly:

    except ConfigurationError: ...

or precisely:

    except MissingEnvironmentVarError: ...
"""


class ConfigurationError(Exception):
    """Base class for all configuration-related errors."""


class MissingEnvironmentVarError(ConfigurationError):
    """Raised when a required environment variable is not set."""


class InvalidConfigValueError(ConfigurationError):
    """Raised when a config value fails validation."""


class MissingConfigKeyError(ConfigurationError):
    """Raised when a required key is absent from the config file."""


class ConfigFileNotFoundError(ConfigurationError, FileNotFoundError):
    """Raised when the configuration file cannot be located or read."""