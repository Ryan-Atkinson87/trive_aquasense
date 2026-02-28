"""
main.py

Bootstrap entry point for the monitoring service. Loads configuration, sets up
logging, constructs input and output managers, initializes the ThingsBoard
client, and starts the monitoring agent.
"""

import logging
from monitoring_service.__version__ import __version__
from monitoring_service.config_loader import ConfigLoader
from monitoring_service.logging_setup import setup_logging
from monitoring_service.inputs.input_manager import InputManager
from monitoring_service.outputs.output_manager import OutputManager
from monitoring_service.outputs.display.factory import build_displays
from monitoring_service.attributes import AttributesCollector
from monitoring_service.TBClientWrapper import TBClientWrapper
from monitoring_service.agent import MonitoringAgent


def main():
    """
    Initialize and start the monitoring service.

    This function loads configuration, configures logging, builds the input
    and output managers, wires the ThingsBoard client, and starts the
    MonitoringAgent.
    """
    bootstrap_logger = logging.getLogger("bootstrap")
    bootstrap_logger.setLevel(logging.INFO)
    bootstrap_logger.addHandler(logging.StreamHandler())

    bootstrap_logger.info(f"Trive Aquasense v{__version__}")

    config = ConfigLoader(logger=bootstrap_logger).as_dict()

    logger = setup_logging(
        log_dir="log",
        log_file_name="monitoring_service.log",
        log_level=config["log_level"],
    )

    sensors_config = config.get("sensors", [])
    if not isinstance(sensors_config, list) or not sensors_config:
        raise RuntimeError("Config missing a non-empty 'sensors' list")

    input_manager = InputManager(
        sensors_config=sensors_config,
        logger=logger,
    )

    displays = build_displays(
        displays_config=config.get("displays", []),
        logger=logger,
    )
    output_manager = OutputManager(outputs=displays, logger=logger)
    output_manager.render_startup(f"Aquasense v{__version__}")

    server = config["server"]
    token = config["token"]
    poll_period = config["poll_period"]
    device_name = config["device_name"]

    attributes_collector = AttributesCollector(device_name, logger)
    client = TBClientWrapper(server, token, logger)

    agent = MonitoringAgent(
        logger=logger,
        input_manager=input_manager,
        attributes_collector=attributes_collector,
        tb_client=client,
        output_manager=output_manager,
        poll_period=poll_period,
    )

    output_manager.render_startup("Connecting...")
    client.connect()
    output_manager.render_startup("Connected")

    try:
        agent.start()
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user.")
    finally:
        output_manager.close()
        client.disconnect()


if __name__ == "__main__":
    main()