"""
thingsboard_client.py

Provides the ThingsboardClient class, a thin wrapper around the ThingsBoard MQTT
client. It manages connection setup and exposes methods for sending telemetry
and attribute data.

Classes:
    ThingsboardClient
"""

import time

from tb_device_mqtt import TBDeviceMqttClient


def _safe_log(logger, level: str, message: str) -> None:
    if logger is None:
        return
    fn = getattr(logger, level.lower(), None)
    if callable(fn):
        try:
            fn(message)
        except Exception:
            pass


class ThingsboardClient:
    """
    Wrap the ThingsBoard MQTT client and provide helper methods for connecting,
    sending telemetry and attributes, and disconnecting.
    """

    def __init__(
        self,
        tb_server,
        tb_token,
        logger,
        client_class=TBDeviceMqttClient,
        max_retries: int = 3,
        retry_base_delay: float = 1.0,
    ):
        self.logger = logger
        self.client = client_class(tb_server, username=tb_token)
        self._max_retries = max_retries
        self._retry_base_delay = retry_base_delay

    def _send_with_retry(self, send_fn, payload, description: str) -> None:
        """
        Attempt to call send_fn(payload), retrying with exponential back-off on
        failure up to self._max_retries additional attempts.
        """
        last_exc = None
        for attempt in range(self._max_retries + 1):
            try:
                send_fn(payload)
                return
            except Exception as e:
                last_exc = e
                if attempt < self._max_retries:
                    delay = self._retry_base_delay * (2 ** attempt)
                    _safe_log(
                        self.logger,
                        "warning",
                        f"Failed to send {description} "
                        f"(attempt {attempt + 1}/{self._max_retries + 1}): {e}. "
                        f"Retrying in {delay:.1f}s",
                    )
                    time.sleep(delay)
        _safe_log(
            self.logger,
            "error",
            f"Failed to send {description} after {self._max_retries + 1} attempt(s): {last_exc}",
        )

    def connect(self):
        """
        Establish a connection to the ThingsBoard server.
        """
        try:
            self.client.connect()
            _safe_log(self.logger, "info", "Connected to ThingsBoard.")
        except Exception as e:
            _safe_log(self.logger, "error", f"Could not connect to ThingsBoard server: {e}")
            raise

    def send_telemetry(self, telemetry: dict):
        """
        Send a telemetry payload to ThingsBoard.

        Empty payloads are logged and skipped. Transient failures are retried
        with exponential back-off up to max_retries times.
        """
        if not telemetry:
            _safe_log(self.logger, "warning", "Telemetry data is empty. Skipping send.")
            return
        self._send_with_retry(self.client.send_telemetry, telemetry, "telemetry")

    def send_attributes(self, attributes: dict):
        """
        Send an attributes payload to ThingsBoard.

        Empty payloads are logged and skipped. Transient failures are retried
        with exponential back-off up to max_retries times.
        """
        if not attributes:
            _safe_log(self.logger, "warning", "Attributes data is empty. Skipping send.")
            return
        self._send_with_retry(self.client.send_attributes, attributes, "attributes")

    def disconnect(self):
        """
        Disconnect from the ThingsBoard server.
        """
        try:
            self.client.disconnect()
            _safe_log(self.logger, "info", "Disconnected from ThingsBoard.")
        except Exception as e:
            _safe_log(self.logger, "error", f"Failed to disconnect ThingsBoard: {e}")
            raise
