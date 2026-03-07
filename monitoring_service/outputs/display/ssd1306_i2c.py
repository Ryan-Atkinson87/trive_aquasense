"""
ssd1306_i2c.py

Provides an SSD1306 I2C OLED display implementation for rendering telemetry
snapshots using the Adafruit SSD1306 driver and PIL for text layout.

Normal mode (system_screen=False) renders a fixed 3-row telemetry layout:
  - Row 1: Metric labels (Water | Air | Humidity)
  - Row 2: Metric values with units
  - Row 3: Timestamp of last telemetry update

System-screen mode (system_screen=True) renders a persistent status layout:
  - Row 1: Version header (e.g. "Aquasense v2.6.0") — fixed
  - Row 2: Second-most-recent system message
  - Row 3: Most recent system message
In this mode render() is a no-op; all updates arrive via render_startup().
"""

import logging
from collections import deque
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

            self._header: str = config.get("_version_header", "Aquasense")
            self._messages: deque[str] = deque(maxlen=2)

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
        In system-screen mode this method is a no-op.
        """

        if self._system_screen:
            return

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

            col_width = self._width / 3
            col_centers = [
                int(col_width * 0.5),
                int(col_width * 1.5),
                int(col_width * 2.5),
            ]

            label_y = 0
            value_y = self._height // 3
            time_y = self._height - self._height // 3

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
        Render a system/startup message to the OLED display.

        In system-screen mode the display shows a fixed header on row 1 and
        scrolls the last two messages on rows 2 and 3.

        In normal mode the message is centred on the display (single-message
        startup splash).

        Args:
            message: Short status string to display.
        """
        try:
            if self._system_screen:
                self._messages.append(message)
                self._draw_system_screen()
            else:
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

    def _draw_system_screen(self) -> None:
        """
        Draw the 3-row system-screen layout and push it to the hardware.

        Row 1 (y=0):  version header (fixed)
        Row 2 (y=11): second-most-recent message (blank until two messages exist)
        Row 3 (y=22): most recent message
        """
        row_step = self._height // 3

        self._draw.rectangle((0, 0, self._width, self._height), outline=0, fill=0)
        self._draw.text((0, 0), self._header, font=self._font, fill=255)

        msgs = list(self._messages)
        if len(msgs) == 2:
            self._draw.text((0, row_step), msgs[0], font=self._font, fill=255)
        if msgs:
            self._draw.text((0, row_step * 2), msgs[-1], font=self._font, fill=255)

        self._oled.image(self._image)
        self._oled.show()

    def close(self) -> None:
        """Clear the OLED display and release hardware resources."""
        try:
            self._oled.fill(0)
            self._oled.show()
        except Exception:
            self._logger.warning("Failed to close SSD1306 display", exc_info=True)
