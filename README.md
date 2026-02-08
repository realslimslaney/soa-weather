# soa-weather
Sandbox for SOA Weather Research tasks. Not an official codebase of the SOA.

## Documentation

| Guide | Description |
|---|---|
| [Getting Started](docs/getting-started.md) | Install prerequisites, clone the repo, and run your first check |
| [Contributing](docs/contributing.md) | Workflow, code style, and project structure guidelines |

## Data Sources

- [NOAA Climate Data Online (CDO)](https://www.ncei.noaa.gov/cdo-web/datasets) — primary data source, particularly the GHCN (Global Historical Climatology Network) datasets

## Project Structure

```
src/soa_weather/  # Importable package (import soa_weather)
scripts/         # Runnable analysis scripts
tests/           # Tests
docs/            # Documentation
```

## Getting Started

See [docs/getting-started.md](docs/getting-started.md) for full setup instructions.

**Quick start** (assumes prerequisites are installed):

```bash
uv sync
just check
```

## Development

```bash
just lint       # Run linter
just format     # Auto-format code
just test       # Run tests
just check      # Lint + format check + test
```
