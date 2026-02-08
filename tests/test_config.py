"""Tests for soa_weather.config."""

import logging

from soa_weather.config import setup_logging


def test_setup_logging_creates_handler():
    logger = logging.getLogger("soa_weather")
    logger.handlers.clear()

    setup_logging()
    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], logging.StreamHandler)


def test_setup_logging_no_duplicate_handlers():
    logger = logging.getLogger("soa_weather")
    logger.handlers.clear()

    setup_logging()
    setup_logging()
    assert len(logger.handlers) == 1


def test_setup_logging_level():
    logger = logging.getLogger("soa_weather")
    logger.handlers.clear()

    setup_logging(level=logging.DEBUG)
    assert logger.level == logging.DEBUG
