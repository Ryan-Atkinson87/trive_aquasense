# Deployment Guide

## Prerequisites

- Raspberry Pi OS (Bookworm or later)
- Python 3.11+
- A running ThingsBoard instance
- An MQTT device access token from ThingsBoard

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/Ryan-Atkinson87/trive_aquasense.git /opt/trive_aquasense
cd /opt/trive_aquasense
```

### 2. Set up the virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure the environment

```bash
cp config.example.json config.json
```

Edit `config.json` with your sensor IDs, display settings, and operational parameters. See [CONFIGURATION.md](CONFIGURATION.md) for a full field reference.

Create `.env` with your credentials:

```dotenv
ACCESS_TOKEN=your_device_token_here
THINGSBOARD_SERVER=demo.thingsboard.io
```

---

## Running directly

```bash
source venv/bin/activate
python -m monitoring_service.main
```

---

## Pi hardware setup

### Enable 1-Wire (DS18B20)

```bash
sudo raspi-config
# Interface Options → 1-Wire → Enable
```

Or add to `/boot/firmware/config.txt`:

```
dtoverlay=w1-gpio
```

Then reboot. Confirm the sensor appears under `/sys/bus/w1/devices/`.

### Enable I2C (SSD1306, water level sensor)

```bash
sudo raspi-config
# Interface Options → I2C → Enable
```

Verify with: `i2cdetect -y 1`

### Enable SPI (Waveshare display)

```bash
sudo raspi-config
# Interface Options → SPI → Enable
```

### pigpio daemon (water flow sensor)

The water flow sensor uses pigpio. Start the daemon on boot:

```bash
sudo systemctl enable pigpiod
sudo systemctl start pigpiod
```

---

## systemd service (production)

A service template is provided at `trive_aquasense_example.service`.

### Install the service

Copy the template (production paths are already set):

```bash
sudo cp trive_aquasense_example.service /etc/systemd/system/trive_aquasense.service
```

Place your `.env` at the path the service expects:

```bash
sudo mkdir -p /etc/trive_aquasense
sudo cp .env /etc/trive_aquasense/.env
```

Then enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable trive_aquasense.service
sudo systemctl start trive_aquasense.service
```

### Check service status

```bash
sudo systemctl status trive_aquasense.service
journalctl -u trive_aquasense.service -f
```

---

## Production paths

| Path                                          | Purpose                                                  |
|-----------------------------------------------|----------------------------------------------------------|
| `/opt/trive_aquasense/`                       | Application root                                         |
| `/etc/trive_aquasense/config.json`            | Production config (set via `CONFIG_PATH` in `.env`)      |
| `/etc/trive_aquasense/.env`                   | Environment variables — injected by systemd via `EnvironmentFile=` |
| `/etc/systemd/system/trive_aquasense.service` | systemd unit file                                        |

---

## Updating

```bash
cd /opt/trive_aquasense
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart trive_aquasense.service
```