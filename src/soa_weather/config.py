"""Logging configuration for soa-weather."""

import logging
import sys


def setup_logging(level: int = logging.INFO) -> None:
    """Configure the root ``soa_weather`` logger.

    Sends INFO+ messages to *stdout* with a clean, readable format.
    Call once at program startup (e.g. in a script's ``if __name__`` block).
    """
    logger = logging.getLogger("soa_weather")
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
