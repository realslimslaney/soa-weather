"""Functions for writing GHCN-Daily data to disk."""

import logging
from pathlib import Path

import polars as pl

log = logging.getLogger(__name__)


def write_stations_csv(df: pl.DataFrame, output_file: Path) -> None:
    """Write the stations DataFrame to a CSV file and log a preview."""
    df.write_csv(output_file)
    log.info("Output saved to: %s", output_file)
    log.info("Preview:\n%s", df)
