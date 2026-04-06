"""Read Copernicus ERA5 Data"""

import cdsapi

dataset = "reanalysis-era5-single-levels"
request = {
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
    "time": [
        "00:00",
        "01:00",
        "02:00",
        "03:00",
        "04:00",
        "05:00",
        "06:00",
        "07:00",
        "08:00",
        "09:00",
        "10:00",
        "11:00",
        "12:00",
        "13:00",
        "14:00",
        "15:00",
        "16:00",
        "17:00",
        "18:00",
        "19:00",
        "20:00",
        "21:00",
        "22:00",
        "23:00",
    ],
    "data_format": "netcdf",
    "download_format": "unarchived",
    "area": [45, -15, 35, 5],
}

client = cdsapi.Client()
client.retrieve(dataset, request).download()
