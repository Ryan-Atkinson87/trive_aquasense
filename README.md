# Trive Aquasense

![MIT License](https://img.shields.io/badge/license-MIT-green)

## Overview

**Trive Aquasense** is a lightweight Python application for Raspberry Pi that reads aquarium telemetry from physical sensors and sends it to a ThingsBoard instance via MQTT. It also renders live telemetry to attached displays. Designed for production environments with reliable telemetry reporting, structured logging, and systemd deployment.

**Target:** Raspberry Pi Zero WH, Raspberry Pi OS (Bookworm+), Python 3.11+

## Features

- Sends aquarium telemetry (temperature, humidity, water flow) to ThingsBoard via MQTT
- Sends static device attributes (device name, IP, MAC address)
- Renders live telemetry to OLED and LCD displays
- Local rotating log files for debugging and traceability
- Easily configurable via `.env` and `config.json`
- Production-ready systemd service
- Unit tested with Pytest

## Quick Start

```bash
git clone https://github.com/Ryan-Atkinson87/trive_aquasense.git
cd trive_aquasense
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp config.example.json config.json
# Edit config.json and create .env with ACCESS_TOKEN and THINGSBOARD_SERVER
python -m monitoring_service.main
```

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for full Pi setup, systemd installation, and production paths.

## Documentation

| Document | Contents |
|----------|----------|
| [docs/CONFIGURATION.md](docs/CONFIGURATION.md) | `config.json` and `.env` field reference |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Pi setup, systemd service, production paths |
| [docs/SENSORS.md](docs/SENSORS.md) | Wiring diagrams and config examples per sensor |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Module architecture and data flow |
| [docs/SENSOR_INTERFACE.md](docs/SENSOR_INTERFACE.md) | Sensor driver interface contract |

## Testing

```bash
source venv/bin/activate && pytest tests/unit/
source venv/bin/activate && pytest -m hardware tests/
```

## Contributing

Contributions are welcome — bug fixes, docs improvements, or new sensor support.

1. Fork the repository
2. Create a branch: `git checkout -b feature/my-feature`
3. Commit with a clear message and open a PR against `dev`
4. All new code must include unit tests
5. Check the [Project Board](https://github.com/Ryan-Atkinson87/trive_aquasense/projects) for ongoing work

## License

This project is licensed under the [MIT License](LICENSE).