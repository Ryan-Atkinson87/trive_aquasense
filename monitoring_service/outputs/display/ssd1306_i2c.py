"""
ssd1306_i2c.py

Provides an SSD1306 I2C OLED display implementation for rendering telemetry
snapshots using the Adafruit SSD1306 driver and PIL for text layout.

This display renders a fixed 3-row layout:
  - Row 1: Metric labels (Water | Air | Humidity)
  - Row 2: Metric values with units
  - Row 3: Timestamp of last telemetry update
"""

import logging
from datetime import datetime
from typing import Mapping, Any

from PIL import Image, ImageDraw, ImageFont

import board
import busio
import adafruit_ssd1306

from monitoring_service.outputs.display.base import BaseDisplay
from monitoring_service.outputs.status_model import DisplayStatus


class SSD1306I2CDisplay(BaseDisplay):
    """
    SSD1306-based I2C OLED display implementation.

    This class is responsible only for rendering already-collected telemetry
    snapshots. It does not perform any sensor reads or timekeeping itself.
    """

    def __init__(self, config: Mapping[str, Any]) -> None:
        """
        Initialise the SSD1306 I2C OLED display.

        Args:
            config: Display-specific configuration mapping. Supported keys:
                - width (int): Display width in pixels (default: 128)
                - height (int): Display height in pixels (default: 32)
                - address (int): I2C address of the display (default: 0x3C)
        """
        super().__init__(config)
        self._logger = logging.getLogger("display.ssd1306")

        self._width = int(config.get("width", 128))
        self._height = int(config.get("height", 32))
        self._address = int(config.get("address", 0x3C))

        try:
            i2c = busio.I2C(board.SCL, board.SDA)
            self._oled = adafruit_ssd1306.SSD1306_I2C(
                self._width,
                self._height,
                i2c,
                addr=self._address,
            )

            self._oled.fill(0)
            self._oled.show()

            self._image = Image.new("1", (self._width, self._height))
            self._draw = ImageDraw.Draw(self._image)
            self._font = ImageFont.load_default()

            self._line_height = 10

            self._logger.info(
                "SSD1306 OLED initialised (%sx%s @ 0x%X)",
                self._width,
                self._height,
                self._address,
            )

        except Exception:
            self._logger.error(
                "Failed to initialise SSD1306 I2C OLED display",
                exc_info=True,
            )
            raise

    def _draw_centered_text(self, text: str, center_x: int, y: int) -> None:
        """
        Draw text horizontally centered around a given x coordinate.

        Args:
            text: Text to render.
            center_x: Horizontal center point in pixels.
            y: Vertical position in pixels.
        """
        bbox = self._draw.textbbox((0, 0), text, font=self._font)
        text_width = bbox[2] - bbox[0]
        x = int(center_x - text_width / 2)
        self._draw.text((x, y), text, font=self._font, fill=255)

    def render(self, snapshot: Mapping[str, Any]) -> None:
        """
        Render a telemetry snapshot to the OLED display.

        Expected snapshot structure:
            {
                "ts": int | float | datetime,
                "values": {
                    "water_temperature": float,
                    "air_temperature": float,
                    "air_humidity": float
                }
            }

        Rendering is skipped if the configured refresh period has not elapsed.
        """

        if not self._should_render():
            return

        try:
            status = DisplayStatus.from_snapshot(snapshot)

            self._draw.rectangle((0, 0, self._width, self._height), outline=0, fill=0)

            self._logger.info(
                "OLED update | water_temperature=%s | air_temperature=%s | air_humidity=%s",
                status.water_temperature,
                status.air_temperature,
                status.air_humidity,
            )

            col_centers = [21, 64, 107]

            label_y = 0
            value_y = 10
            time_y = 22

            labels = ["Water", "Air", "Humidity"]
            for label, cx in zip(labels, col_centers):
                self._draw_centered_text(label, cx, label_y)

            water_text = f"{status.water_temperature:.1f}°C" if status.water_temperature is not None else "--°C"
            air_text = f"{status.air_temperature:.1f}°C" if status.air_temperature is not None else "--°C"
            humidity_text = f"{status.air_humidity:.0f}%" if status.air_humidity is not None else "--%"

            values = [water_text, air_text, humidity_text]
            for value, cx in zip(values, col_centers):
                self._draw_centered_text(value, cx, value_y)

            timestamp_ms = status.timestamp_utc
            if timestamp_ms:
                timestamp_ms_dt = datetime.fromtimestamp(timestamp_ms / 1000)
                timestamp = timestamp_ms_dt.strftime("%H:%M %d/%m/%Y")
            else:
                timestamp = "--:-- --/--/----"

            bbox = self._draw.textbbox((0, 0), timestamp, font=self._font)
            timestamp_ms_width = bbox[2] - bbox[0]
            timestamp_ms_x = int((self._width - timestamp_ms_width) / 2)
            self._draw.text((timestamp_ms_x, time_y), timestamp, font=self._font, fill=255)

            self._oled.image(self._image)
            self._oled.show()

        except Exception:
            self._logger.warning(
                "Failed to render snapshot on SSD1306 OLED display",
                exc_info=True,
            )

    def render_startup(self, message: str) -> None:
        """
        Render a bootstrap progress message centred on the OLED display.

        Args:
            message: Short status string to display.
        """
        try:
            self._draw.rectangle((0, 0, self._width, self._height), outline=0, fill=0)

            bbox = self._draw.textbbox((0, 0), message, font=self._font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = max(0, (self._width - text_width) // 2)
            y = max(0, (self._height - text_height) // 2)
            self._draw.text((x, y), message, font=self._font, fill=255)

            self._oled.image(self._image)
            self._oled.show()

        except Exception:
            self._logger.warning(
                "Failed to render startup message on SSD1306 OLED display",
                exc_info=True,
            )

    def close(self) -> None:
        """Clear the OLED display and release hardware resources."""
        try:
            self._oled.fill(0)
            self._oled.show()
        except Exception:
            self._logger.warning("Failed to close SSD1306 display", exc_info=True)
