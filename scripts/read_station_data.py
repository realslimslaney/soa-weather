"""Python script to replace the Excel Macro to read station data from a text file."""

import logging
import time

from soa_weather.config import setup_logging
from soa_weather.read import check_and_download, load_countries, load_stations
from soa_weather.utils import data_dir
from soa_weather.write import write_stations_csv

# ══════════════════════════════════════════════════════════════════════════════
# USER CONFIGURATION — update these as needed
# ══════════════════════════════════════════════════════════════════════════════
BASE_URL = "https://www.ncei.noaa.gov/pub/data/ghcn/daily/"
DATA_DIR = data_dir()
# ══════════════════════════════════════════════════════════════════════════════

# Derived paths
STATION_LIST_FILE = DATA_DIR / "ghcnd-stations.txt"
COUNTRY_LOOKUP_FILE = DATA_DIR / "ghcnd-countries.txt"
TAR_FILE = DATA_DIR / "ghcnd_all.tar.gz"
DLY_SUBDIR = DATA_DIR / "ghcnd_all"
OUTPUT_FILE = DATA_DIR / "stations_output.csv"

FILES_TO_DOWNLOAD = [
    ("ghcnd-stations.txt", STATION_LIST_FILE),
    ("ghcnd-countries.txt", COUNTRY_LOOKUP_FILE),
    ("ghcnd_all.tar.gz", TAR_FILE),
]

log = logging.getLogger(__name__)

# ── Main ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    setup_logging()

    log.info("=" * 60)
    log.info("GHCN-Daily Station Loader")
    log.info("Data directory: %s", DATA_DIR)
    log.info("Source:         %s", BASE_URL)
    log.info("=" * 60)

    # Download & extract (skips anything already present)
    check_and_download(BASE_URL, DATA_DIR, FILES_TO_DOWNLOAD, TAR_FILE, DLY_SUBDIR)

    # Build station list
    log.info("Loading country lookup...")
    countries = load_countries(COUNTRY_LOOKUP_FILE)

    log.info("Parsing station metadata & filtering...")
    start = time.time()
    result = load_stations(STATION_LIST_FILE, DLY_SUBDIR, countries)
    elapsed = round(time.time() - start, 1)

    # Save output
    write_stations_csv(result, OUTPUT_FILE)

    log.info("Stations loaded: %s", f"{result.height:,}")
    log.info("Runtime (parse + filter): %s seconds", elapsed)
    log.info("Done!")
