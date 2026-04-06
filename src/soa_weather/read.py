"""Functions for reading and downloading GHCN-Daily data."""

import logging
import sys
import tarfile
import time
import urllib.request
from datetime import date as Date
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
            mtime = datetime.fromtimestamp(local_path.stat().st_mtime, tz=timezone.utc)
            age_days = (datetime.now(tz=timezone.utc) - mtime).days
            log.info(
                "[EXISTS] %s (%d days old, %.1f MB)",
                local_path.name,
                age_days,
                size_mb,
            )
            if not _prompt_redownload(local_path, age_days):
                log.info("  Keeping existing file")
                continue

        url = base_url + remote_name
        log.info("[DOWNLOAD] %s -> %s", remote_name, local_path)
        log.info("  Source: %s", url)
        urllib.request.urlretrieve(url, local_path, reporthook=_reporthook)
        size_mb = local_path.stat().st_size / 1_048_576
        sys.stdout.write("\n")
        log.info("  Done - %.1f MB", size_mb)

    # Extract tar.gz — prompt if extraction looks incomplete
    needs_extract = True
    if dly_subdir.exists() and any(dly_subdir.rglob("*.dly")):
        dly_count = sum(1 for _ in dly_subdir.rglob("*.dly"))
        log.info(
            "[EXISTS] %s/ has %s .dly files",
            dly_subdir.name,
            f"{dly_count:,}",
        )
        if dly_count < 100_000:
            log.warning("  Expected ~120,000 files — extraction may be incomplete")
            answer = input(f"  Re-extract {tar_file.name}? [y/N]: ")
            needs_extract = answer.strip().lower() in ("y", "yes")
            if not needs_extract:
                log.info("  Keeping existing extraction")
        else:
            needs_extract = False

    if needs_extract:
        log.info("[EXTRACT] %s -> %s", tar_file.name, data_dir)
        log.info("  This may take 10-20 minutes for ~120,000 files...")
        t0 = time.time()
        with tarfile.open(tar_file, "r:gz") as tar:
            log.info("  Scanning archive (this may take a minute)...")
            members = tar.getmembers()
            total = len(members)
            log.info("  Archive contains %s files", f"{total:,}")
            for i, member in enumerate(members, 1):
                tar.extract(member, path=data_dir)
                if i % 10_000 == 0 or i == total:
                    elapsed = time.time() - t0
                    sys.stdout.write(f"\r  {i:,} / {total:,} files extracted ({elapsed:.0f}s)")
                    sys.stdout.flush()
            sys.stdout.write("\n")
        elapsed = time.time() - t0
        log.info("  Extraction complete in %.1f minutes", elapsed / 60)


def extract_txt_files(tar_file: Path, output_dir: Path) -> None:
    """Extract all .txt files from a tar.gz archive into *output_dir*.

    Parameters
    ----------
    tar_file : Path
        Path to the ``.tar.gz`` archive.
    output_dir : Path
        Destination folder; created if it does not exist.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    log.info("[EXTRACT TXT] %s -> %s", tar_file.name, output_dir)
    t0 = time.time()
    with tarfile.open(tar_file, "r:gz") as tar:
        txt_members = [m for m in tar.getmembers() if m.name.endswith(".txt")]
        log.info("  Found %s .txt files in archive", f"{len(txt_members):,}")
        tar.extractall(path=output_dir, members=txt_members)
    elapsed = time.time() - t0
    log.info("  Extraction complete in %.1f seconds", elapsed)


def parse_dly(dly_file: Path) -> pl.DataFrame:
    """Parse a single GHCN-Daily ``.dly`` file into a long-format DataFrame.

    Each line represents one month of observations for one element at one station.
    Fixed-width layout per line (1-based NOAA column numbers):

    - Cols  1-11: Station ID
    - Cols 12-15: Year
    - Cols 16-17: Month
    - Cols 18-21: Element (e.g. TMAX, TMIN, PRCP)
    - Then 31 groups of 8 chars (one per day): VALUE(5) MFLAG(1) QFLAG(1) SFLAG(1)

    Missing values (-9999) and invalid calendar dates (e.g. Feb 30) are dropped.
    Output schema matches ``OBSERVATIONS_SCHEMA``.

    Parameters
    ----------
    dly_file : Path
        Path to a single ``.dly`` station file.

    Returns
    -------
    pl.DataFrame
        Long-format observations with columns:
        ``station_id``, ``date``, ``element``, ``value``, ``mflag``, ``qflag``, ``sflag``.
    """
    lines = [line for line in dly_file.read_text().splitlines() if len(line) >= 21]
    if not lines:
        return pl.DataFrame()

    raw = (
        pl.DataFrame({"line": lines})
        .with_columns(
            pl.col("line").str.slice(0, 11).str.strip_chars().alias("station_id"),
            pl.col("line").str.slice(11, 4).cast(pl.Int32).alias("year"),
            pl.col("line").str.slice(15, 2).cast(pl.Int32).alias("month"),
            pl.col("line").str.slice(17, 4).str.strip_chars().alias("element"),
            *[
                pl.struct(
                    pl.col("line")
                    .str.slice(21 + (d - 1) * 8, 5)
                    .str.strip_chars()
                    .cast(pl.Int64)
                    .alias("value"),
                    pl.col("line").str.slice(21 + (d - 1) * 8 + 5, 1).alias("mflag"),
                    pl.col("line").str.slice(21 + (d - 1) * 8 + 6, 1).alias("qflag"),
                    pl.col("line").str.slice(21 + (d - 1) * 8 + 7, 1).alias("sflag"),
                ).alias(str(d))
                for d in range(1, 32)
            ],
        )
        .drop("line")
    )

    return (
        raw.unpivot(
            on=[str(d) for d in range(1, 32)],
            index=["station_id", "year", "month", "element"],
            variable_name="day",
            value_name="obs",
        )
        .with_columns(
            pl.col("day").cast(pl.Int32),
            pl.col("obs").struct.field("value").alias("value"),
            pl.col("obs").struct.field("mflag").alias("mflag"),
            pl.col("obs").struct.field("qflag").alias("qflag"),
            pl.col("obs").struct.field("sflag").alias("sflag"),
        )
        .drop("obs")
        .filter(pl.col("value") != -9999)
        .with_columns(
            (
                pl.col("year").cast(pl.String).str.zfill(4)
                + pl.col("month").cast(pl.String).str.zfill(2)
                + pl.col("day").cast(pl.String).str.zfill(2)
            )
            .str.to_date(format="%Y%m%d", strict=False)
            .alias("date")
        )
        .filter(pl.col("date").is_not_null())
        .select("station_id", "date", "element", "value", "mflag", "qflag", "sflag")
        .sort("station_id", "date", "element")
    )


def load_station_observations(station_ids: list[str], dly_subdir: Path) -> pl.DataFrame:
    """Load and concatenate ``.dly`` observation files for a list of station IDs.

    Parameters
    ----------
    station_ids : list[str]
        GHCN station identifiers to load (e.g. ``["SPE00120354", "POM00008535"]``).
    dly_subdir : Path
        Directory containing ``.dly`` files (may be nested).

    Returns
    -------
    pl.DataFrame
        Combined long-format observations for all requested stations.
    """
    total = len(station_ids)
    log.info("Loading observations for %s stations...", f"{total:,}")
    t0 = time.time()
    frames = []
    for i, sid in enumerate(station_ids, 1):
        dly_file = next(dly_subdir.rglob(f"{sid}.dly"), None)
        if dly_file is None:
            log.warning("No .dly file found for station %s", sid)
            continue
        frames.append(parse_dly(dly_file))
        if i % 10 == 0 or i == total:
            elapsed = time.time() - t0
            sys.stdout.write(f"\r  {i:,} / {total:,} stations ({elapsed:.0f}s)")
            sys.stdout.flush()
    sys.stdout.write("\n")
    if not frames:
        return pl.DataFrame()
    log.info("Concatenating %s station frames...", f"{len(frames):,}")
    result = pl.concat(frames)
    log.info("Done — %s observations loaded in %.1fs", f"{result.height:,}", time.time() - t0)
    return result


def pivot_observations(
    obs: pl.DataFrame,
    element: str,
    date_start: Date,
    date_end: Date,
    completeness_threshold: float = 0.0,
) -> pl.DataFrame:
    """Pivot long-format observations to wide format with one column per date.

    Replicates the output of the VBA ``Output_Station_Data_for_Specified_Period`` macro:
    one row per station, one column per calendar date, plus a data completeness column.

    Parameters
    ----------
    obs : pl.DataFrame
        Long-format observations as returned by ``load_station_observations`` or ``parse_dly``.
    element : str
        The element to pivot (e.g. ``"TMAX"``, ``"PRCP"``).
    date_start : date
        Start of the date range (inclusive).
    date_end : date
        End of the date range (inclusive).
    completeness_threshold : float
        Minimum fraction of days with data (0.0–1.0). Stations below this threshold
        are dropped. Default ``0.0`` keeps all stations.

    Returns
    -------
    pl.DataFrame
        Wide-format DataFrame with columns:
        ``station_id``, ``data_complete_pct``, one column per date in the range.
    """
    total_days = (date_end - date_start).days + 1

    filtered = obs.filter(
        (pl.col("element") == element)
        & (pl.col("date") >= date_start)
        & (pl.col("date") <= date_end)
    ).select("station_id", "date", "value")

    completeness = filtered.group_by("station_id").agg(
        (pl.col("value").count() / total_days).alias("data_complete_pct")
    )

    if completeness_threshold > 0.0:
        passing = completeness.filter(pl.col("data_complete_pct") >= completeness_threshold)[
            "station_id"
        ]
        filtered = filtered.filter(pl.col("station_id").is_in(passing))
        completeness = completeness.filter(pl.col("station_id").is_in(passing))

    wide = filtered.pivot(values="value", index="station_id", on="date", aggregate_function="first")

    # Sort date columns chronologically (ISO strings sort correctly as strings)
    date_cols = sorted(c for c in wide.columns if c != "station_id")

    return (
        wide.join(completeness, on="station_id", how="left")
        .select(["station_id", "data_complete_pct", *date_cols])
        .sort("station_id")
    )


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
