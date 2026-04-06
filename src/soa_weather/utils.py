"""Shared utility helpers for soa-weather."""

import platform
from pathlib import Path

import polars as pl

# ── Unit conversion expressions ──────────────────────────────────────────────
# Each function accepts and returns a pl.Expr, composing naturally inside
# .with_columns() either as a direct call or via .pipe():
#
#   df.with_columns(celsius_to_fahrenheit(pl.col("tmax")).alias("tmax_f"))
#   df.with_columns(pl.col("prcp").pipe(tenths_to_unit).pipe(mm_to_inches).alias("prcp_in"))


def tenths_to_unit(expr: pl.Expr) -> pl.Expr:
    """Divide by 10 to convert NOAA tenths-of-unit storage to the base unit.

    NOAA stores TMAX, TMIN, TAVG as tenths of °C and PRCP as tenths of mm.
    """
    return expr / 10


def celsius_to_fahrenheit(expr: pl.Expr) -> pl.Expr:
    """Convert °C to °F."""
    return expr * 9 / 5 + 32


def fahrenheit_to_celsius(expr: pl.Expr) -> pl.Expr:
    """Convert °F to °C."""
    return (expr - 32) * 5 / 9


def mm_to_inches(expr: pl.Expr) -> pl.Expr:
    """Convert millimetres to inches."""
    return expr / 25.4


def inches_to_mm(expr: pl.Expr) -> pl.Expr:
    """Convert inches to millimetres."""
    return expr * 25.4


# ── Platform paths ────────────────────────────────────────────────────────────


def data_dir() -> Path:
    """Return the default data directory for the current platform.

    - Windows: ``C:/Data/SOA_Weather``
    - macOS / Linux: ``~/Data/SOA_Weather``

    Override by setting the ``SOA_WEATHER_DATA`` environment variable
    (or in a ``.env`` file — see ``.env.example``).

    The directory is created automatically if it does not already exist.
    """
    import os

    env = os.environ.get("SOA_WEATHER_DATA")
    if env:
        p = Path(env)
    elif platform.system() == "Windows":
        p = Path("C:/Data/SOA_Weather")
    else:
        p = Path.home() / "Data" / "SOA_Weather"

    p.mkdir(parents=True, exist_ok=True)
    return p
