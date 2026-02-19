import logging
from unittest.mock import MagicMock, patch

# Hardware stubs (board, adafruit_dht, tb_device_mqtt, etc.) are set up in
# conftest.py before this module is collected.

from monitoring_service.agent import MonitoringAgent


def make_agent(poll_period=60):
    logger = MagicMock(spec=logging.Logger)
    input_manager = MagicMock()
    attributes_collector = MagicMock()
    attributes_collector.device_name = "test_tank"
    tb_client = MagicMock()
    output_manager = MagicMock()

    agent = MonitoringAgent(
        logger=logger,
        input_manager=input_manager,
        attributes_collector=attributes_collector,
        tb_client=tb_client,
        output_manager=output_manager,
        poll_period=poll_period,
    )
    return agent, logger, input_manager, attributes_collector, tb_client, output_manager


def test_read_and_send_telemetry_with_data():
    agent, _, input_manager, _, tb_client, output_manager = make_agent()
    input_manager.collect.return_value = {"water_temperature": 24.5}

    agent._read_and_send_telemetry()

    tb_client.send_telemetry.assert_called_once_with({"water_temperature": 24.5})
    output_manager.render.assert_called_once()


def test_read_and_send_telemetry_skips_when_empty():
    agent, _, input_manager, _, tb_client, output_manager = make_agent()
    input_manager.collect.return_value = {}

    agent._read_and_send_telemetry()

    tb_client.send_telemetry.assert_not_called()
    output_manager.render.assert_not_called()


def test_read_and_send_attributes():
    agent, _, _, attrs, tb_client, _ = make_agent()
    attrs.as_dict.return_value = {"device_name": "test_tank", "ip_address": "192.168.1.1"}

    agent._read_and_send_attributes()

    tb_client.send_attributes.assert_called_once_with(
        {"device_name": "test_tank", "ip_address": "192.168.1.1"}
    )


def test_render_snapshot_includes_device_name_and_values():
    agent, _, input_manager, _, _, output_manager = make_agent()
    input_manager.collect.return_value = {"water_temperature": 22.0}

    agent._read_and_send_telemetry()

    snapshot = output_manager.render.call_args[0][0]
    assert snapshot["device_name"] == "test_tank"
    assert snapshot["values"] == {"water_temperature": 22.0}
    assert "ts" in snapshot


def test_start_runs_one_cycle_then_breaks():
    agent, _, input_manager, attrs, _, _ = make_agent(poll_period=1)
    input_manager.collect.return_value = {}
    attrs.as_dict.return_value = {}

    with patch("monitoring_service.agent.time.sleep", side_effect=KeyboardInterrupt):
        try:
            agent.start()
        except KeyboardInterrupt:
            pass

    input_manager.collect.assert_called_once()
    attrs.as_dict.assert_called_once()