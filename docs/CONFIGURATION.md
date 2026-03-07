# Configuration Reference

## Overview

Trive Aquasense is configured via two files:

- **`.env`** — secrets and environment-specific overrides (never committed)
- **`config.json`** — sensor/display definitions and operational parameters (gitignored; use `config.example.json` as the template)

Only `ConfigLoader` reads these files. No other module accesses them directly.

---

## `.env`

| Variable             | Required | Description                                                       |
|----------------------|----------|-------------------------------------------------------------------|
| `ACCESS_TOKEN`       | Yes      | ThingsBoard MQTT device access token                              |
| `THINGSBOARD_SERVER` | Yes      | ThingsBoard host (e.g. `demo.thingsboard.io`)                     |
| `CONFIG_PATH`        | No       | Override path to `config.json`. Defaults to `config.json` in CWD |

Example:

```dotenv
ACCESS_TOKEN=your_device_token_here
THINGSBOARD_SERVER=demo.thingsboard.io
```

---

## `config.json`

Copy `config.example.json` to `config.json` and edit for your deployment.

### Top-level fields

| Field              | Type    | Required | Description                                                   |
|--------------------|---------|----------|---------------------------------------------------------------|
| `poll_period`      | int     | Yes      | Global telemetry send interval in seconds                     |
| `device_name`      | string  | Yes      | Human-readable device label sent as a ThingsBoard attribute   |
| `mount_path`       | string  | Yes      | Filesystem path used for disk-usage reporting (e.g. `"/"`)    |
| `log_level`        | string  | Yes      | Logging verbosity: `"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"`|
| `log_max_bytes`    | int     | No       | Max log file size before rotation. Default: `5242880` (5 MB)  |
| `log_backup_count` | int     | No       | Number of rotated log backups to keep. Default: `3`           |
| `displays`         | array   | Yes      | List of display configuration objects (see below)             |
| `sensors`          | array   | Yes      | List of sensor configuration objects (see below)              |

### Display configuration

Each entry in `displays` must include:

| Field            | Type    | Required | Description                                                                                  |
|------------------|---------|----------|----------------------------------------------------------------------------------------------|
| `type`           | string  | Yes      | Display driver identifier (e.g. `ssd1306_i2c`, `waveshare_147_st7789`, `logging`)           |
| `enabled`        | bool    | Yes      | Whether this display is active                                                               |
| `show_startup`   | bool    | Yes      | Opt into bootstrap/status messages on startup                                                |
| `system_screen`  | bool    | Yes      | Dedicate this display to the persistent system-status layout (disables telemetry rendering). Implies `show_startup: true` |
| `refresh_period` | int     | Yes      | How often (seconds) the display refreshes                                                    |

Additional driver-specific fields (e.g. `width`, `height`, `address` for SSD1306; `spi`, `pins` for Waveshare) are documented alongside the driver.

### Sensor configuration

Each entry in `sensors` must include:

| Field         | Type   | Required | Description                                                                  |
|---------------|--------|----------|------------------------------------------------------------------------------|
| `type`        | string | Yes      | Sensor driver identifier (e.g. `ds18b20`, `DHT22`, `water_flow`)            |
| `id`          | string | Yes      | Unique identifier for this sensor instance (e.g. `gpio17`, `28-xxxx`)       |
| `keys`        | object | Yes      | Maps driver output keys to canonical telemetry keys                          |
| `calibration` | object | Yes      | Per telemetry key: `{ "offset": float, "slope": float }`. Applied as `value * slope + offset` |
| `ranges`      | object | Yes      | Per telemetry key: `{ "min": number, "max": number }`. Out-of-range readings are discarded |
| `smoothing`   | object | No       | Per telemetry key: `{ "window": int }` for EMA smoothing. Omit or leave `{}` to disable |
| `precision`   | object | No       | Per telemetry key: decimal places to round to. Driver defaults apply if omitted |
| `interval`    | int    | No       | Per-sensor read frequency in seconds. Defaults to `poll_period` if omitted   |

Additional driver-specific fields (e.g. `pin`, `path`, `sensor_id`, `bus`) vary by sensor type. See [SENSORS.md](SENSORS.md) for per-sensor field reference.

---

## Production config path

In production the service reads config from `/etc/trive_aquasense/config.json`. Set `CONFIG_PATH` in `.env` to override:

```dotenv
CONFIG_PATH=/etc/trive_aquasense/config.json
```