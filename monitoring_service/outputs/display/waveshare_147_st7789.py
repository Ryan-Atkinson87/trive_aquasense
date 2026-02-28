"""
waveshare_147_st7789.py

Waveshare 1.47" LCD (ST7789V3) display driver
Resolution: 172x320 (centered in 240x320 GRAM)
Interface: SPI (4-wire)
"""

import time
import logging
from typing import Mapping, Any

import spidev
import RPi.GPIO as GPIO

from monitoring_service.outputs.display.base import BaseDisplay
from monitoring_service.outputs.display.font_5x7 import FONT_5X7
from monitoring_service.outputs.status_model import DisplayStatus


class Waveshare147ST7789Display(BaseDisplay):
    # Visible panel size
    WIDTH = 172
    HEIGHT = 320

    # Panel is horizontally centered in 240-wide GRAM
    X_OFFSET = 34
    Y_OFFSET = 0

    FONT_SCALE = 2
    SPI_WRITE_CHUNK = 4096  # spidev write limit

    def __init__(self, config: Mapping[str, Any]) -> None:
        super().__init__(config)
        self._validate_config(config)

        self._logger = logging.getLogger(
            "monitoring_service.display.waveshare_147_st7789"
        )

        pins = config["pins"]
        spi_cfg = config["spi"]

        self._dc_pin = pins["dc"]
        self._reset_pin = pins["reset"]
        self._backlight_pin = pins["backlight"]

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self._dc_pin, GPIO.OUT)
        GPIO.setup(self._reset_pin, GPIO.OUT)
        GPIO.setup(self._backlight_pin, GPIO.OUT)

        self._spi = spidev.SpiDev()
        self._spi.open(spi_cfg["bus"], spi_cfg["device"])
        self._spi.mode = spi_cfg.get("mode", 0)
        self._spi.max_speed_hz = spi_cfg.get("max_speed_hz", 10_000_000)

        self._framebuffer = bytearray(
            self.WIDTH * self.HEIGHT * 2
        )

        self._logger.info(
            "ST7789 init: visible=%dx%d offset=(%d,%d)",
            self.WIDTH,
            self.HEIGHT,
            self.X_OFFSET,
            self.Y_OFFSET,
        )

        self._hardware_reset()
        self._init_display()

        GPIO.output(self._backlight_pin, GPIO.HIGH)

    # ------------------------------------------------------------------
    # Low-level helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _rgb565(r: int, g: int, b: int) -> bytes:
        value = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
        return value.to_bytes(2, "big")

    @staticmethod
    def _u16(value: int) -> bytes:
        return value.to_bytes(2, "big")

    def _write_command(self, command: int) -> None:
        GPIO.output(self._dc_pin, GPIO.LOW)
        self._spi.writebytes([command])

    def _write_data(self, data: bytes) -> None:
        GPIO.output(self._dc_pin, GPIO.HIGH)

        for i in range(0, len(data), self.SPI_WRITE_CHUNK):
            self._spi.writebytes(data[i:i + self.SPI_WRITE_CHUNK])

    def _hardware_reset(self) -> None:
        GPIO.output(self._reset_pin, GPIO.HIGH)
        time.sleep(0.01)
        GPIO.output(self._reset_pin, GPIO.LOW)
        time.sleep(0.01)
        GPIO.output(self._reset_pin, GPIO.HIGH)
        time.sleep(0.01)

    # ------------------------------------------------------------------
    # Display init
    # ------------------------------------------------------------------

    def _init_display(self) -> None:
        self._write_command(0x36)  # MADCTL
        self._write_data(b"\x00")  # Portrait, RGB

        self._write_command(0x3A)  # COLMOD
        self._write_data(b"\x05")  # RGB565 (MCU interface)

        self._write_command(0xB2)  # Porch control
        self._write_data(b"\x0C\x0C\x00\x33\x33")

        self._write_command(0xB7)  # Gate control
        self._write_data(b"\x35")

        self._write_command(0xBB)  # VCOM setting
        self._write_data(b"\x35")

        self._write_command(0xC0)  # LCM control
        self._write_data(b"\x2C")

        self._write_command(0xC2)  # VDV/VRH enable
        self._write_data(b"\x01")

        self._write_command(0xC3)  # VRH set
        self._write_data(b"\x13")

        self._write_command(0xC4)  # VDV set
        self._write_data(b"\x20")

        self._write_command(0xC6)  # Frame rate control
        self._write_data(b"\x0F")

        self._write_command(0xD0)  # Power control
        self._write_data(b"\xA4\xA1")

        self._write_command(0xE0)  # Positive gamma correction
        self._write_data(
            b"\xF0\xF0\x00\x04\x04\x04\x05\x29"
            b"\x33\x3E\x38\x12\x12\x28\x30"
        )

        self._write_command(0xE1)  # Negative gamma correction
        self._write_data(
            b"\xF0\x07\x0A\x0D\x0B\x07\x28"
            b"\x33\x3E\x36\x14\x14\x29\x32"
        )

        self._write_command(0x21)  # Display inversion on

        self._write_command(0x11)  # SLPOUT
        time.sleep(0.15)

        self._write_command(0x29)  # DISPON

    def _set_window(self) -> None:
        self._write_command(0x2A)
        self._write_data(
            self._u16(self.X_OFFSET) +
            self._u16(self.X_OFFSET + self.WIDTH - 1)
        )

        self._write_command(0x2B)
        self._write_data(
            self._u16(self.Y_OFFSET) +
            self._u16(self.Y_OFFSET + self.HEIGHT - 1)
        )

        self._write_command(0x2C)

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def _clear_framebuffer(self, color: bytes) -> None:
        self._framebuffer[:] = color * (self.WIDTH * self.HEIGHT)

    def _draw_pixel(self, x: int, y: int, color: bytes) -> None:
        if not (0 <= x < self.WIDTH and 0 <= y < self.HEIGHT):
            return

        idx = (y * self.WIDTH + x) * 2
        self._framebuffer[idx:idx + 2] = color

    def _draw_char(
        self, x: int, y: int, char: str, color: bytes, scale: int = 1,
    ) -> None:
        glyph = FONT_5X7.get(char.upper())
        if not glyph:
            return

        for col, bits in enumerate(glyph):
            for row in range(7):
                if bits & (1 << row):
                    px = x + col * scale
                    py = y + row * scale
                    for sy in range(scale):
                        for sx in range(scale):
                            self._draw_pixel(px + sx, py + sy, color)

    def draw_text(
        self, x: int, y: int, text: str, color: bytes, scale: int = 1,
    ) -> None:
        cx = x
        for char in text:
            self._draw_char(cx, y, char, color, scale)
            cx += 6 * scale

    @staticmethod
    def _text_width(text: str, scale: int = 1) -> int:
        return len(text) * 6 * scale - scale

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render(self, snapshot: Mapping[str, Any]) -> None:
        if not self._should_render():
            return

        try:
            status = DisplayStatus.from_snapshot(snapshot)

            self._clear_framebuffer(self._rgb565(0, 0, 0))

            white = self._rgb565(255, 255, 255)
            scale = self.FONT_SCALE

            # Build lines to render
            lines: list[str] = [status.device_name]

            if status.water_temperature is not None:
                lines.append(f"WATER:{status.water_temperature:.1f}C")

            if status.air_temperature is not None:
                lines.append(f"AIR:{status.air_temperature:.1f}C")

            if status.air_humidity is not None:
                lines.append(f"HUMID:{status.air_humidity:.1f}%")

            if status.water_flow is not None:
                lines.append(f"FLOW:{status.water_flow:.1f}L/M")

            # 10% margins on each side
            y_margin = int(self.HEIGHT * 0.10)
            usable_height = self.HEIGHT - 2 * y_margin
            char_height = 7 * scale
            n = len(lines)

            if n > 1:
                line_stride = (usable_height - char_height) // (n - 1)
            else:
                line_stride = 0

            for i, text in enumerate(lines):
                tw = self._text_width(text, scale)
                x = (self.WIDTH - tw) // 2
                y = y_margin + i * line_stride
                self.draw_text(x, y, text, white, scale)

            self._set_window()
            self._write_data(self._framebuffer)

            self._logger.debug("Display rendered successfully")

        except Exception:
            self._logger.warning("Render failed", exc_info=True)

    def render_startup(self, message: str) -> None:
        """
        Render a bootstrap progress message centred on the display.

        Args:
            message: Short status string to display.
        """
        try:
            self._clear_framebuffer(self._rgb565(0, 0, 0))

            white = self._rgb565(255, 255, 255)
            scale = self.FONT_SCALE
            tw = self._text_width(message, scale)
            x = max(0, (self.WIDTH - tw) // 2)
            y = self.HEIGHT // 2 - (7 * scale) // 2
            self.draw_text(x, y, message, white, scale)

            self._set_window()
            self._write_data(self._framebuffer)

        except Exception:
            self._logger.warning("Failed to render startup message on Waveshare display", exc_info=True)

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Release SPI and GPIO resources."""
        GPIO.output(self._backlight_pin, GPIO.LOW)
        self._spi.close()
        GPIO.cleanup([self._dc_pin, self._reset_pin, self._backlight_pin])

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_config(config: Mapping[str, Any]) -> None:
        if "spi" not in config:
            raise ValueError("Display config missing 'spi'")
        if "pins" not in config:
            raise ValueError("Display config missing 'pins'")

        for key in ("bus", "device"):
            if key not in config["spi"]:
                raise ValueError(f"SPI config missing '{key}'")

        for pin in ("dc", "reset", "backlight"):
            if pin not in config["pins"]:
                raise ValueError(f"Pin config missing '{pin}'")