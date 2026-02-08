"""Functions for reading and downloading GHCN-Daily data."""

import logging
import sys
import tarfile
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import polars as pl

log = logging.getLogger(__name__)

STALE_DAYS = 30


def _is_stale(path: Path) -> bool:
    """Return True if *path* was last modified more than STALE_DAYS ago."""
    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    age_days = (datetime.now(tz=timezone.utc) - mtime).days
    return age_days > STALE_DAYS


def _prompt_redownload(path: Path, age_days: int) -> bool:
    """Ask the user whether to re-download a stale file."""
    answer = input(f"  {path.name} is {age_days} days old. Re-download? [y/N]: ")
    return answer.strip().lower() in ("y", "yes")


def _reporthook(block_num: int, block_size: int, total_size: int) -> None:
    """Print a simple progress bar during download."""
    downloaded = block_num * block_size
    if total_size > 0:
        pct = min(100, downloaded * 100 / total_size)
        mb_down = downloaded / 1_048_576
        mb_total = total_size / 1_048_576
        sys.stdout.write(f"\r  {pct:5.1f}%  ({mb_down:,.0f} / {mb_total:,.0f} MB)")
    else:
        mb_down = downloaded / 1_048_576
        sys.stdout.write(f"\r  {mb_down:,.0f} MB downloaded")
    sys.stdout.flush()


def check_and_download(
    base_url: str,
    data_dir: Path,
    files_to_download: list[tuple[str, Path]],
    tar_file: Path,
    dly_subdir: Path,
) -> None:
    """Download required GHCN files if missing and extract the tar archive."""
    data_dir.mkdir(parents=True, exist_ok=True)

    for remote_name, local_path in files_to_download:
        if local_path.exists():
            size_mb = local_path.stat().st_size / 1_048_576
            if _is_stale(local_path):
                mtime = datetime.fromtimestamp(local_path.stat().st_mtime, tz=timezone.utc)
                age_days = (datetime.now(tz=timezone.utc) - mtime).days
                log.info(
                    "[STALE] %s is %d days old (%.1f MB)",
                    local_path.name,
                    age_days,
                    size_mb,
                )
                if not _prompt_redownload(local_path, age_days):
                    log.info("  Keeping existing file")
                    continue
            else:
                log.info("[SKIP] %s already exists (%.1f MB)", local_path.name, size_mb)
                continue

        url = base_url + remote_name
        log.info("[DOWNLOAD] %s -> %s", remote_name, local_path)
        log.info("  Source: %s", url)
        urllib.request.urlretrieve(url, local_path, reporthook=_reporthook)
        size_mb = local_path.stat().st_size / 1_048_576
        sys.stdout.write("\n")
        log.info("  Done - %.1f MB", size_mb)

    # Extract tar.gz if the folder doesn't exist yet (rglob handles nested dirs)
    if dly_subdir.exists() and any(dly_subdir.rglob("*.dly")):
        dly_count = sum(1 for _ in dly_subdir.rglob("*.dly"))
        log.info(
            "[SKIP] %s/ already extracted (%s .dly files)",
            dly_subdir.name,
            f"{dly_count:,}",
        )
    else:
        log.info("[EXTRACT] %s -> %s", tar_file.name, data_dir)
        log.info("  This may take 10-20 minutes for ~120,000 files...")
        t0 = time.time()
        with tarfile.open(tar_file, "r:gz") as tar:
            tar.extractall(path=data_dir)
        elapsed = time.time() - t0
        log.info("  Extraction complete in %.1f minutes", elapsed / 60)


def load_countries(country_file: Path) -> pl.DataFrame:
    """Parse the fixed-width country code file (cols 1-2 = code, 4+ = name)."""
    rows = []
    with open(country_file, "r") as f:
        for line in f:
            if len(line.strip()) == 0:
                continue
            rows.append(
                {
                    "country_code": line[0:2].strip(),
                    "country_name": line[3:].strip(),
                }
            )
    return pl.DataFrame(rows)


_STATION_COLUMNS = [
    "station_id",
    "latitude",
    "longitude",
    "elevation",
    "state",
    "station_name",
    "gsn_flag",
    "hcn_crn_flag",
    "wmo_id",
]


def _parse_stations_txt(station_file: Path) -> pl.DataFrame:
    """Parse the fixed-width ``ghcnd-stations.txt`` format.

    Fixed-width layout:
    -------------------------------------------------------
    Variable       Columns   Type
    -------------------------------------------------------
    ID              1-11     Character
    LATITUDE       13-20     Real
    LONGITUDE      22-30     Real
    ELEVATION      32-37     Real
    STATE          39-40     Character
    NAME           42-71     Character
    GSN FLAG       73-75     Character
    HCN/CRN FLAG   77-79     Character
    WMO ID         81-85     Character
    -------------------------------------------------------
    """
    log.info("Parsing stations from fixed-width .txt")
    lines = [line for line in station_file.read_text().splitlines() if line.strip()]
    raw = pl.DataFrame({"line": lines})

    return (
        raw.with_columns(
            pl.col("line").str.slice(0, 11).str.strip_chars().alias("station_id"),
            pl.col("line").str.slice(12, 8).str.strip_chars().alias("latitude"),
            pl.col("line").str.slice(21, 9).str.strip_chars().alias("longitude"),
            pl.col("line").str.slice(31, 6).str.strip_chars().alias("elevation"),
            pl.col("line").str.slice(38, 2).str.strip_chars().alias("state"),
            pl.col("line").str.slice(41, 30).str.strip_chars().alias("station_name"),
        )
        .drop("line")
        .with_columns(
            pl.col("latitude").cast(pl.Float64).round(2),
            pl.col("longitude").cast(pl.Float64).round(2),
            pl.col("elevation").cast(pl.Float64).cast(pl.Int64),
        )
    )


def _parse_stations_csv(station_file: Path) -> pl.DataFrame:
    """Parse the comma-delimited ``ghcnd-stations.csv`` format (no header row)."""
    log.info("Parsing stations from .csv")
    return (
        pl.read_csv(
            station_file,
            has_header=False,
            new_columns=_STATION_COLUMNS,
            schema_overrides={
                "station_id": pl.String,
                "latitude": pl.Float64,
                "longitude": pl.Float64,
                "elevation": pl.Float64,
                "state": pl.String,
                "station_name": pl.String,
            },
        )
        .with_columns(
            pl.col("latitude").round(2),
            pl.col("longitude").round(2),
            pl.col("elevation").cast(pl.Int64),
            pl.col("station_id").str.strip_chars(),
            pl.col("state").str.strip_chars(),
            pl.col("station_name").str.strip_chars(),
        )
        .select("station_id", "latitude", "longitude", "elevation", "state", "station_name")
    )


def load_stations(
    station_file: Path,
    dly_subdir: Path,
    countries: pl.DataFrame,
) -> pl.DataFrame:
    """Load station metadata, filter to .dly files on disk, and join countries."""
    suffix = station_file.suffix.lower()
    if suffix == ".txt":
        stations = _parse_stations_txt(station_file)
    elif suffix == ".csv":
        stations = _parse_stations_csv(station_file)
    else:
        raise ValueError(f"Unsupported station file format: {suffix!r} (expected .txt or .csv)")

    # Derive country_code from the first two characters of station_id
    stations = stations.with_columns(
        pl.col("station_id").str.slice(0, 2).alias("country_code"),
    )

    # Filter to stations whose .dly file exists on disk (rglob handles nested dirs)
    log.info("Scanning .dly directory...")
    existing_files = {p.stem for p in dly_subdir.rglob("*.dly")}
    log.info("  Found %s .dly files", f"{len(existing_files):,}")

    stations = stations.filter(pl.col("station_id").is_in(existing_files))

    # Join country names
    stations = stations.join(countries, on="country_code", how="left")

    return stations.select(
        "country_code",
        "country_name",
        "state",
        "station_id",
        "station_name",
        "latitude",
        "longitude",
        "elevation",
    )
