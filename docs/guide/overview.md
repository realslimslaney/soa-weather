# User Guide

soa-weather provides a pipeline for working with NOAA's GHCN-Daily weather data.

## How It Works

The main pipeline (`weather` CLI command or `soa_weather.main.main()`) performs three steps:

1. **Download** — fetches station metadata, country codes, and the full `.dly` archive from NOAA's public server. Skips files already on disk and prompts for re-download if files are older than 30 days.
2. **Parse & Filter** — reads fixed-width or CSV station files, filters to stations that have corresponding `.dly` files on disk, and joins country names.
3. **Write** — saves the final station list as a CSV.

## Modules at a Glance

| Module | Responsibility |
|---|---|
| [`main`](../api/main.md) | CLI entry point orchestrating the full pipeline |
| [`read`](../api/read.md) | Downloading, extracting, and parsing GHCN data files |
| [`write`](../api/write.md) | Writing DataFrames to disk |
| [`validate`](../api/validate.md) | Schema validation for Polars DataFrames |
| [`schema`](../api/schema.md) | Polars Schema definitions for standard datasets |
| [`config`](../api/config.md) | Logging setup |
| [`utils`](../api/utils.md) | Platform-aware data directory resolution |
