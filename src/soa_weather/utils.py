"""Shared utility helpers for soa-weather."""

import platform
from pathlib import Path


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
