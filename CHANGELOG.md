# Changelog
All notable changes to this project will be documented in this file.
Format: Keep a Changelog. Versioning: SemVer (MAJOR.MINOR.PATCH).

## [Unreleased]
### Added
- (Planned) SQLite queue for offline storage and retries.
- (Planned) HTTP implementation for sending data to places other than ThingsBoard.

## [v3.1.0] - 2026-03-09

### Added
- Retry and exponential back-off logic for sensor reads and MQTT publishes — configurable per sensor via `max_retries` and `retry_base_delay` in `config.json` (#120).
- Pre-start validation script (`pre_start_check.sh`) — runs via `ExecStartPre` in the systemd service. Verifies venv, `config.json`, and required env vars before the service starts; failures are written to the journal (#124).
- Pre-warm sensor reads on startup to absorb the DHT22 first-read failure before the main loop begins (#138).

### Changed
- Log output moved to `/var/log/trive_aquasense` — managed by systemd `LogsDirectory=` directive (#121).
- Display subsystem refactored to factory pattern with full driver isolation (#153).

## [v3.0.0] - 2026-03-07

### Added
- `software_version` attribute in `AttributesCollector.as_dict()` — reads from `__version__.py` and sends to ThingsBoard on startup (#151).
- JSON schema validation for `config.json` via `config_schema.json` — structural errors are caught at load time with clear developer-facing messages (#71).
- Architecture testing with `import-linter` — layer and independence contracts enforce the documented dependency direction at CI time; violations fail `lint-imports` (#130).
- Log rotation parameters (`max_bytes`, `backup_count`) exposed in `config.json` under `logging` — previously hardcoded in `logging_setup.py` (#133).
- OLED layout (column positions, row offsets) derived from per-display config dimensions rather than hardcoded constants (#133).
- `docs/CONFIGURATION.md`, `docs/DEPLOYMENT.md`, `docs/SENSORS.md`, `docs/ARCHITECTURE.md` — README split into focused documents; `README.md` is now a short project overview with links (#145).

### Changed
- `SensorBundle` moved from `factory.py` to `inputs/sensors/models.py` — removes cross-layer coupling between `TelemetryCollector` and the factory module (#142).
- Flat `monitoring_service/` layout reorganised into sub-packages (`config/`, `logging/`, `exceptions/` already existed) — improves navigability and aligns with module isolation goals (#119).
- `exceptions/sensors.py` renamed to `exceptions/sensor_exceptions.py` — aligns with the `*_exceptions.py` naming convention used by `config_exceptions.py` and `factory_exceptions.py` (#150).
- Production service file template (`trive_aquasense_example.service`) updated with production paths (`/opt/trive_aquasense`) and `EnvironmentFile=/etc/trive_aquasense/.env` directive.

## [v2.6.0] - 2026-03-02

### Added
- `show_startup` config field on `BaseDisplay` — opts a display into bootstrap progress messages rendered via `render_startup()` (#131).
- `render_startup()` abstract method on `BaseDisplay`; implemented on `SSD1306I2CDisplay`, `Waveshare147ST7789Display`, and `LoggingDisplay`. `OutputManager.render_startup()` fans messages out to opted-in displays (#132).
- Startup sequence in `main.py` renders "Aquasense v{version}", "Connecting...", and "Connected" to opted-in displays on boot (#132).
- `system_screen` config field on `BaseDisplay` — dedicates a display to a persistent system-status layout. Setting `system_screen: true` implicitly enables `show_startup`. Intended for the small OLED when a second display is connected (#132).
- System-screen mode for `SSD1306I2CDisplay`: fixed version header on row 1, rolling two-message log on rows 2–3. `render()` is a no-op in this mode (#132).
- Version header injected into system-screen displays via `build_displays()` factory — `__version__` is passed from `main.py` and merged into the display config as `_version_header`, keeping display drivers free of package-level imports (#132).
- `MonitoringAgent` emits `render_startup("Collected HH:MM:SS")` and `render_startup("Sent HH:MM:SS")` after each telemetry cycle, feeding the system-screen rolling log (#132).

## [v2.5.0] - 2026-02-27

### Added
- Shared sensor exception base hierarchy (`exceptions/sensors.py`): `SensorInitError`, `SensorReadError`, `SensorStopError`, `SensorValueError`. All sensor drivers now raise from this hierarchy (#62).
- Configuration error hierarchy (`exceptions/config_exceptions.py`): `ConfigError`, `ConfigFileNotFoundError`, `ConfigValidationError`, `MissingEnvVarError` (#69).
- `full_id` computed attribute on `SensorBundle` — combines sensor type and id at build time (e.g. `"ds18b20_28-abc"`). Used by `TelemetryCollector` for consistent bundle identification (#61, #129).
- Precision pipeline step in `TelemetryCollector` — `_apply_precision()` rounds telemetry values to configured decimal places as the final pipeline step (#128).
- `DEFAULT_PRECISION: dict[str, int]` class attribute on `WaterFlowSensor`, `DS18B20Sensor`, and `DHT22Sensor`. `SensorFactory.build()` merges driver defaults with config-supplied precision overrides (#134).
- Comprehensive unit test coverage added across all modules: `MonitoringAgent`, `InputManager`, `OutputManager`, `DisplayStatus`, display factory, sensor exceptions, factory exceptions, `GPIOSensor`, `TelemetryCollector`, `LoggingSetup`, and all sensor drivers (#126).
- `check-github-issues` and `organise-releases` Claude Code skills.

### Changed
- `TelemetryCollector._bundle_id()` now reads `bundle.full_id` directly instead of constructing its own identifier (#129).
- `DS18B20Sensor.read()` no longer rounds internally — precision is now applied uniformly by `TelemetryCollector._apply_precision()` (#134).
- ABC contracts for `BaseSensor` and `BaseDisplay` are now formally enforced with `@abstractmethod` declarations (#127).

### Fixed
- `pkg_resources` import in tests replaced with `importlib.metadata` after `pkg_resources` was dropped from `setuptools` (#125).

## [v2.4.2] - 2026-02-18

### Added
- Unit test for DHT22 sensor reset on read failure.
- `pi-testing` skill for creating release candidate tags.

### Fixed
- DHT22 sensor not recovering after stale `libgpiod` handle; sensor now tears down and re-creates on read failure instead of failing permanently.

### Changed
- CLAUDE.md updated with module isolation principles, layer responsibility rules, and venv activation instructions.

## [v2.4.1] - 2026-02-17

### Added
- `__version__.py` for internal version tracking, logged at startup.
- Unit tests to verify driver ACCEPTED_KWARGS, REQUIRED_KWARGS, and COERCERS align with `__init__` signatures.
- Version check step in prepare-release skill.

### Fixed
- DS18B20 water temperature now rounded to 1 decimal place to match air_temperature format.
- Poll period drift caused by `int()` truncation in delay calculation; now preserves sub-second accuracy.
- Noisy telemetry logging when no sensors are due; replaced with single debug message.

### Removed
- Stale TODO comments in config_loader.py that referenced already-implemented functionality.

## [v2.4.0] - 2026-02-16

### Added
- Waveshare 1.47" ST7789 LCD display driver (`waveshare_147_st7789.py`) with SPI interface.
- Custom 5x7 bitmap font (`font_5x7.py`) supporting uppercase letters, numbers, and symbols.
- `DisplayStatus` dataclass (`status_model.py`) consumed by all display drivers.
- `InputManager` to encapsulate sensor factory and telemetry collection behind a single `collect()` interface.
- `OutputManager` to fan out snapshots to displays with failure isolation and cleanup.
- Unit and hardware tests for the Waveshare 1.47" display.
- CLAUDE.md and `.claudeignore` for Claude Code integration.
- Prepare-release skill for release readiness checks.

### Changed
- Restructured project into `inputs/` and `outputs/` directories for clearer module separation.
  - Sensors moved from `monitoring_service/sensors/` to `monitoring_service/inputs/sensors/`.
  - Displays moved from `monitoring_service/display/` to `monitoring_service/outputs/display/`.
- `MonitoringAgent` now delegates to `InputManager` and `OutputManager` instead of managing sensors and displays directly.
- Waveshare display renders black background with white text, 2x scaled font, centered layout.
- Display renders air temp, humidity, and water flow alongside water temperature.

### Fixed
- ST7789 init sequence, framebuffer sizing, and reset to match Waveshare reference implementation.
- Pixel coordinate overflow in Waveshare display driver.
- OverflowError from buffer being too large to send to display.
- SensorFactory import path after `inputs/` restructure.
- Double close in Waveshare hardware test.

## [v2.3.0] - 2026-01-28

### Added
- No additions

### Changed

- Updated name of whole project to Trive Aquasense.
- Moved intended project location to /opt.
- Moved intended config and environment variables to /etc.
- Improved logic for ThingsBoard connection loop.
- updated tests to work with new locations and ThingsBoard logic.

### Documentation

- No updates

## [v2.2.0] - 2026-01-12

### Added
- Introduced a pluggable display subsystem with support for multiple displays via configuration.
- Added `BaseDisplay` abstraction to standardise display rendering and refresh throttling.
- Implemented `LoggingDisplay` for non-hardware testing and validation of display output.
- Added SSD1306 I2C OLED display support using the Adafruit SSD1306 driver.
- Display configuration now supports width, height, I2C address, refresh period, and enable flags.
- Telemetry snapshots are now rendered with:
    - Water temperature, air temperature, and air humidity.
    - Rounded values with appropriate units.
    - Human-readable timestamp of last update.

### Changed

- `agent.py` now outputs a snapshot containing timestamp and device name alongside telemetry values.
- Removed example `config.json` and `.env` from `README.md` as there are example files for this.

### Documentation

- Updated `README.md` to match new display directory structure.

## [v2.1.1] - 2025-12-23
### Added
- No new features.

### Changed
- Names of variables updated to be more semantic.

### Documentation
- Added/updated docstrings for all files, classes, methods.

## [v2.1.0] - 2025-12-05
### Added
- DHT22 sensor support for temperature and humidity.
- Unit tests for DHT22 driver and factory integration.
- Hardware test files for DHT22.
- Water flow sensor support for water flow readings.
- Unit tests for Water Flow driver and factory integration.
- Hardware test files for Water Flow sensor.
- README updates for wiring, config example, and expected telemetry keys.

### Changed
- SensorFactory now supports drivers that declare `REQUIRED_KWARGS`.
- Improved coercion and validation for GPIO-based sensors.

### Documentation
- Updated README.

## [v2.0.0] – 2025-10-21
### Added
- Modular SensorFactory for dynamic sensor creation.
- DS18B20 driver with calibration and validation.
- ThingsBoard MQTT client wrapper for telemetry.
- Attributes module for device metadata.

### Changed
- Refactored TelemetryCollector to use factory output.
- Improved ConfigLoader and logging setup.

### Fixed
- Stability and environment variable handling.

### Documentation
- Updated README and added systemd service example.

## [2.0.0-rc2] - 2025-10-20
### Fixed
- Resolved critical bug in DS18B20Sensor where the driver ignored provided path and mis-treated the file path as a base directory.
- Now correctly distinguishes between path (full w1_slave file) and base_dir (directory).
- Fully supports both configuration styles:
   - {"id": "28-xxxx", "path": "/sys/bus/w1/devices/"}
   - {"path": "/sys/bus/w1/devices/28-xxxx/w1_slave"}
- _get_device_file() no longer returns None and properly raises DS18B20ReadError on missing sensors.

### Improved
- Added explicit device_file attribute to DS18B20Sensor for clarity and logging.
- Enhanced TelemetryCollector ID resolution (id, sensor_id, path, or device_file) for more readable logs.

### Version
- Marked as release candidate 2 for v2.0.0.
- This RC focuses on verifying stable hardware operation before final release.

## [2.0.0-rc1] - 2025-10-18
### Added
- **SensorFactory** to build sensors from config (extensible, validated).
- **DS18B20Sensor** driver wired through the factory.
- **TelemetryCollector** integration with factory output (per-sensor intervals supported).
- **31 unit tests** now passing; hardware test markers for Pi-only runs.
- Local **deployment notes** and tag-based release flow (RCs).

### Changed
- Telemetry pipeline refactored to use factory-built sensor bundles.
- Config schema tightened and validated on build.
- Logging and module layout tidied for readability and deployment.

### Fixed
- More robust error handling around sensor reads (DS18B20 edge cases).

### Removed
- Direct, ad-hoc sensor instantiation in collector (replaced by factory).

### Breaking
- v1.x configs/expectations **won’t work** without updating to factory-driven config and key names.

## [1.0.0] - 2025-0X-XX
### Added
- First stable, working end-to-end version.
- Basic telemetry collection and ThingsBoard publish.
- Systemd service skeleton and minimal docs.

