"""Data cleaning functions for GHCN-Daily observations."""

from typing import Literal

import polars as pl

from soa_weather.utils import celsius_to_fahrenheit, mm_to_inches, tenths_to_unit


def clean_ghcn_daily_observations(
    df: pl.DataFrame,
    system: Literal["metric", "imperial"] = "metric",
) -> pl.DataFrame:
    """Convert raw NOAA integer observation values to standard units.

    NOAA stores values as integers in the following raw units:

    - TMAX, TMIN, TAVG: tenths of °C
    - PRCP:             tenths of mm
    - SNOW, SNWD:       mm (not tenths)
    - All other elements are passed through unchanged.

    Parameters
    ----------
    df : pl.DataFrame
        Long-format observations with ``element`` and ``value`` columns,
        as returned by ``parse_dly`` or ``load_station_observations``.
    system : {"metric", "imperial"}
        Target unit system:

        - ``"metric"``:   temperatures → °C, precipitation/snow → mm
        - ``"imperial"``: temperatures → °F, precipitation/snow → inches

    Returns
    -------
    pl.DataFrame
        DataFrame with ``value`` cast to Float64 and converted in-place.

    Examples
    --------
    >>> obs = load_station_observations(station_ids, dly_subdir)
    >>> obs_metric = clean_ghcn_daily_observations(obs, system="metric")
    >>> obs_imperial = clean_ghcn_daily_observations(obs, system="imperial")
    """
    temp_elements = ["TMAX", "TMIN", "TAVG"]
    prcp_elements = ["PRCP", "MDPR", "DAPR"]
    snow_elements = ["SNOW", "SNWD"]

    if system == "metric":
        converted = (
            pl.when(pl.col("element").is_in(temp_elements + prcp_elements))
            .then(tenths_to_unit(pl.col("value").cast(pl.Float64)))
            .otherwise(pl.col("value").cast(pl.Float64))
            .alias("value")
        )
    else:
        converted = (
            pl.when(pl.col("element").is_in(temp_elements))
            .then(celsius_to_fahrenheit(tenths_to_unit(pl.col("value").cast(pl.Float64))))
            .when(pl.col("element").is_in(prcp_elements))
            .then(mm_to_inches(tenths_to_unit(pl.col("value").cast(pl.Float64))))
            .when(pl.col("element").is_in(snow_elements))
            .then(mm_to_inches(pl.col("value").cast(pl.Float64)))
            .otherwise(pl.col("value").cast(pl.Float64))
            .alias("value")
        )

    return df.with_columns(converted)


def filter_ghcn_quality_flags(df: pl.DataFrame) -> pl.DataFrame:
    """Remove observations that failed NOAA quality assurance checks.

    Drops rows where ``qflag`` is not blank. A blank qflag means the observation
    passed all QA checks; any other character indicates a flagged (suspect or
    erroneous) value.

    Parameters
    ----------
    df : pl.DataFrame
        Long-format observations with a ``qflag`` column,
        as returned by ``parse_dly`` or ``load_station_observations``.

    Returns
    -------
    pl.DataFrame
        DataFrame with QA-failed rows removed.
    """
    return df.filter(pl.col("qflag") == " ")
