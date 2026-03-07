# Architecture Overview

## Module dependency flow

Dependencies flow inward toward simple data structures. Each layer knows only its own job, takes dependencies via constructor injection, and is unaware of the layers above or beside it.

```mermaid
flowchart TD
    CFG[config.json / .env\nConfigLoader]
    MAIN[main.py\nBootstrap]
    IM[InputManager]
    SF[SensorFactory]
    TC[TelemetryCollector]
    S1[DS18B20]
    S2[DHT22]
    S3[WaterFlow]
    MA[MonitoringAgent]
    TB[TBClientWrapper\nThingsBoard MQTT]
    OM[OutputManager]
    D1[SSD1306 OLED]
    D2[Waveshare LCD]
    D3[LoggingDisplay]

    CFG --> MAIN
    MAIN --> MA
    MAIN --> IM
    MAIN --> OM
    MAIN --> TB

    MA --> IM
    MA --> OM
    MA --> TB

    IM --> SF
    IM --> TC
    SF --> S1
    SF --> S2
    SF --> S3

    OM --> D1
    OM --> D2
    OM --> D3
```

## Data flow (telemetry pipeline)

```
Sensor.read()
  → key mapping
  → calibration (value * slope + offset)
  → EMA smoothing
  → range filtering
  → precision rounding
  → merged telemetry dict
      → TBClientWrapper (ThingsBoard MQTT)
      → OutputManager → Display drivers
```

## Key modules

| Module | Responsibility |
|--------|----------------|
| `main.py` | Bootstrap only: loads config, constructs all components, wires dependencies, starts agent |
| `agent.py` | `MonitoringAgent` — runs the main loop, delegates collection to `InputManager` and rendering to `OutputManager` |
| `config_loader.py` | Merges `config.json` + `.env`, validates required fields. Only module that reads files |
| `inputs/input_manager.py` | Wraps `SensorFactory` + `TelemetryCollector` behind a single `collect()` interface |
| `inputs/sensors/` | One driver per sensor type. `BaseSensor` ABC, `read()` returns raw dict. Factory builds `SensorBundle` dataclasses |
| `telemetry.py` | `TelemetryCollector` — per-sensor interval scheduling, key mapping, calibration, EMA smoothing, range filtering, precision rounding |
| `outputs/output_manager.py` | Fans out snapshots to all displays, isolates failures, manages cleanup |
| `outputs/display/` | Display drivers — `BaseDisplay` ABC, `render()` / `render_startup()` / `close()`. Receive pre-formatted content; must not assemble telemetry strings |
| `TBClientWrapper.py` | ThingsBoard MQTT client abstraction |
| `attributes.py` | Static device attributes (hostname, MAC, IP, device name) sent to ThingsBoard |
| `logging_setup.py` | Central logger with `RotatingFileHandler`. Never imported ad-hoc into domain logic |
| `exceptions/` | Domain exceptions: `config_exceptions.py`, `factory_exceptions.py`, `sensor_exceptions.py` |

## Design rules

- **Module isolation** — no cross-import spaghetti, no shared global state, no circular dependencies
- **Constructor injection** — each module receives its dependencies; only the factory knows concrete classes
- **Replaceability** — any layer's implementation can be swapped (e.g. replace MQTT with HTTP, swap a sensor library) without other modules noticing
- **Display drivers are output-only** — they receive pre-formatted strings and render to pixels/text; they do not import `DisplayStatus` or reference telemetry key names
- **Sensor drivers are minimal** — they read hardware and return dicts; no logging, no transport awareness, no scheduling