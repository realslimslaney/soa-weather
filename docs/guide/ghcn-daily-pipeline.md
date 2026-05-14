# GHCN-Daily Pipeline

The GHCN-Daily (Global Historical Climatology Network – Daily) pipeline downloads station metadata and observation files from NOAA, parses them into Polars DataFrames, and writes a station index CSV used by Quarto reports.

## Overview

```
NOAA FTP
  ├── ghcnd-stations.txt     → station metadata (fixed-width)
  ├── ghcnd-countries.txt    → country code lookup (fixed-width)
  └── ghcnd_all.tar.gz       → ~120,000 .dly observation files

                  ↓ check_and_download()

Local data directory (C:/Data/SOA_Weather by default)
  ├── ghcnd-stations.txt
  ├── ghcnd-countries.txt
  ├── ghcnd_all.tar.gz
  └── ghcnd_all/             → extracted .dly files

                  ↓ load_stations() + load_countries()

stations_output.csv           → filtered station index with country names

                  ↓ load_station_observations() (in reports)

Long-format observations DataFrame
  └── pivot_observations()   → wide format (one column per date)
```

## Running the Pipeline

```bash
uv run python scripts/read_ghcn_daily.py
```

On first run this downloads ~4 GB of data and extracts ~120,000 files — expect 15–30 minutes. Subsequent runs skip files that are already present and prompt before re-downloading anything stale (older than 30 days).

## Step-by-Step

### 1. Download

`check_and_download()` fetches three files from NOAA if they are missing locally:

| File | Size | Purpose |
|---|---|---|
| `ghcnd-stations.txt` | ~10 MB | Station metadata (ID, coordinates, name) |
| `ghcnd-countries.txt` | ~5 KB | Two-letter country code → country name |
| `ghcnd_all.tar.gz` | ~4 GB | All `.dly` observation files |

After downloading, the tar archive is extracted into `ghcnd_all/`. If the extraction looks incomplete (fewer than 100,000 `.dly` files), you are prompted to re-extract.

### 2. Parse Station Metadata

`load_stations()` reads `ghcnd-stations.txt` (or `.csv` if present) and produces a DataFrame matching `STATIONS_SCHEMA`:

| Column | Type | Description |
|---|---|---|
| `country_code` | String | First two characters of `station_id` |
| `country_name` | String | Joined from `ghcnd-countries.txt` |
| `state` | String | US state abbreviation (blank for non-US) |
| `station_id` | String | 11-character GHCN station identifier |
| `station_name` | String | Human-readable station name |
| `latitude` | Float64 | Decimal degrees, rounded to 2 places |
| `longitude` | Float64 | Decimal degrees, rounded to 2 places |
| `elevation` | Int64 | Metres above sea level |

Stations are filtered to only those whose `.dly` file exists on disk, so `stations_output.csv` reflects what is actually available locally.

### 3. Write Station Index

`write_stations_csv()` writes the filtered station DataFrame to `stations_output.csv` in the data directory. This file is the starting point for all Quarto reports — reports read it, filter by bounding box or country, and use the resulting station IDs to load observations.

### 4. Load Observations (in reports)

Reports call `load_station_observations()` with a list of station IDs and the `ghcnd_all/` directory. It parses each matching `.dly` file via `parse_dly()` and concatenates the results into a single long-format DataFrame matching `OBSERVATIONS_SCHEMA`:

| Column | Type | Description |
|---|---|---|
| `station_id` | String | GHCN station identifier |
| `date` | Date | Calendar date |
| `element` | String | Measurement type (e.g. `PRCP`, `TMAX`, `TMIN`) |
| `value` | Int64 | Raw integer value in NOAA units (see below) |
| `mflag` | String | Measurement flag |
| `qflag` | String | Quality flag (blank = passed QA) |
| `sflag` | String | Source flag |

### 5. Clean Observations (in reports)

Two cleaning steps are applied before analysis:

**`filter_ghcn_quality_flags(obs)`** — drops any row where `qflag` is not blank. A non-blank flag means NOAA's QA process flagged the value as suspect or erroneous.

**`clean_ghcn_daily_observations(obs, system="metric")`** — converts raw NOAA integer storage units to human-readable values:

| Element | Raw unit | Metric | Imperial |
|---|---|---|---|
| `TMAX`, `TMIN`, `TAVG` | tenths of °C | °C | °F |
| `PRCP`, `MDPR`, `DAPR` | tenths of mm | mm | inches |
| `SNOW`, `SNWD` | mm | mm | inches |

### 6. Pivot to Wide Format (in reports)

`pivot_observations()` converts the long-format observations to wide format — one row per station, one column per calendar date — for a given element and date range. A `data_complete_pct` column indicates what fraction of days in the window the station reported. Stations below a configurable `completeness_threshold` are dropped.

## Data Directory

The default data directory is `C:/Data/SOA_Weather` on Windows and `~/Data/SOA_Weather` on macOS/Linux. Override it with the `SOA_WEATHER_DATA` environment variable (see [Configuration](configuration.md)).

## Common Elements

| Element | Description |
|---|---|
| `PRCP` | Precipitation |
| `TMAX` | Maximum temperature |
| `TMIN` | Minimum temperature |
| `TAVG` | Average temperature |
| `SNOW` | Snowfall |
| `SNWD` | Snow depth |

For the full element list see the [GHCN-Daily readme](https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme.txt).
