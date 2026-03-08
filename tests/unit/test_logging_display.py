import logging

from monitoring_service.outputs.display.logging_display import LoggingDisplay
from monitoring_service.outputs.display.models import DisplayContent


def test_logging_display_renders_content(caplog):
    config = {
        "enabled": True,
        "refresh_period": 0,
    }

    display = LoggingDisplay(config)

    content = DisplayContent(
        lines=["test_device", "WATER:25.1C", "AIR:22.3C", "HUMID:60.0%"],
        timestamp_str="12:34 08/03/2026",
    )

    with caplog.at_level(logging.INFO):
        display.render(content)

    assert "WATER:25.1C" in caplog.text
    assert "AIR:22.3C" in caplog.text
    assert "ts=12:34 08/03/2026" in caplog.text


def test_logging_display_renders_empty_content(caplog):
    config = {
        "enabled": True,
        "refresh_period": 0,
    }

    display = LoggingDisplay(config)
    content = DisplayContent(lines=[], timestamp_str="")

    with caplog.at_level(logging.INFO):
        display.render(content)

    assert "Display update" in caplog.text


def test_logging_display_respects_refresh_period(caplog):
    config = {
        "enabled": True,
        "refresh_period": 9999,
    }

    display = LoggingDisplay(config)
    content = DisplayContent(lines=["WATER:25.1C"], timestamp_str="12:34 08/03/2026")

    # First render arms the timer
    display.render(content)
    caplog.clear()

    # Second render within the refresh period should be skipped
    with caplog.at_level(logging.INFO):
        display.render(content)

    assert "Display update" not in caplog.text