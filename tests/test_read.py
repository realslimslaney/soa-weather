"""Tests for soa_weather.read — parsing functions."""

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import polars as pl
import pytest

from soa_weather.read import _is_stale, _parse_stations_csv, _parse_stations_txt, load_countries

# ---------------------------------------------------------------------------
# load_countries
# ---------------------------------------------------------------------------


@pytest.fixture()
def countries_file(tmp_path: Path) -> Path:
    path = tmp_path / "ghcnd-countries.txt"
    path.write_text("US United States\nCA Canada\nMX Mexico\n")
    return path


def test_load_countries_columns(countries_file):
    df = load_countries(countries_file)
    assert df.columns == ["country_code", "country_name"]


def test_load_countries_values(countries_file):
    df = load_countries(countries_file)
    assert df.shape[0] == 3
    row = df.filter(pl.col("country_code") == "US")
    assert row["country_name"].item() == "United States"


def test_load_countries_skips_blank_lines(tmp_path: Path):
    path = tmp_path / "countries.txt"
    path.write_text("US United States\n\nCA Canada\n")
    df = load_countries(path)
    assert df.shape[0] == 2


# ---------------------------------------------------------------------------
# _parse_stations_txt
# ---------------------------------------------------------------------------

# Fixed-width layout (1-indexed in the spec, 0-indexed in code):
#   ID(1-11) LAT(13-20) LON(22-30) ELEV(32-37) STATE(39-40) NAME(42-71)

STATIONS_TXT_LINE = "USW00094728  40.7789  -73.9692   39.6 NY NEW YORK CENTRAL PARK OBS      "


@pytest.fixture()
def stations_txt_file(tmp_path: Path) -> Path:
    path = tmp_path / "ghcnd-stations.txt"
    path.write_text(STATIONS_TXT_LINE + "\n")
    return path


def test_parse_stations_txt_columns(stations_txt_file):
    df = _parse_stations_txt(stations_txt_file)
    assert "station_id" in df.columns
    assert "latitude" in df.columns
    assert "longitude" in df.columns
    assert "elevation" in df.columns
    assert "state" in df.columns
    assert "station_name" in df.columns


def test_parse_stations_txt_values(stations_txt_file):
    df = _parse_stations_txt(stations_txt_file)
    assert df["station_id"].item() == "USW00094728"
    assert df["latitude"].item() == pytest.approx(40.78, abs=0.01)
    assert df["longitude"].item() == pytest.approx(-73.97, abs=0.01)
    assert df["elevation"].item() == 39
    assert df["state"].item() == "NY"
    assert "NEW YORK" in df["station_name"].item()


def test_parse_stations_txt_dtypes(stations_txt_file):
    df = _parse_stations_txt(stations_txt_file)
    assert df["latitude"].dtype == pl.Float64
    assert df["longitude"].dtype == pl.Float64
    assert df["elevation"].dtype == pl.Int64
    assert df["station_id"].dtype == pl.Utf8


# ---------------------------------------------------------------------------
# _parse_stations_csv
# ---------------------------------------------------------------------------


@pytest.fixture()
def stations_csv_file(tmp_path: Path) -> Path:
    path = tmp_path / "ghcnd-stations.csv"
    path.write_text("USW00094728,40.7789,-73.9692,39.6,NY,NEW YORK CENTRAL PARK OBS,,,\n")
    return path


def test_parse_stations_csv_columns(stations_csv_file):
    df = _parse_stations_csv(stations_csv_file)
    expected = ["station_id", "latitude", "longitude", "elevation", "state", "station_name"]
    assert df.columns == expected


def test_parse_stations_csv_values(stations_csv_file):
    df = _parse_stations_csv(stations_csv_file)
    assert df["station_id"].item() == "USW00094728"
    assert df["latitude"].item() == pytest.approx(40.78, abs=0.01)
    assert df["longitude"].item() == pytest.approx(-73.97, abs=0.01)
    assert df["elevation"].item() == 39
    assert df["state"].item() == "NY"


def test_parse_stations_csv_dtypes(stations_csv_file):
    df = _parse_stations_csv(stations_csv_file)
    assert df["latitude"].dtype == pl.Float64
    assert df["longitude"].dtype == pl.Float64
    assert df["elevation"].dtype == pl.Int64


# ---------------------------------------------------------------------------
# _is_stale
# ---------------------------------------------------------------------------


def test_is_stale_old_file(tmp_path: Path):
    path = tmp_path / "old.txt"
    path.write_text("data")
    old_time = (datetime.now(tz=timezone.utc) - timedelta(days=60)).timestamp()
    os.utime(path, (old_time, old_time))
    assert _is_stale(path) is True


def test_is_stale_fresh_file(tmp_path: Path):
    path = tmp_path / "fresh.txt"
    path.write_text("data")
    assert _is_stale(path) is False
