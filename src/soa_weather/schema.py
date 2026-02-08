"""Schemas for common datasets to validate the data and to provide metadata for the datasets."""

from polars import Float64, Int64, Schema, String

COUNTRIES_SCHEMA = Schema(
    {
        "country_code": String,
        "country_name": String,
    }
)

STATIONS_SCHEMA = Schema(
    {
        "country_code": String,
        "country_name": String,
        "state": String,
        "station_id": String,
        "station_name": String,
        "latitude": Float64,
        "longitude": Float64,
        "elevation": Int64,
    }
)
