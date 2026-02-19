import os
import logging
import pytest
from monitoring_service.logging_setup import setup_logging


@pytest.fixture(autouse=True)
def clean_root_handlers():
    """Remove all root logger handlers before and after each test."""
    root = logging.getLogger()
    original_handlers = root.handlers[:]
    root.handlers.clear()
    yield
    root.handlers.clear()
    root.handlers.extend(original_handlers)


def test_creates_log_directory(tmp_path):
    log_dir = str(tmp_path / "logs")
    setup_logging(log_dir=log_dir, log_file_name="test.log")
    assert os.path.isdir(log_dir)


def test_returns_root_logger(tmp_path):
    result = setup_logging(log_dir=str(tmp_path), log_file_name="test.log")
    assert isinstance(result, logging.Logger)


def test_log_level_is_set(tmp_path):
    setup_logging(log_dir=str(tmp_path), log_file_name="test.log", log_level="DEBUG")
    assert logging.getLogger().level == logging.DEBUG


def test_handlers_are_added(tmp_path):
    setup_logging(log_dir=str(tmp_path), log_file_name="test.log")
    assert len(logging.getLogger().handlers) == 2


def test_does_not_add_duplicate_handlers(tmp_path):
    setup_logging(log_dir=str(tmp_path), log_file_name="test.log")
    handler_count = len(logging.getLogger().handlers)
    setup_logging(log_dir=str(tmp_path), log_file_name="test.log")
    assert len(logging.getLogger().handlers) == handler_count