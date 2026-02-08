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

## Links

- [NOAA CDO Datasets](https://www.ncei.noaa.gov/cdo-web/datasets)
- [GHCN-Daily README](https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme.txt)
