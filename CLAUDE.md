# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Trive Aquasense is a structured Python agent for Raspberry Pi that reads aquarium telemetry from physical sensors, normalises the data, and sends it to ThingsBoard via MQTT. It also renders live telemetry to attached displays. It runs as a systemd service in production.

**Target:** Raspberry Pi Zero WH, Raspberry Pi OS (Bookworm+), Python 3.11+

## Commands

```bash
# Run tests (unit only, no hardware needed)
pytest tests/unit/

# Run a single test file
pytest tests/unit/test_dht22_sensor.py

# Run hardware integration tests (requires Pi + sensors)
pytest -m hardware tests/

# Run all tests
pytest tests/

# Run the application
python -m monitoring_service.main
```

## Architecture

### Module Isolation (Hard Rule)

Each module must be unaware of the internals of any other module. No cross-import spaghetti, no shared global state, no circular dependencies. All interaction happens via clear interfaces and constructor injection.

**Dependency direction:** dependencies flow inward toward simple data structures.

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
- **inputs/sensors/** — One driver per sensor type (`BaseSensor` ABC, `read()` returns raw dict). Factory validates config and builds `SensorBundle` dataclasses
- **telemetry.py** — `TelemetryCollector` owns per-sensor interval scheduling, key mapping, calibration, EMA smoothing, and range filtering
- **outputs/output_manager.py** — `OutputManager` fans out snapshots to displays, isolates failures, manages cleanup via `close()`
- **outputs/display/** — Display drivers (`BaseDisplay` ABC, `render()` + `close()`). Factory builds from config
- **outputs/status_model.py** — `DisplayStatus` dataclass consumed by all display drivers
- **TBClientWrapper.py** — ThingsBoard MQTT client abstraction
- **attributes.py** — Static device attributes (hostname, MAC, IP, device_name) sent to ThingsBoard
- **exceptions/** — Custom domain exceptions (e.g. `UnknownSensorTypeError`, `InvalidSensorConfigError`)
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

## Testing Conventions

- Unit tests mock all hardware dependencies (GPIO, I2C, SPI, 1-Wire)
- Hardware tests use `@pytest.mark.hardware` marker
- Test fixtures provide standard sensor configurations
- Incomplete/WIP tests go in `tests/not_implemented/`

## Git Workflow

- `main` — Production stable
- `dev` — Development integration
- Feature branches: `v2.x.x-feature-name`
- Pi test tags: `v2.x.x-pi_testN`
- Semantic versioning (MAJOR.MINOR.PATCH)