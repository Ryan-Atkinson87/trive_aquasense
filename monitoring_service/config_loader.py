"""
config_loader.py

Load configuration from environment variables and a required JSON config file.
The loader validates the file against config_schema.json on load, then validates
required environment values, and exposes a merged configuration dictionary via
as_dict(). Startup fails if config.json cannot be located, fails schema validation,
or if required environment variables are missing.

Classes:
    ConfigLoader

Usage:
    loader = ConfigLoader(logger)
    config = loader.as_dict()
"""

from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Any, Dict, Optional

import jsonschema

from monitoring_service.exceptions.config_exceptions import (
    ConfigFileNotFoundError,
    InvalidConfigValueError,
    MissingConfigKeyError,
    MissingEnvironmentVarError,
)

ETC_CONFIG_PATH = Path("/etc/trive_aquasense/config.json")
DEFAULT_CONFIG_FILENAME = "config.json"
_SCHEMA_PATH = Path(__file__).parent / "config_schema.json"

with open(_SCHEMA_PATH) as _schema_file:
    _CONFIG_SCHEMA = json.load(_schema_file)


def _safe_log(logger, level: str, msg: str) -> None:
    """
    Log a message using the provided logger while safely handling missing or
    nonstandard logger implementations.
    """

    if logger is None:
        return
    log_method = getattr(logger, level.lower(), None)
    if callable(log_method):
        try:
            log_method(msg)
        except Exception:
            pass

def _load_json_config(path: Optional[Path], logger=None) -> Dict[str, Any]:
    """
    Load JSON configuration from the given file path. Raises on failure.
    """
    if not path:
        raise ConfigFileNotFoundError("ConfigLoader: config path was not resolved")
    try:
        with open(path, "r") as file:  # <- use builtins.open so tests can mock it
            return json.load(file)
    except Exception as e:
        _safe_log(logger, "error", f"ConfigLoader: failed reading {path}: {e}")
        raise


class ConfigLoader:
    """
    Load and validate configuration from environment variables and a JSON config file.

    The JSON file is validated against config_schema.json before any values are
    extracted. This guarantees that by the time any _get_* method runs, required
    fields are present and all types and value ranges are correct.

    Required environment variables:
        ACCESS_TOKEN
        THINGSBOARD_SERVER

    Required JSON keys:
      - poll_period (int ≥ 1)
      - device_name (str, non-empty)
      - mount_path (str, non-empty)
      - sensors (list, ≥ 1 entry, each with id/type/interval)

    Optional JSON keys (with defaults):
      - log_level (str, default "INFO")
      - log_max_bytes (int ≥ 1, default 5 MB)
      - log_backup_count (int ≥ 0, default 3)
      - displays (list)
    """

    def __init__(self, logger):
        """
        Initialize the loader, read environment variables, load and schema-validate
        the JSON config file, and extract configuration fields.

        Args:
            logger (Logger): Logger instance for diagnostic output.
        """

        self.logger = logger

        self.token = os.getenv("ACCESS_TOKEN")
        self.server = os.getenv("THINGSBOARD_SERVER")

        # Resolve and load config.json (hard fail if missing or unreadable)
        self.config_path = self._resolve_config_path()
        self.config = _load_json_config(self.config_path, self.logger)

        # Validate structure, types, and value ranges against the JSON schema
        self._validate_config_schema()

        # Validate required environment variables
        self._validate_or_raise()

        self.poll_period = self._get_poll_period()
        self.device_name = self._get_device_name()
        self.mount_path = self._get_mount_path()
        self.log_level = self._get_log_level()
        self.log_max_bytes = self._get_log_max_bytes()
        self.log_backup_count = self._get_log_backup_count()

    def as_dict(self) -> Dict[str, Any]:
        """
        Return the merged configuration dictionary with environment variables
        taking precedence over JSON values.
        """
        merged: Dict[str, Any] = {
            "token": self.token,
            "server": self.server,
            "poll_period": self.poll_period,
            "device_name": self.device_name,
            "mount_path": self.mount_path,
            "log_level": self.log_level,
            "log_max_bytes": self.log_max_bytes,
            "log_backup_count": self.log_backup_count,
        }

        for key, value in self.config.items():
            if key not in merged or merged[key] in (None, "", []):
                merged[key] = value

        _safe_log(self.logger, "info", f"ConfigLoader: keys loaded: {list(merged.keys())}")
        _safe_log(self.logger, "info",
                  f"ConfigLoader: sensors present: {'sensors' in merged and bool(merged.get('inputs/sensors'))}")
        _safe_log(
            self.logger,
            "info",
            f"ConfigLoader: displays present: {'displays' in merged and bool(merged.get('displays'))}",
        )

        return merged

    def _validate_config_schema(self) -> None:
        """
        Validate the loaded config against config_schema.json.

        Raises:
            MissingConfigKeyError: If a required field is absent.
            InvalidConfigValueError: If a field has the wrong type or an out-of-range value.
        """
        try:
            jsonschema.validate(instance=self.config, schema=_CONFIG_SCHEMA)
        except jsonschema.ValidationError as e:
            field = " → ".join(str(part) for part in e.absolute_path) or "root"
            if e.validator == "required":
                msg = f"Config schema validation failed: {e.message}"
                _safe_log(self.logger, "error", msg)
                raise MissingConfigKeyError(msg) from e
            msg = f"Config schema validation failed at '{field}': {e.message}"
            _safe_log(self.logger, "error", msg)
            raise InvalidConfigValueError(msg) from e

    def _validate_or_raise(self) -> None:
        """
        Validate that required environment variables are present.

        Raises:
            MissingEnvironmentVarError: If required environment variables are missing.
        """
        missing = []
        if not self.token:
            missing.append("ACCESS_TOKEN")
        if not self.server:
            missing.append("THINGSBOARD_SERVER")
        if missing:
            msg = f"Missing required environment variables: {', '.join(missing)}"
            _safe_log(self.logger, "error", msg)
            raise MissingEnvironmentVarError(msg)

    # --- Field accessors ---
    # Schema validation has already guaranteed presence, type, and value range for
    # required fields. These methods exist only to extract values and supply defaults
    # for optional fields.

    def _get_poll_period(self) -> int:
        return self.config["poll_period"]

    def _get_device_name(self) -> str:
        return self.config["device_name"]

    def _resolve_config_path(self) -> Path:
        env_path = os.getenv("CONFIG_PATH")
        if env_path:
            path = Path(env_path).expanduser().resolve()
            if path.is_file():
                self.logger.info(f"ConfigLoader: using config from CONFIG_PATH env var: {path}")
                return path
            raise ConfigFileNotFoundError(f"CONFIG_PATH set but file does not exist: {path}")

        if ETC_CONFIG_PATH.is_file():
            self.logger.info(f"ConfigLoader: using config from {ETC_CONFIG_PATH}")
            return ETC_CONFIG_PATH

        project_root = Path.cwd()
        local_path = project_root / DEFAULT_CONFIG_FILENAME
        if local_path.is_file():
            self.logger.warning(
                f"ConfigLoader: using local dev config at {local_path} (NOT /etc)"
            )
            return local_path

        raise ConfigFileNotFoundError(
            "ConfigLoader: no config.json found via CONFIG_PATH, /etc, or project directory"
        )

    def _get_mount_path(self) -> str:
        return self.config["mount_path"]

    def _get_log_level(self) -> str:
        return self.config.get("log_level", "INFO")

    def _get_log_max_bytes(self) -> int:
        return self.config.get("log_max_bytes", 5 * 1024 * 1024)

    def _get_log_backup_count(self) -> int:
        return self.config.get("log_backup_count", 3)
