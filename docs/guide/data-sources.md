# Data Sources

soa-weather works with NOAA's **GHCN-Daily** (Global Historical Climatology Network — Daily) dataset.

## GHCN-Daily Files

The pipeline downloads three files from `https://www.ncei.noaa.gov/pub/data/ghcn/daily/`:

| File | Description | Approximate Size |
|---|---|---|
| `ghcnd-stations.txt` | Fixed-width station metadata (~120K stations) | ~10 MB |
| `ghcnd-countries.txt` | Two-letter country code lookup | ~10 KB |
| `ghcnd_all.tar.gz` | Complete archive of `.dly` observation files | ~3.5 GB |

!!! warning
    The tar archive extraction creates ~120,000 files and can take 10–20 minutes.

## Station Metadata Schema

After processing, station data follows this schema:

| Column | Type | Description |
|---|---|---|
| `country_code` | String | Two-letter country code (e.g. `US`) |
| `country_name` | String | Full country name (e.g. `United States`) |
| `state` | String | State or province code (2 characters) |
| `station_id` | String | GHCN station identifier (e.g. `USW00094728`) |
| `station_name` | String | Human-readable station name |
| `latitude` | Float64 | Latitude in decimal degrees (rounded to 2 decimals) |
| `longitude` | Float64 | Longitude in decimal degrees (rounded to 2 decimals) |
| `elevation` | Int64 | Elevation in meters above sea level |

## Country Code Schema

| Column | Type | Description |
|---|---|---|
| `country_code` | String | Two-letter country code |
| `country_name` | String | Full country name |

## Observation Data Schema (``.dly`` files)

Each `.dly` file contains all historical daily observations for one station.
Use `parse_dly` (single file) or `load_station_observations` (multiple stations) to
read them into a long-format DataFrame.

Fixed-width layout per record line (1-based column numbers):

| Field | Columns | Description |
|---|---|---|
| Station ID | 1–11 | GHCN station identifier |
| Year | 12–15 | 4-digit year |
| Month | 16–17 | 2-digit month |
| Element | 18–21 | Observation type (e.g. `TMAX`, `TMIN`, `PRCP`) |
| Value 1–31 | repeating | 5-char integer; **-9999** = missing |
| MFlag 1–31 | +5 | Measurement flag (1 char) |
| QFlag 1–31 | +6 | Quality assurance flag (1 char) |
| SFlag 1–31 | +7 | Source flag (1 char) |

Each day block is 8 characters wide (5 + 1 + 1 + 1), starting at column 22.

After parsing, output follows `OBSERVATIONS_SCHEMA`:

| Column | Type | Description |
|---|---|---|
| `station_id` | String | GHCN station identifier |
| `date` | Date | Calendar date (invalid dates like Feb 30 are dropped) |
| `element` | String | Observation type |
| `value` | Int32 | Raw integer value (tenths of °C for TMAX/TMIN; tenths of mm for PRCP) |
| `mflag` | String | Measurement flag |
| `qflag` | String | Quality assurance flag |
| `sflag` | String | Source flag |

## Links

- [NOAA CDO Datasets](https://www.ncei.noaa.gov/cdo-web/datasets)
- [GHCN-Daily README](https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme.txt)
