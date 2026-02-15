# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Trive Aquasense is a Python application for Raspberry Pi that monitors aquarium telemetry (temperature, humidity, water flow) and sends data to ThingsBoard via MQTT. It runs as a systemd service in production.

**Target:** Raspberry Pi OS (Bookworm+), Python 3.11+

## Commands

```bash
# Run tests (unit only, no hardware needed)
pytest tests/unit/

# Run hardware integration tests (requires Pi + sensors)
pytest -m hardware tests/

# Run all tests
pytest tests/

# Run the application
python -m monitoring_service.main
```

## Architecture

**Data flow:** ConfigLoader → SensorFactory → TelemetryCollector → TBClientWrapper (MQTT) + Displays

Key modules in `monitoring_service/`:

- **main.py** — Bootstrap entry point
- **agent.py** — Main monitoring loop (`MonitoringAgent`)
- **config_loader.py** — Loads `config.json` + `.env` environment variables
- **telemetry.py** — `TelemetryCollector` reads sensors, applies calibration/smoothing/range filtering
- **TBClientWrapper.py** — ThingsBoard MQTT client abstraction
- **attributes.py** — Device attributes (IP, MAC) sent to ThingsBoard
- **inputs/sensors/** — Sensor drivers (DS18B20, DHT22, water flow) with factory pattern
- **outputs/display/** — Display drivers (SSD1306 OLED, Waveshare ST7789 LCD, logging) with factory pattern
- **outputs/status_model.py** — Display data model consumed by all display drivers

### Factory + Plugin Pattern

Sensors and displays follow the same pattern:
1. Implement the abstract base class (`BaseSensor` or `BaseDisplay`)
2. Register the new type in the corresponding factory
3. Add configuration to `config.json`

The factories validate config at startup and build typed bundles. Sensor key mapping, calibration (`offset` + `slope`), smoothing (EMA), and range filtering are all handled by `TelemetryCollector`, not by individual sensor drivers.

### Telemetry Pipeline

Raw sensor `read()` → key mapping → calibration → smoothing → range filtering → merge → send to ThingsBoard + render on displays

## Configuration

- **config.json** — Sensor/display definitions, poll period, log level (see `config.example.json`)
- **.env** — `ACCESS_TOKEN` and `THINGSBOARD_SERVER` (required), `CONFIG_PATH` (optional override)
- Production config: `/etc/trive_aquasense/config.json`
- Production install: `/opt/trive_aquasense`

## Testing Conventions

- Unit tests mock all hardware dependencies (GPIO, I2C, SPI, 1-Wire)
- Hardware tests use `@pytest.mark.hardware` marker
- Test fixtures provide standard sensor configurations
- Incomplete/WIP tests go in `tests/not_implemented/`

## Git Workflow

- `main` — Production stable
- `dev` — Development integration
- Feature branches: `v2.x.x-feature-name`
- Semantic versioning (MAJOR.MINOR.PATCH)