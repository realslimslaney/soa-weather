"""Download Copernicus ERA5 reanalysis data for Storm Kristin (Jan 2026, Iberian Peninsula)."""

from pathlib import Path

import cdsapi

from soa_weather.utils import data_dir

DATASET = "reanalysis-era5-single-levels"
REQUEST = {
    "product_type": ["reanalysis"],
    "variable": [
        "10m_u_component_of_wind",
        "10m_v_component_of_wind",
        "total_precipitation",
        "10m_wind_gust_since_previous_post_processing",
        "instantaneous_10m_wind_gust",
        "mean_convective_precipitation_rate",
        "mean_large_scale_precipitation_rate",
        "mean_total_precipitation_rate",
        "maximum_total_precipitation_rate_since_previous_post_processing",
    ],
    "year": ["2026"],
    "month": ["01"],
    "day": ["27", "28", "29", "30", "31"],
    "time": [f"{h:02d}:00" for h in range(24)],
    "data_format": "netcdf",
    "download_format": "unarchived",
    "area": [45, -15, 35, 5],  # [N, W, S, E] — Iberian Peninsula bounding box
}

if __name__ == "__main__":
    output_path: Path = data_dir() / "era5_storm_kristin_jan2026.nc"
    client = cdsapi.Client()
    client.retrieve(DATASET, REQUEST).download(output_path)
    print(f"Downloaded to {output_path}")
