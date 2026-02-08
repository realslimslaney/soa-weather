"""CLI entry point for soa-weather."""

import logging
import time

from .config import setup_logging
from .read import check_and_download, load_countries, load_stations
from .utils import data_dir
from .write import write_stations_csv

BASE_URL = "https://www.ncei.noaa.gov/pub/data/ghcn/daily/"

log = logging.getLogger(__name__)


def main() -> None:
    """Download GHCN-Daily data, build the station list, and write output CSV."""
    setup_logging()

    data = data_dir()
    station_file = data / "ghcnd-stations.txt"
    country_file = data / "ghcnd-countries.txt"
    tar_file = data / "ghcnd_all.tar.gz"
    dly_subdir = data / "ghcnd_all"
    output_file = data / "stations_output.csv"

    files_to_download = [
        ("ghcnd-stations.txt", station_file),
        ("ghcnd-countries.txt", country_file),
        ("ghcnd_all.tar.gz", tar_file),
    ]

    log.info("=" * 60)
    log.info("GHCN-Daily Station Loader")
    log.info("Data directory: %s", data)
    log.info("Source:         %s", BASE_URL)
    log.info("=" * 60)

    # Download & extract (skips anything already present)
    check_and_download(BASE_URL, data, files_to_download, tar_file, dly_subdir)

    # Build station list
    log.info("Loading country lookup...")
    countries = load_countries(country_file)

    log.info("Parsing station metadata & filtering...")
    start = time.time()
    stations = load_stations(station_file, dly_subdir, countries)
    elapsed = round(time.time() - start, 1)

    # Save output
    write_stations_csv(stations, output_file)

    log.info("Stations loaded: %s", f"{stations.height:,}")
    log.info("Runtime (parse + filter): %s seconds", elapsed)
    log.info("Done!")
