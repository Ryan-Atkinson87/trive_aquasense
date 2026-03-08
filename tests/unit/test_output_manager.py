import logging
from unittest.mock import MagicMock

from monitoring_service.outputs.output_manager import OutputManager
from monitoring_service.outputs.display.models import DisplayBundle, DisplayContent


def make_logger():
    return MagicMock(spec=logging.Logger)


def make_bundle(show_startup: bool = False, system_screen: bool = False) -> DisplayBundle:
    driver = MagicMock()
    return DisplayBundle(driver=driver, show_startup=show_startup, system_screen=system_screen)


SNAPSHOT = {
    "ts": 1741430040000,
    "device_name": "test_tank",
    "values": {
        "water_temperature": 24.5,
        "air_temperature": 22.1,
        "air_humidity": 61.0,
    },
}


# ---------------------------------------------------------------------------
# render tests
# ---------------------------------------------------------------------------

def test_render_calls_all_non_system_outputs():
    logger = make_logger()
    b1, b2 = make_bundle(), make_bundle()
    manager = OutputManager(outputs=[b1, b2], logger=logger)

    manager.render(SNAPSHOT)

    b1.driver.render.assert_called_once()
    b2.driver.render.assert_called_once()


def test_render_skips_system_screen_outputs():
    logger = make_logger()
    b_telemetry = make_bundle(system_screen=False)
    b_system = make_bundle(system_screen=True)
    manager = OutputManager(outputs=[b_telemetry, b_system], logger=logger)

    manager.render(SNAPSHOT)

    b_telemetry.driver.render.assert_called_once()
    b_system.driver.render.assert_not_called()


def test_render_passes_display_content_to_driver():
    logger = make_logger()
    bundle = make_bundle()
    manager = OutputManager(outputs=[bundle], logger=logger)

    manager.render(SNAPSHOT)

    args, _ = bundle.driver.render.call_args
    content = args[0]
    assert isinstance(content, DisplayContent)
    assert any("WATER" in line for line in content.lines)
    assert any("AIR" in line for line in content.lines)
    assert content.timestamp_str != ""


def test_render_removes_failed_output():
    logger = make_logger()
    b1, b2 = make_bundle(), make_bundle()
    b1.driver.render.side_effect = Exception("hardware error")
    manager = OutputManager(outputs=[b1, b2], logger=logger)

    manager.render(SNAPSHOT)

    assert b1 not in manager._outputs
    assert b2 in manager._outputs
    logger.warning.assert_called_once()


def test_render_with_no_outputs_does_not_raise():
    logger = make_logger()
    manager = OutputManager(outputs=[], logger=logger)
    manager.render(SNAPSHOT)


def test_failed_render_does_not_prevent_remaining_outputs():
    logger = make_logger()
    b1, b2, b3 = make_bundle(), make_bundle(), make_bundle()
    b1.driver.render.side_effect = Exception("fail")
    manager = OutputManager(outputs=[b1, b2, b3], logger=logger)

    manager.render(SNAPSHOT)

    b2.driver.render.assert_called_once()
    b3.driver.render.assert_called_once()


# ---------------------------------------------------------------------------
# _assemble_content tests
# ---------------------------------------------------------------------------

def test_assemble_content_includes_known_values():
    logger = make_logger()
    manager = OutputManager(outputs=[], logger=logger)
    content = manager._assemble_content(SNAPSHOT)

    assert "test_tank" in content.lines
    assert any("WATER:24.5C" in line for line in content.lines)
    assert any("AIR:22.1C" in line for line in content.lines)
    assert any("HUMID:61.0%" in line for line in content.lines)


def test_assemble_content_omits_none_values():
    logger = make_logger()
    manager = OutputManager(outputs=[], logger=logger)
    snapshot = {"ts": 1741430040000, "device_name": "tank", "values": {"water_temperature": None}}
    content = manager._assemble_content(snapshot)

    assert not any("WATER" in line for line in content.lines)


def test_assemble_content_timestamp_fallback_on_missing_ts():
    logger = make_logger()
    manager = OutputManager(outputs=[], logger=logger)
    snapshot = {"device_name": "tank", "values": {}}
    content = manager._assemble_content(snapshot)

    assert content.timestamp_str == "--:-- --/--/----"


def test_assemble_content_formats_water_flow():
    logger = make_logger()
    manager = OutputManager(outputs=[], logger=logger)
    snapshot = {"ts": 1741430040000, "device_name": "tank", "values": {"water_flow": 1.23}}
    content = manager._assemble_content(snapshot)

    assert any("FLOW:1.2L/M" in line for line in content.lines)


# ---------------------------------------------------------------------------
# close tests
# ---------------------------------------------------------------------------

def test_close_calls_all_outputs():
    logger = make_logger()
    b1, b2 = make_bundle(), make_bundle()
    manager = OutputManager(outputs=[b1, b2], logger=logger)

    manager.close()

    b1.driver.close.assert_called_once()
    b2.driver.close.assert_called_once()


def test_close_logs_warning_on_failure_and_does_not_raise():
    logger = make_logger()
    b1 = make_bundle()
    b1.driver.close.side_effect = Exception("close failed")
    manager = OutputManager(outputs=[b1], logger=logger)

    manager.close()

    logger.warning.assert_called_once()


# ---------------------------------------------------------------------------
# render_startup tests
# ---------------------------------------------------------------------------

def test_render_startup_only_calls_opted_in_displays():
    logger = make_logger()
    b_on = make_bundle(show_startup=True)
    b_off = make_bundle(show_startup=False)
    manager = OutputManager(outputs=[b_on, b_off], logger=logger)

    manager.render_startup("Connecting...")

    b_on.driver.render_startup.assert_called_once_with("Connecting...")
    b_off.driver.render_startup.assert_not_called()


def test_render_startup_with_no_opted_in_displays_does_not_raise():
    logger = make_logger()
    b = make_bundle(show_startup=False)
    manager = OutputManager(outputs=[b], logger=logger)

    manager.render_startup("Starting")


def test_render_startup_failure_is_logged_and_does_not_remove_output():
    logger = make_logger()
    b = make_bundle(show_startup=True)
    b.driver.render_startup.side_effect = Exception("hardware error")
    manager = OutputManager(outputs=[b], logger=logger)

    manager.render_startup("Starting")

    logger.warning.assert_called_once()
    assert b in manager._outputs


def test_render_startup_failure_does_not_prevent_remaining_outputs():
    logger = make_logger()
    b1 = make_bundle(show_startup=True)
    b2 = make_bundle(show_startup=True)
    b1.driver.render_startup.side_effect = Exception("fail")
    manager = OutputManager(outputs=[b1, b2], logger=logger)

    manager.render_startup("Starting")

    b2.driver.render_startup.assert_called_once_with("Starting")