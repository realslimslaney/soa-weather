"""Tests for soa_weather.write."""

from pathlib import Path

import polars as pl

from soa_weather.write import write_stations_csv


def test_write_stations_csv_roundtrip(tmp_path: Path):
    df = pl.DataFrame(
        {
            "station_id": ["USW00094728"],
            "latitude": [40.78],
            "longitude": [-73.97],
        }
    )
    out = tmp_path / "out.csv"
    write_stations_csv(df, out)

    assert out.exists()
    result = pl.read_csv(out)
    assert result.shape == df.shape
    assert result["station_id"].item() == "USW00094728"


def test_write_stations_csv_creates_file(tmp_path: Path):
    df = pl.DataFrame({"a": [1, 2, 3]})
    out = tmp_path / "test.csv"
    write_stations_csv(df, out)
    assert out.exists()
    assert out.stat().st_size > 0
