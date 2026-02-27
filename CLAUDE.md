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
- **telemetry.py** — `TelemetryCollector` owns per-sensor interval scheduling, key mapping, calibration, EMA smoothing, and range filtering
- **outputs/output_manager.py** — `OutputManager` fans out snapshots to displays, isolates failures, manages cleanup via `close()`
- **outputs/display/** — Display drivers (`BaseDisplay` ABC, `render()` + `close()`). Factory builds from config
- **outputs/status_model.py** — `DisplayStatus` dataclass consumed by all display drivers
- **TBClientWrapper.py** — ThingsBoard MQTT client abstraction
- **attributes.py** — Static device attributes (hostname, MAC, IP, device_name) sent to ThingsBoard
- **__version__.py** — Single-source version string (e.g. `"2.4.1"`)
- **exceptions/** — Custom domain exceptions: `FactoryError` base, `UnknownSensorTypeError`, `InvalidSensorConfigError`, plus `GPIOValueError` in `gpio_sensor.py`
- **logging_setup.py** — Central logger with `RotatingFileHandler` (5MB, 3 backups) + console

### Factory + Plugin Pattern

Sensors and displays follow the same extensibility pattern:
1. Implement the abstract base class (`BaseSensor` or `BaseDisplay`)
2. Register the new type in the corresponding factory
3. Add configuration to `config.json`

Sensor drivers declare `REQUIRED_KWARGS`, `ACCEPTED_KWARGS`, and `COERCERS` as class attributes. The factory validates config, coerces types, and constructs `SensorBundle` (driver + key mapping + calibration + ranges + smoothing + interval).

### Telemetry Pipeline

Raw sensor `read()` → key mapping → calibration (`value * slope + offset`) → EMA smoothing → range filtering → merge → send to ThingsBoard + render on displays

## Configuration

- **config.json** — Sensor/display definitions, `poll_period`, `device_name`, `log_level`, `mount_path` (see `config.example.json`)
- **.env** — `ACCESS_TOKEN` and `THINGSBOARD_SERVER` (required), `CONFIG_PATH` (optional override)
- Production config: `/etc/trive_aquasense/config.json`
- Production install: `/opt/trive_aquasense`
- No secrets in code. No module reads config files directly — only `ConfigLoader`.
- **docs/** — Additional documentation (e.g. `SENSOR_INTERFACE.md`)
- **versions/** — Archived release zip files

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

## INSTRUCTIONS.md

`INSTRUCTIONS.md` is a companion file for use as Claude.ai project context (UI conversations). It mirrors the architecture and rules in this file but is written without CLI-specific commands.

- It is gitignored — never commit it, never create it if it does not exist
- It must be kept in sync with this file **only on machines where it already exists**
- The `prepare-release` and `release-and-cleanup` skills both include a step to regenerate it
- If you update this file outside of a skill, also update `INSTRUCTIONS.md` to reflect the changes
- **If `INSTRUCTIONS.md` does not exist, skip all sync steps silently — do not create it**