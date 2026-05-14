# Best Practices

## File Paths

Always use `pathlib.Path` and forward slashes. Backslash string literals break on macOS and Linux.

```python
# Good
from pathlib import Path
DATA_DIR = Path(__file__).parent / "data"
csv_path = DATA_DIR / "stations.csv"

# Bad — Windows-only, breaks CI
filepath = "data\\stations.csv"
```

Anchor paths to `__file__` so scripts work regardless of the working directory:

```python
# Good — works from any CWD
DATA_DIR = Path(__file__).parent / "data"

# Bad — only works if you cd to the right directory first
DATA_DIR = Path("data")
```

Forward slashes also work in YAML and TOML config files on all platforms:

```yaml
# Good
python: "../.venv/Scripts/python.exe"

# Bad in YAML (backslash is an escape character)
python: "..\\.venv\\Scripts\\python.exe"
```

## Scripts vs Modules

Wrap top-level execution in `if __name__ == "__main__"` so a script can be imported without running:

```python
# Good
if __name__ == "__main__":
    main()

# Bad — runs immediately on import
client.retrieve(dataset, request).download()
```

## Environment Variables

`.env.example` is a template — every line should be commented out. Use `KEY=value` with no spaces around `=`:

```bash
# Good
# SOA_WEATHER_DATA=/custom/path

# Bad — active assignment with spaces; most .env parsers reject this
SOA_WEATHER_DATA = "/custom/path"
```

## ERA5 / CDS API

ERA5 credentials go in `~/.cdsapirc`, not in `.env`. The `cdsapi` library reads that file automatically — do not pass credentials via environment variables. See the [CDS API how-to](https://cds.climate.copernicus.eu/how-to-api) for setup.

Always pass an explicit output path to `.download()` so the file lands in a known location:

```python
# Good
client.retrieve(dataset, request).download(data_dir() / "era5_output.nc")

# Bad — saves to CWD with a generated filename
client.retrieve(dataset, request).download()
```

## Polars

- Use `pl.Config.set_tbl_rows(...)` only inside `if __name__ == "__main__"` — it mutates global state and affects any process that imports the file.
- Filter date columns with `date(2025, 7, 4)` from the standard library, not `pl.datetime(...)`.
- Pin the Polars version in `pyproject.toml` (`"polars>=1.0"`) — Polars has breaking API changes between minor versions.
