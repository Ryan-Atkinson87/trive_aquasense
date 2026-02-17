"""
agent.py

Defines the MonitoringAgent class, responsible for running the main monitoring
loop. The agent periodically collects telemetry and device attributes and sends
them through the configured ThingsBoard client.

Classes:
    MonitoringAgent

Usage:
    agent = MonitoringAgent(...)
    agent.start()  # starts the blocking monitoring loop
"""

import logging
import time

from monitoring_service.inputs.input_manager import InputManager
from monitoring_service.outputs.output_manager import OutputManager
from monitoring_service.attributes import AttributesCollector
from monitoring_service.TBClientWrapper import TBClientWrapper


class MonitoringAgent:
    """
    MonitoringAgent runs the main monitoring loop. It periodically collects telemetry
    and device attributes and forwards both to the ThingsBoard client.

    Args:
        logger: Logger instance.
        input_manager: Collects telemetry from configured sensors.
        attributes_collector: Collects static and dynamic device attributes.
        tb_client: Client used to send telemetry and attributes.
        output_manager: Renders telemetry snapshots to configured displays.
        poll_period: Seconds between each loop iteration.
    """

    def __init__(
        self,
        logger: logging.Logger,
        input_manager: InputManager,
        attributes_collector: AttributesCollector,
        tb_client: TBClientWrapper,
        output_manager: OutputManager,
        poll_period: int = 60,
    ) -> None:
        self._logger = logger
        self._input_manager = input_manager
        self._attributes_collector = attributes_collector
        self._tb_client = tb_client
        self._output_manager = output_manager
        self._poll_period = poll_period

    def start(self) -> None:
        """
        Start and run the blocking monitoring loop.

        On each iteration the agent:
          1) collects telemetry from input_manager,
          2) collects attributes from attributes_collector,
          3) forwards both to the ThingsBoard client,
          4) sleeps for `poll_period` seconds minus the cycle runtime.

        This method blocks indefinitely and logs progress. Exceptions raised by
        the collectors or tb_client will propagate to the caller.
        """

        self._logger.info("MonitoringAgent started.")
        while True:
            start_time = time.time()
            self._read_and_send_telemetry()
            self._read_and_send_attributes()
            end_time = time.time()
            elapsed = end_time - start_time
            delay = max(0, int(self._poll_period - elapsed))
            time.sleep(delay)

    def _read_and_send_telemetry(self) -> None:
        """
        Collect telemetry and send it to the ThingsBoard client.

        Also renders the telemetry snapshot to all configured outputs.
        """
        values = self._input_manager.collect()

        if not values:
            self._logger.debug("No sensors due this cycle.")
            return

        self._logger.info(f"Collected telemetry: {values}")

        self._tb_client.send_telemetry(values)
        self._logger.info("Telemetry sent.")

        snapshot = {
            "ts": int(time.time() * 1000),
            "device_name": self._attributes_collector.device_name,
            "values": values,
        }
        self._output_manager.render(snapshot)

    def _read_and_send_attributes(self) -> None:
        """
        Collect device attributes and send them to the ThingsBoard client.
        """
        self._logger.info("Reading attributes...")
        attributes = self._attributes_collector.as_dict()
        self._logger.info(f"Collected attributes: {attributes}")

        self._logger.info("Sending attributes...")
        self._tb_client.send_attributes(attributes)
        self._logger.info("Attributes sent.")