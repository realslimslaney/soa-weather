"""Tests for soa_weather.schema — sanity-check the declared schemas."""

import polars as pl

from soa_weather.schema import COUNTRIES_SCHEMA, STATIONS_SCHEMA


def test_countries_schema_columns():
    assert COUNTRIES_SCHEMA.names() == ["country_code", "country_name"]


def test_countries_schema_dtypes():
    assert all(dtype == pl.String for dtype in COUNTRIES_SCHEMA.dtypes())


def test_stations_schema_columns():
    expected = [
        "country_code",
        "country_name",
        "state",
        "station_id",
        "station_name",
        "latitude",
        "longitude",
        "elevation",
    ]
    assert STATIONS_SCHEMA.names() == expected


def test_stations_schema_dtypes():
    assert STATIONS_SCHEMA["latitude"] == pl.Float64
    assert STATIONS_SCHEMA["longitude"] == pl.Float64
    assert STATIONS_SCHEMA["elevation"] == pl.Int64
    assert STATIONS_SCHEMA["station_id"] == pl.String
