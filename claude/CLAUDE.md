# SOA Weather

Python project for analyzing weather data as part of the Society of Actuaries (SOA) Weather and Research group. Uses Polars for data manipulation and analysis.

## Tech Stack

- **Language:** Python >=3.12
- **Data processing:** Polars
- **Package manager:** uv
- **Task runner:** just
- **Linting/formatting:** ruff
- **Testing:** pytest
- **Platform:** Windows (primary), CI runs on Ubuntu

## Data Sources

- [NOAA Climate Data Online (CDO)](https://www.ncei.noaa.gov/cdo-web/datasets) — primary data source, particularly the GHCN (Global Historical Climatology Network) datasets

## Project Layout

- `src/soa_weather/` — importable package (`import soa_weather`) with shared utilities and modules
- `scripts/` — runnable analysis scripts (import from `soa_weather` package)
- `tests/` — pytest test suite
- `docs/` — documentation

## Conventions

- This is a sandbox/research repo, not an official SOA codebase
- Prefer Polars over pandas for dataframe operations
- Use lazy evaluation (`scan_*` / `.lazy()`) where possible for performance
- Default to `Float64` and `Int64` for all numeric Polars columns — avoid 32-bit types unless there is a specific memory constraint
- Use `uv run` to execute scripts (e.g. `uv run python scripts/read_station_data.py`)
- Use `just` for common tasks: `just lint`, `just format`, `just test`, `just check`
- Ruff line length is 100 characters
