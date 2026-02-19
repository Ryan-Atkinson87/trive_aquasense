import logging
from unittest.mock import MagicMock
from monitoring_service.outputs.output_manager import OutputManager


def make_logger():
    return MagicMock(spec=logging.Logger)


def make_display():
    return MagicMock()


def test_render_calls_all_outputs():
    logger = make_logger()
    d1, d2 = make_display(), make_display()
    manager = OutputManager(outputs=[d1, d2], logger=logger)
    snapshot = {"values": {"water_temperature": 24.5}}

    manager.render(snapshot)

    d1.render.assert_called_once_with(snapshot)
    d2.render.assert_called_once_with(snapshot)


def test_render_removes_failed_output():
    logger = make_logger()
    d1, d2 = make_display(), make_display()
    d1.render.side_effect = Exception("hardware error")
    manager = OutputManager(outputs=[d1, d2], logger=logger)

    manager.render({"values": {}})

    assert d1 not in manager._outputs
    assert d2 in manager._outputs
    logger.warning.assert_called_once()


def test_render_with_no_outputs_does_not_raise():
    logger = make_logger()
    manager = OutputManager(outputs=[], logger=logger)
    manager.render({"values": {}})


def test_failed_render_does_not_prevent_remaining_outputs():
    logger = make_logger()
    d1, d2, d3 = make_display(), make_display(), make_display()
    d1.render.side_effect = Exception("fail")
    manager = OutputManager(outputs=[d1, d2, d3], logger=logger)

    manager.render({"values": {}})

    d2.render.assert_called_once()
    d3.render.assert_called_once()


def test_close_calls_all_outputs():
    logger = make_logger()
    d1, d2 = make_display(), make_display()
    manager = OutputManager(outputs=[d1, d2], logger=logger)

    manager.close()

    d1.close.assert_called_once()
    d2.close.assert_called_once()


def test_close_logs_warning_on_failure_and_does_not_raise():
    logger = make_logger()
    d1 = make_display()
    d1.close.side_effect = Exception("close failed")
    manager = OutputManager(outputs=[d1], logger=logger)

    manager.close()

    logger.warning.assert_called_once()