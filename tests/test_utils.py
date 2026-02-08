"""Tests for soa_weather.utils."""

import platform
from pathlib import Path

from soa_weather.utils import data_dir


def test_data_dir_returns_path():
    result = data_dir()
    assert isinstance(result, Path)
    assert result.parts[-1] == "SOA_Weather"


def test_data_dir_platform_default():
    result = data_dir()
    if platform.system() == "Windows":
        assert str(result) == "C:\\Data\\SOA_Weather"
    else:
        assert result == Path.home() / "Data" / "SOA_Weather"


def test_data_dir_env_override(monkeypatch):
    monkeypatch.setenv("SOA_WEATHER_DATA", "/tmp/custom")
    result = data_dir()
    assert result == Path("/tmp/custom")
