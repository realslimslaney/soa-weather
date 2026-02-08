---
hide:
  - navigation
---

# soa-weather

Weather data analysis toolkit for the Society of Actuaries Weather Research group.

---

**soa-weather** is a Python toolkit for downloading, parsing, validating, and analyzing
NOAA GHCN-Daily (Global Historical Climatology Network) weather station data.

!!! note
    This is a sandbox / research repository. It is **not** an official codebase of the SOA.

## Features

- **Automated data download** from NOAA's GHCN-Daily archive with smart caching
- **Fixed-width and CSV parsing** of station metadata files
- **Schema validation** using Polars DataFrames
- **Configurable data directory** via environment variable or `.env` file
- **CLI entry point** (`weather` command) for one-step download-and-build

## Quick Start

```bash
# Install dependencies
uv sync

# Run all checks (lint + format + test)
just check

# Run the main pipeline
uv run weather
```

## Project Structure

| Directory | Purpose |
|---|---|
| `src/soa_weather/` | Importable package |
| `scripts/` | Standalone analysis scripts |
| `tests/` | Test suite |
| `docs/` | Documentation (this site) |

## Data Sources

- [NOAA Climate Data Online (CDO)](https://www.ncei.noaa.gov/cdo-web/datasets) — primary data source, particularly the GHCN-Daily datasets
