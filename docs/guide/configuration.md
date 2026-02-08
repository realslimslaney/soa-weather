# Configuration

## Data Directory

By default, downloaded data is stored at:

| Platform | Default Path |
|---|---|
| Windows | `C:/Data/SOA_Weather` |
| macOS / Linux | `~/Data/SOA_Weather` |

The directory is created automatically if it does not exist.

### Overriding the Data Directory

**Option 1 — Environment variable:**

=== "macOS / Linux"

    ```bash
    export SOA_WEATHER_DATA=/path/to/your/data
    ```

=== "Windows (PowerShell)"

    ```powershell
    $env:SOA_WEATHER_DATA = "D:\your\data"
    ```

=== "Windows (CMD)"

    ```cmd
    set SOA_WEATHER_DATA=D:\your\data
    ```

**Option 2 — `.env` file:**

Copy `.env.example` to `.env` and uncomment the `SOA_WEATHER_DATA` line:

```bash
cp .env.example .env
# then edit .env and set your custom path
```

## Logging

Logging is configured by `soa_weather.config.setup_logging()`. By default it sends `INFO`-level messages to stdout with a timestamp format:

```
2026-01-15 14:30:00 [INFO] soa_weather.read - Loading country lookup...
```

Pass a different `logging` level to change verbosity.

## Stale File Detection

Files older than **30 days** are flagged as stale. The pipeline will prompt whether to re-download them. This threshold is defined as `STALE_DAYS` in `soa_weather.read`.
