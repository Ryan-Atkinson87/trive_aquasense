# pigpio Setup

The `water_flow` sensor driver requires the `pigpiod` daemon to be installed
and running on the Raspberry Pi.

## Installation

```bash
sudo apt update
sudo apt install pigpio python3-pigpio
```

## Enable and start the daemon

```bash
sudo systemctl enable pigpiod
sudo systemctl start pigpiod
```

## Verify

```bash
sudo systemctl status pigpiod
```