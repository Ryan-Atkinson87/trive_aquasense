# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Trive Aquasense is a structured Python agent for Raspberry Pi that reads aquarium telemetry from physical sensors, normalises the data, and sends it to ThingsBoard via MQTT. It also renders live telemetry to attached displays. It runs as a systemd service in production.

**Target:** Raspberry Pi Zero WH, Raspberry Pi OS (Bookworm+), Python 3.11+

## Commands

```bash
# Shell state doesn't persist between Bash calls, so always chain with activate:
source venv/bin/activate && pytest tests/unit/
source venv/bin/activate && pytest tests/unit/test_dht22_sensor.py
source venv/bin/activate && pytest -m hardware tests/
source venv/bin/activate && pytest tests/
source venv/bin/activate && python -m monitoring_service.main
```

## Architecture

### Module Isolation (Hard Rule)

Each module must be unaware of the internals of any other module. No cross-import spaghetti, no shared global state, no circular dependencies. All interaction happens via clear interfaces and constructor injection. Each module talks to interfaces and contracts, not implementations.

**Dependency direction:** dependencies flow inward toward simple data structures.

**Each layer knows only its own job.** A module does one thing, takes its dependencies via constructor injection, and knows nothing about the layers above or beside it. Logging is centrally configured — never imported ad-hoc inside domain logic. Only the factory knows concrete classes. Only `ConfigLoader` reads config files.

**Replaceability test:** you should be able to swap any layer's implementation (e.g. replace MQTT with HTTP, swap a sensor library) without any other module noticing.

```
Sensors → InputManager → MonitoringAgent → OutputManager → Displays
                              ↓
                        TBClientWrapper
```

### Key Modules (`monitoring_service/`)

- **main.py** — Bootstrap: loads config, constructs managers, wires dependencies, starts agent
- **agent.py** — `MonitoringAgent` runs the main loop. Only orchestration layer — delegates to `InputManager` for collection and `OutputManager` for rendering
- **config_loader.py** — Merges `config.json` + `.env`, validates required fields. No other module reads files directly
- **inputs/input_manager.py** — `InputManager` wraps `SensorFactory` + `TelemetryCollector` behind a single `collect()` interface
- **inputs/sensors/** — One driver per sensor type (`BaseSensor` ABC, `read()` returns raw dict). Factory validates config and builds `SensorBundle` dataclasses. `GPIOSensor` intermediate base class provides shared GPIO validation. `constants.py` defines `VALID_GPIO_PINS`. `non_functional/` holds WIP drivers not yet production-ready (e.g. `i2c_water_level`)
- **telemetry.py** — `TelemetryCollector` owns per-sensor interval scheduling, key mapping, calibration, EMA smoothing, range filtering, and precision rounding
- **outputs/output_manager.py** — `OutputManager` fans out snapshots to displays, isolates failures, manages cleanup via `close()`
- **outputs/display/** — Display drivers (`BaseDisplay` ABC, `render()` + `render_startup()` + `close()`). Factory builds from config. Each display config entry must include both `"show_startup": true/false` and `"system_screen": true/false` — these are required fields for every display entry. `show_startup: true` opts a display into bootstrap/status messages; `system_screen: true` dedicates a display to the persistent system-status layout (fixed header + rolling 2-message log) and disables telemetry rendering on it. `system_screen: true` implies `show_startup: true`. Intended use: set `system_screen: true` on the small OLED when a second display is connected. Always add both fields when adding a new display to `config.example.json`.
- **outputs/status_model.py** — `DisplayStatus` dataclass. Content assembly (formatting telemetry values into display strings such as `"WATER: 24.1C"`) belongs in `OutputManager` or a dedicated helper — not in display drivers. Display drivers must not import `DisplayStatus` or reference telemetry key names directly; they receive a pre-formatted generic payload and are responsible only for rendering it to pixels/text
- **TBClientWrapper.py** — ThingsBoard MQTT client abstraction
- **attributes.py** — Static device attributes (hostname, MAC, IP, device_name) sent to ThingsBoard
- **__version__.py** — Single-source version string (e.g. `"2.5.0"`)
- **exceptions/** — Custom domain exceptions. All files follow the `*_exceptions.py` naming convention: `factory_exceptions.py` (`FactoryError`, `UnknownSensorTypeError`, `InvalidSensorConfigError`), `sensor_exceptions.py` (`SensorInitError`, `SensorReadError`, `SensorStopError`, `SensorValueError`) — note: currently named `sensors.py`, pending rename, `config_exceptions.py` (`ConfigError`, `ConfigFileNotFoundError`, `ConfigValidationError`, `MissingEnvVarError`). `GPIOValueError` lives in `gpio_sensor.py`
- **logging_setup.py** — Central logger with `RotatingFileHandler` (5MB, 3 backups) + console

### Factory + Plugin Pattern

Sensors and displays follow the same extensibility pattern:
1. Implement the abstract base class (`BaseSensor` or `BaseDisplay`)
2. Register the new type in the corresponding factory
3. Add configuration to `config.json`

Sensor drivers declare `REQUIRED_KWARGS`, `ACCEPTED_KWARGS`, `COERCERS`, and optionally `DEFAULT_PRECISION` as class attributes. The factory validates config, coerces types, merges driver precision defaults with config overrides, and constructs `SensorBundle` (driver + key mapping + calibration + ranges + smoothing + precision + interval + full_id).

### Telemetry Pipeline

Raw sensor `read()` → key mapping → calibration (`value * slope + offset`) → EMA smoothing → range filtering → precision rounding → merge → send to ThingsBoard + render on displays

## Configuration

- **config.example.json** — Committed template for sensor/display definitions, `poll_period`, `device_name`, `log_level`, `mount_path`. Copy to `config.json` locally and on the Pi to configure the deployment. `config.json` is gitignored.
- **.env** — `ACCESS_TOKEN` and `THINGSBOARD_SERVER` (required), `CONFIG_PATH` (optional override)
- Production config: `/etc/trive_aquasense/config.json`
- Production install: `/opt/trive_aquasense`
- Production `.env`: `/etc/trive_aquasense/.env` — loaded by the systemd service via `EnvironmentFile=`
- Production service file: `/etc/systemd/system/trive_aquasense.service` — see `trive_aquasense_example.service` for the template. **Whenever the service file configuration is changed, update `trive_aquasense_example.service` to match.**
- No secrets in code. No module reads config files directly — only `ConfigLoader`.
- **docs/** — Additional documentation (e.g. `SENSOR_INTERFACE.md`)
- **versions/** — Archived release zip files

## Code Style Conventions

- **Semantic variable names** — no terse abbreviations. Use `log_method` not `fn`; `_ema_state` not `_ema`. Names should be self-explanatory without surrounding context.
- **No inline comments on dataclass fields** — field names and type hints are the documentation. The class docstring covers overall purpose. Do not add comments that restate the field name.
- **Section dividers in all drivers** — every sensor and display driver must use `# --- Properties ---`, `# --- Internals ---`, `# --- Public API ---` style dividers. Use `dht22.py` as the reference. Single-line comments elsewhere only where logic is genuinely non-obvious.
- **No operational notes in source files** — installation instructions, `systemctl` commands, wiring notes, and setup steps belong in `docs/`, not in driver files or module headers.
- **Exception file naming** — all exception files follow the `*_exceptions.py` convention: `config_exceptions.py`, `factory_exceptions.py`, `sensor_exceptions.py`.

## Testing Conventions

- Unit tests mock all hardware dependencies (GPIO, I2C, SPI, 1-Wire)
- Hardware tests use `@pytest.mark.hardware` marker
- Test fixtures provide standard sensor configurations
- Incomplete/WIP tests go in `tests/not_implemented/`
- **Mocking submodule imports (e.g. `RPi.GPIO`):** When a driver does `import RPi.GPIO as GPIO`, Python resolves via attribute access on the parent module. You must link both `sys.modules` entries to the same mock object:
  ```python
  mock_gpio = MagicMock()
  mock_rpi = MagicMock()
  mock_rpi.GPIO = mock_gpio          # attribute access path
  sys.modules["RPi"] = mock_rpi
  sys.modules["RPi.GPIO"] = mock_gpio  # import system path
  ```
  Setting them independently causes the driver to bind to an auto-generated child mock instead of your mock, so assertions on `mock_gpio` silently fail.

## GitHub CLI

- Always use `--json` with specific fields when calling `gh issue view` to avoid a GraphQL deprecation error from Projects (classic):
  ```bash
  gh issue view 61 --repo Ryan-Atkinson87/trive_aquasense --json title,body,labels,state
  ```
  Running `gh issue view` without `--json` triggers a non-fatal error about Projects (classic) sunset.

## Git Workflow

- `main` — Production stable
- `dev` — Development integration
- Feature branches: `v2.x.x-feature-name`
- Pi test tags: `v2.x.x-pi_testN`
- Semantic versioning (MAJOR.MINOR.PATCH)
- Pull requests into `dev` and `main` are created via GitHub, not the CLI
- **Commit message prefixes:**
  - On a versioned feature branch (e.g. `v2.4.2-some-feature`): prefix with `v2.4.2 - `
  - On `main` or `dev` directly: ask the user to confirm before committing, then prefix with `adhoc - `
- **GitHub issue commits:** when a commit resolves or contributes to a GitHub issue, include the issue number in the message: `v2.5.0 - Fix pkg_resources test failure (#125)`
- **One commit per issue:** each GitHub issue is implemented and committed separately. Do not bundle multiple issues into one commit.

## INSTRUCTIONS.md

`INSTRUCTIONS.md` is a companion file for use as Claude.ai project context (UI conversations). It mirrors the architecture and rules in this file but is written without CLI-specific commands.

- It is gitignored — never commit it, never create it if it does not exist
- It must be kept in sync with this file **only on machines where it already exists**
- The `prepare-release` and `release-and-cleanup` skills both include a step to regenerate it
- If you update this file outside of a skill, also update `INSTRUCTIONS.md` to reflect the changes
- **If `INSTRUCTIONS.md` does not exist, skip all sync steps silently — do not create it**