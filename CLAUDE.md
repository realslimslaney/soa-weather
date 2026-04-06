# SOA Weather

## Overview

Weather data analysis toolkit for the Society of Actuaries (SOA) Weather and Research group. Downloads, parses, and processes GHCN-Daily (Global Historical Climatology Network) weather station data from NOAA's Climate Data Online. This is a sandbox/research repo, not an official SOA codebase.

## Project Structure

```
soa-weather/
├── src/soa_weather/         # Main package
│   ├── main.py              # CLI entry point
│   ├── read.py              # Download & parsing logic
│   ├── write.py             # CSV output functions
│   ├── validate.py          # Schema validation
│   ├── config.py            # Logging configuration
│   ├── schema.py            # Polars schemas
│   └── utils.py             # Platform-specific paths
├── scripts/
│   ├── read_ghcn_daily.py   # GHCN-Daily station data download & export
│   ├── read_era5.py         # ERA5 reanalysis data reader
│   └── texas_floods_example.py # Example analysis script
├── quarto/                  # Quarto documents and reports
│   └── portugal_storm_kristin.qmd
├── tests/                   # pytest test suite
├── docs/                    # MkDocs documentation (Diataxis structure)
└── .github/workflows/       # CI (lint + test) and docs deployment
```

## Languages & Tools

- **Language**: Python 3.12+
- **Package manager**: uv (never use pip)
- **Data library**: Polars (not pandas)
- **Linting/formatting**: ruff (line length: 100, rules: E, F, I, W)
- **Testing**: pytest
- **Pre-commit**: ruff check + ruff format
- **Documentation**: MkDocs + Material theme + mkdocstrings (NumPy-style docstrings)
- **Task runner**: just
- **Platform**: Windows (primary), CI runs on Ubuntu
- **Data source**: [NOAA Climate Data Online (CDO)](https://www.ncei.noaa.gov/cdo-web/datasets) — GHCN datasets

## Key Commands

```bash
just check          # lint + format-check + test (full CI)
just test           # Run pytest
just lint           # Run ruff check
just format         # Auto-format with ruff
just docs-serve     # Serve docs locally
uv sync             # Install dependencies
uv run python scripts/read_ghcn_daily.py  # Run scripts via uv
```

## Code Conventions

- Use Polars for all data manipulation
- Use lazy evaluation (`scan_*` / `.lazy()`) where possible for performance
- Default to `Float64` and `Int64` for numeric Polars columns — avoid 32-bit types unless there is a specific memory constraint
- Type hints on all function signatures
- NumPy-style docstrings for all public functions
- Schema-driven validation via `schema.py` and `validate.py`
- Platform-aware paths (Windows: `C:/Data/SOA_Weather`, macOS/Linux: `~/Data/SOA_Weather`)
- Configurable via `SOA_WEATHER_DATA` environment variable

## Data Flow

1. Download GHCN station metadata and country lookup from NOAA
2. Parse fixed-width text files into Polars DataFrames
3. Validate against defined schemas
4. Filter stations by available .dly files
5. Join with country names and write to CSV

## CI/CD

- **ci.yml**: Runs ruff check, ruff format --check, and pytest on push/PR
- **docs.yml**: Builds and deploys MkDocs to GitHub Pages on main branch
