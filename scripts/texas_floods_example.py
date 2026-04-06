import json

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import geopandas as gpd
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import polars as pl
from scipy.interpolate import griddata

# NOTE: this work is not mine, I copied it from https://www.soa.org/resources/research-reports/2019/weather-extremes/
# this work is open source and available for use, and copying it here helped me build future studies

pl.Config.set_tbl_rows(1000)
filepath = "data\\TexasFlooding.csv"  # Taken from excel tool
riverfile = "data\\shapefile\\Tx_Rivers_General_NE.shp"  # https://www.depts.ttu.edu/geospatial/center/TexasGISData.html # noqa: E501
countyfile = "data\\shapefile\\Tx_Census_CntyBndry_Detail_TIGER500k.shp"  # https://www.depts.ttu.edu/geospatial/center/TexasGISData.html # noqa: E501
huntdischarge = "data\\HuntDischargeMax.json"  # https://waterdata.usgs.gov/monitoring-location/USGS-08165500/ on 7/10/2025  # noqa: E501
kerrvilledischarge = "data\\KerrvilleDischargeMax.json"  # https://waterdata.usgs.gov/monitoring-location/USGS-08166200/ on 7/10/2025  # noqa: E501
comfortdischarge = "data\\ComfortDischargeMax.json"  # https://waterdata.usgs.gov/monitoring-location/USGS-08167000/ on 7/10/2025  # noqa: E501
kerrvillegage = "data\\KerrvilleGageMax.json"  # https://waterdata.usgs.gov/monitoring-location/USGS-08166200/ on 7/10/2025  # noqa: E501


raw_data = pl.read_csv(
    source=filepath,
    has_header=True,
    infer_schema_length=100000,
)

melted = (
    raw_data.unpivot(
        index=[
            "Country",
            "State",
            "Station_ID",
            "Station_Name",
            "Lat_N",
            "Lon_E",
            "Elev_Meters",
            " Data_Complete_Pct",
        ]
    )
    .rename({"variable": "date"})
    .with_columns(
        pl.col(" Data_Complete_Pct")
        .str.replace(" ", "")
        .cast(pl.Float64)
        .alias("data_complete_pct")
    )
    .drop(" Data_Complete_Pct")
)

precip_data = (
    melted.with_columns(
        pl.date(
            year=pl.col("date").str.slice(0, 4),
            month=pl.col("date").str.slice(4, 2),
            day=pl.col("date").str.slice(6, 2),
        ).alias("date1")
    )
    .drop("date")
    .rename({"date1": "date", "value": "precip"})
)
july4th = (
    precip_data.filter(pl.col("date") == pl.datetime(2025, 7, 4))
    .with_columns(
        pl.col("Lat_N").str.replace_all(" ", "").cast(pl.Float64),
        pl.col("Lon_E").str.replace_all(" ", "").cast(pl.Float64),
        pl.col("precip").str.replace_all(" ", "").cast(pl.Float64),
    )
    .with_columns((pl.col("Lon_E") - 360).alias("longitude"), pl.col("Lat_N").alias("latitude"))
    .filter(pl.col("precip").is_not_null())
    .to_pandas()
)

lat = july4th["latitude"]
lon = july4th["longitude"]
precip = july4th["precip"]

xi = np.linspace(lon.min(), lon.max(), 100)
yi = np.linspace(lat.min(), lat.max(), 100)
zi = griddata((lon, lat), precip, (xi[None, :], yi[:, None]), method="linear")

max_precip = precip.max()
levels = np.linspace(0.5, max_precip, 50) if max_precip > 0 else np.array([0, 1])
vmin_for_norm = 0.5
colors = ["lightgreen", "green", "yellow", "orange", "red", "darkred"]
custom_cmap = mcolors.LinearSegmentedColormap.from_list("green_yellow_red_darkred", colors)

cmap = custom_cmap
cmap_with_transparent_under = cmap.copy()
cmap_with_transparent_under.set_under(color="none", alpha=0)
norm = mcolors.Normalize(vmin=vmin_for_norm, vmax=max_precip)

proj = ccrs.PlateCarree()
fig, ax = plt.subplots(1, 1, figsize=(10, 8), subplot_kw={"projection": proj})

graph1 = ax.contourf(
    xi,
    yi,
    zi,
    cmap=cmap_with_transparent_under,
    transform=ccrs.PlateCarree(),
    levels=levels,
    norm=norm,
    extend="max",
)

ax.coastlines(resolution="10m")  # Use higher resolution for better detail
ax.add_feature(cfeature.STATES, edgecolor="black", zorder=1)  # Add state borders
ax.add_feature(cfeature.OCEAN, facecolor="lightsteelblue", zorder=0)  # Plot ocean behind features
ax.add_feature(
    cfeature.LAND, facecolor="white", edgecolor="black", zorder=0.5
)  # Plot land behind features

ax.set_extent([-107.5, -93, 25, 37], ccrs.PlateCarree())

try:
    rivers = gpd.read_file(riverfile)
    if rivers.crs is None or rivers.crs != ccrs.PlateCarree():
        rivers = rivers.to_crs(ccrs.PlateCarree())

    rivers.plot(
        ax=ax,
        edgecolor="blue",
        facecolor="none",
        linewidth=0.5,
        zorder=4,
        label="Guadalupe River",
    )
    print(f"Successfully loaded and plotted Guadalupe River from: {riverfile}")

except Exception as e:
    print(f"Error loading or plotting Guadalupe River shapefile: {e}")
    print(f"Please ensure you have geopandas installed and the path '{riverfile}' is correct.")
    print("If you cannot find a specific shapefile, cfeature.RIVERS adds general rivers.")

kerrville_lat = 30.0474
kerrville_lon = -99.1403
ax.scatter(
    kerrville_lon,
    kerrville_lat,
    color="black",
    marker="o",
    s=10,
    edgecolor="white",
    linewidth=1,
    transform=ccrs.PlateCarree(),
    zorder=5,
    label="Kerrville",
)
ax.text(
    kerrville_lon + 0.1,
    kerrville_lat + 0.05,
    "Kerrville",
    fontsize=10,
    color="black",
    horizontalalignment="left",
    verticalalignment="bottom",
    transform=ccrs.PlateCarree(),
    zorder=5,
)

hunt_lat = 30.0710
hunt_lon = -99.3380
ax.scatter(
    hunt_lon,
    hunt_lat,
    color="black",
    marker="o",
    s=10,
    edgecolor="white",
    linewidth=1,
    transform=ccrs.PlateCarree(),
    zorder=5,
    label="Hunt",
)
ax.text(
    hunt_lon - 0.1,
    hunt_lat + 0.05,
    "Hunt",
    fontsize=10,
    color="black",
    horizontalalignment="right",
    verticalalignment="bottom",
    transform=ccrs.PlateCarree(),
    zorder=5,
)

comfort_lat = 29.9677
comfort_lon = -98.9050
ax.scatter(
    comfort_lon,
    comfort_lat,
    color="black",
    marker="o",
    s=10,
    edgecolor="white",
    linewidth=1,
    transform=ccrs.PlateCarree(),
    zorder=5,
    label="Comfort",
)
ax.text(
    comfort_lon + 0.02,
    comfort_lat - 0.2,
    "Comfort",
    fontsize=10,
    color="black",
    horizontalalignment="left",
    verticalalignment="bottom",
    transform=ccrs.PlateCarree(),
    zorder=5,
)

ax.text(
    kerrville_lon + 0.8,
    kerrville_lat - 0.5,
    "Guadalupe River",
    fontsize=7,
    color="blue",
    horizontalalignment="left",
    verticalalignment="top",
    transform=ccrs.PlateCarree(),
    zorder=5,
)

try:
    texas_counties = gpd.read_file(countyfile)

    if texas_counties.crs is None or texas_counties.crs != ccrs.PlateCarree():
        texas_counties = texas_counties.to_crs(ccrs.PlateCarree())

    texas_counties.plot(ax=ax, edgecolor="darkgray", facecolor="none", linewidth=0.5, zorder=1.2)
    print(f"Successfully loaded and plotted Texas counties from: {countyfile}")
except Exception as e:
    print(f"Error loading or plotting US counties shapefile: {e}")
    print(f"Please ensure you have geopandas installed, the path '{countyfile}' is correct")


ax.set_title("Precipitation, July 4th, 2025")
gl = ax.gridlines(
    draw_labels=True,
    crs=ccrs.PlateCarree(),
    linestyle="--",
    color="gray",
    xlocs=np.arange(-108, -92, 2),
    ylocs=np.arange(24, 38, 2),
)  # Custom gridline locations
gl.top_labels = False
gl.right_labels = False
cbar = fig.colorbar(graph1, label="Precipitation (inches)")
cbar_ax = cbar.ax
cbar_ax.yaxis.set_major_locator(mticker.MaxNLocator(nbins=5, integer=True))

plt.tight_layout()
plt.show()

july4th = (
    precip_data.filter(pl.col("date") == pl.datetime(2025, 7, 4))
    .with_columns(
        pl.col("Lat_N").str.replace_all(" ", "").cast(pl.Float64),
        pl.col("Lon_E").str.replace_all(" ", "").cast(pl.Float64),
        pl.col("precip").str.replace_all(" ", "").cast(pl.Float64),
    )
    .with_columns((pl.col("Lon_E") - 360).alias("longitude"), pl.col("Lat_N").alias("latitude"))
    .filter(pl.col("precip").is_not_null())
    .to_pandas()
)

lat = july4th["latitude"]
lon = july4th["longitude"]
precip = july4th["precip"]

xi = np.linspace(lon.min(), lon.max(), 100)
yi = np.linspace(lat.min(), lat.max(), 100)
zi = griddata((lon, lat), precip, (xi[None, :], yi[:, None]), method="linear")

max_precip = precip.max()
levels = np.linspace(0.5, max_precip, 50) if max_precip > 0 else np.array([0, 1])
vmin_for_norm = 0.5
colors = ["lightgreen", "green", "yellow", "orange", "red", "darkred"]
custom_cmap = mcolors.LinearSegmentedColormap.from_list("green_yellow_red_darkred", colors)

cmap = custom_cmap
cmap_with_transparent_under = cmap.copy()
cmap_with_transparent_under.set_under(color="none", alpha=0)
norm = mcolors.Normalize(vmin=vmin_for_norm, vmax=max_precip)

proj = ccrs.PlateCarree()
fig, ax = plt.subplots(1, 1, figsize=(10, 8), subplot_kw={"projection": proj})

graph1 = ax.contourf(
    xi,
    yi,
    zi,
    cmap=cmap_with_transparent_under,
    transform=ccrs.PlateCarree(),
    levels=levels,
    norm=norm,
    extend="max",
)

ax.coastlines(resolution="10m")
ax.add_feature(cfeature.STATES, edgecolor="black", zorder=1)
ax.add_feature(cfeature.OCEAN, facecolor="lightsteelblue", zorder=0)
ax.add_feature(cfeature.LAND, facecolor="white", edgecolor="black", zorder=0.5)

ax.set_extent([-101, -97, 28, 32], ccrs.PlateCarree())

try:
    rivers = gpd.read_file(riverfile)
    if rivers.crs is None or rivers.crs != ccrs.PlateCarree():
        rivers = rivers.to_crs(ccrs.PlateCarree())

    rivers.plot(
        ax=ax,
        edgecolor="blue",
        facecolor="none",
        linewidth=0.5,
        zorder=4,
        label="Guadalupe River",
    )
    print(f"Successfully loaded and plotted Guadalupe River from: {riverfile}")

except Exception as e:
    print(f"Error loading or plotting Guadalupe River shapefile: {e}")
    print(f"Please ensure you have geopandas installed and the path '{riverfile}' is correct.")
    print("If you cannot find a specific shapefile, cfeature.RIVERS adds general rivers.")

kerrville_lat = 30.0474
kerrville_lon = -99.1403
ax.scatter(
    kerrville_lon,
    kerrville_lat,
    color="black",
    marker="o",
    s=30,
    edgecolor="white",
    linewidth=1,
    transform=ccrs.PlateCarree(),
    zorder=5,
    label="Kerrville",
)
ax.text(
    kerrville_lon + 0.01,
    kerrville_lat + 0.005,
    "Kerrville",
    fontsize=10,
    color="black",
    horizontalalignment="left",
    verticalalignment="bottom",
    transform=ccrs.PlateCarree(),
    zorder=5,
)

hunt_lat = 30.0710
hunt_lon = -99.3380
ax.scatter(
    hunt_lon,
    hunt_lat,
    color="black",
    marker="o",
    s=30,
    edgecolor="white",
    linewidth=1,
    transform=ccrs.PlateCarree(),
    zorder=5,
    label="Hunt",
)
ax.text(
    hunt_lon + 0.01,
    hunt_lat + 0.005,
    "Hunt",
    fontsize=10,
    color="black",
    horizontalalignment="left",
    verticalalignment="bottom",
    transform=ccrs.PlateCarree(),
    zorder=5,
)

comfort_lat = 29.9677
comfort_lon = -98.9050
ax.scatter(
    comfort_lon,
    comfort_lat,
    color="black",
    marker="o",
    s=30,
    edgecolor="white",
    linewidth=1,
    transform=ccrs.PlateCarree(),
    zorder=5,
    label="Comfort",
)
ax.text(
    comfort_lon + 0.01,
    comfort_lat + 0.005,
    "Comfort",
    fontsize=10,
    color="black",
    horizontalalignment="left",
    verticalalignment="bottom",
    transform=ccrs.PlateCarree(),
    zorder=5,
)


ax.text(
    kerrville_lon + 0.8,
    kerrville_lat - 0.5,
    "Guadalupe River",
    fontsize=10,
    color="blue",
    horizontalalignment="left",
    verticalalignment="top",
    transform=ccrs.PlateCarree(),
    zorder=5,
)

try:
    texas_counties = gpd.read_file(countyfile)

    if texas_counties.crs is None or texas_counties.crs != ccrs.PlateCarree():
        texas_counties = texas_counties.to_crs(ccrs.PlateCarree())

    texas_counties.plot(ax=ax, edgecolor="darkgray", facecolor="none", linewidth=0.5, zorder=1.2)
    print(f"Successfully loaded and plotted Texas counties from: {countyfile}")
except Exception as e:
    print(f"Error loading or plotting US counties shapefile: {e}")
    print(f"Please ensure you have geopandas installed, the path '{countyfile}' is correct")

ax.set_title("Precipitation, July 4th, 2025")
gl = ax.gridlines(
    draw_labels=True,
    crs=ccrs.PlateCarree(),
    linestyle="--",
    color="gray",
    xlocs=np.arange(-108, -92, 2),
    ylocs=np.arange(24, 38, 2),
)
gl.top_labels = False
gl.right_labels = False

cbar = fig.colorbar(graph1, label="Precipitation (inches)")
cbar_ax = cbar.ax
cbar_ax.yaxis.set_major_locator(mticker.MaxNLocator(nbins=5, integer=True))
plt.tight_layout()
plt.show()


EARTH_RADIUS_KM = 6371

kerrville_data = (
    precip_data.filter(pl.col("date") >= pl.datetime(1987, 1, 1))
    .with_columns(
        pl.col("Lat_N").str.replace_all(" ", "").cast(pl.Float64),
        pl.col("Lon_E").str.replace_all(" ", "").cast(pl.Float64),
        pl.col("precip").str.replace_all(" ", "").cast(pl.Float64),
    )
    .with_columns((pl.col("Lon_E") - 360).alias("longitude"), pl.col("Lat_N").alias("latitude"))
    .filter(pl.col("precip").is_not_null())
    .filter(pl.col("precip") > 0)
    .with_columns(
        [
            (pl.col("latitude").radians()).alias("lat_rad"),
            (pl.col("longitude").radians()).alias("lon_rad"),
            (pl.lit(kerrville_lat).radians()).alias("kerrville_lat_rad"),
            (pl.lit(kerrville_lon).radians()).alias("kerrville_lon_rad"),
        ]
    )
    .with_columns(
        [
            (
                ((pl.col("lat_rad") - pl.col("kerrville_lat_rad")).sin() / 2).pow(2)
                + (pl.col("kerrville_lat_rad")).cos()
                * (pl.col("lat_rad")).cos()
                * ((pl.col("lon_rad") - pl.col("kerrville_lon_rad")).sin() / 2).pow(2)
            ).alias("a_haversine"),
        ]
    )
    .with_columns(
        [
            (
                pl.lit(EARTH_RADIUS_KM)
                * 2
                * pl.arctan2(pl.col("a_haversine").sqrt(), (1 - pl.col("a_haversine")).sqrt())
            ).alias("distance_to_kerrville_km")
        ]
    )
    .filter(pl.col("distance_to_kerrville_km") <= 50)
    .select("date", "precip")
    .group_by(pl.col("date"))
    .agg(pl.max("precip"))
    .sort("precip", descending=True)
)
with open(kerrvilledischarge, "r", encoding="utf-8") as f:
    json_string_data = f.read()

json_data = json.loads(json_string_data)
df_raw = pl.DataFrame(json_data["value"]["timeSeries"])
kerrvilledischarge_df = (
    df_raw.select(
        [
            pl.col("sourceInfo").struct.field("siteName").alias("site_name"),
            pl.col("sourceInfo")
            .struct.field("siteCode")
            .list.eval(pl.element().struct.field("value"), parallel=True)
            .list.first()
            .alias("site_code"),
            pl.col("sourceInfo")
            .struct.field("geoLocation")
            .struct.field("geogLocation")
            .struct.field("latitude")
            .alias("latitude"),
            pl.col("sourceInfo")
            .struct.field("geoLocation")
            .struct.field("geogLocation")
            .struct.field("longitude")
            .alias("longitude"),
            pl.col("values").explode().struct.field("value").alias("daily_records_list"),
        ]
    )
    .explode("daily_records_list")
    .select(
        [
            "site_name",
            "site_code",
            "latitude",
            "longitude",
            pl.col("daily_records_list").struct.field("value").cast(pl.Float64).alias("flow_value"),
            pl.col("daily_records_list")
            .struct.field("dateTime")
            .str.to_datetime()
            .alias("date_time"),
        ]
    )
)

with open(huntdischarge, "r", encoding="utf-8") as f:
    json_string_data = f.read()

json_data = json.loads(json_string_data)
df_raw = pl.DataFrame(json_data["value"]["timeSeries"])
huntdischarge_df = (
    df_raw.select(
        [
            pl.col("sourceInfo").struct.field("siteName").alias("site_name"),
            pl.col("sourceInfo")
            .struct.field("siteCode")
            .list.eval(pl.element().struct.field("value"), parallel=True)
            .list.first()
            .alias("site_code"),
            pl.col("sourceInfo")
            .struct.field("geoLocation")
            .struct.field("geogLocation")
            .struct.field("latitude")
            .alias("latitude"),
            pl.col("sourceInfo")
            .struct.field("geoLocation")
            .struct.field("geogLocation")
            .struct.field("longitude")
            .alias("longitude"),
            pl.col("values").explode().struct.field("value").alias("daily_records_list"),
        ]
    )
    .explode("daily_records_list")
    .select(
        [
            "site_name",
            "site_code",
            "latitude",
            "longitude",
            pl.col("daily_records_list").struct.field("value").cast(pl.Float64).alias("flow_value"),
            pl.col("daily_records_list")
            .struct.field("dateTime")
            .str.to_datetime()
            .alias("date_time"),
        ]
    )
)

with open(comfortdischarge, "r", encoding="utf-8") as f:
    json_string_data = f.read()

json_data = json.loads(json_string_data)
df_raw = pl.DataFrame(json_data["value"]["timeSeries"])
comfortdischarge_df = (
    df_raw.select(
        [
            pl.col("sourceInfo").struct.field("siteName").alias("site_name"),
            pl.col("sourceInfo")
            .struct.field("siteCode")
            .list.eval(pl.element().struct.field("value"), parallel=True)
            .list.first()
            .alias("site_code"),
            pl.col("sourceInfo")
            .struct.field("geoLocation")
            .struct.field("geogLocation")
            .struct.field("latitude")
            .alias("latitude"),
            pl.col("sourceInfo")
            .struct.field("geoLocation")
            .struct.field("geogLocation")
            .struct.field("longitude")
            .alias("longitude"),
            pl.col("values").explode().struct.field("value").alias("daily_records_list"),
        ]
    )
    .explode("daily_records_list")
    .select(
        [  # Explode THIS list
            "site_name",
            "site_code",
            "latitude",
            "longitude",
            pl.col("daily_records_list").struct.field("value").cast(pl.Float64).alias("flow_value"),
            pl.col("daily_records_list")
            .struct.field("dateTime")
            .str.to_datetime()
            .alias("date_time"),
        ]
    )
)

with open(kerrvillegage, "r", encoding="utf-8") as f:
    json_string_data = f.read()

json_data = json.loads(json_string_data)
df_raw = pl.DataFrame(json_data["value"]["timeSeries"])
kerrvillegage_df = (
    df_raw.select(
        [
            pl.col("sourceInfo").struct.field("siteName").alias("site_name"),
            pl.col("sourceInfo")
            .struct.field("siteCode")
            .list.eval(pl.element().struct.field("value"), parallel=True)
            .list.first()
            .alias("site_code"),
            pl.col("sourceInfo")
            .struct.field("geoLocation")
            .struct.field("geogLocation")
            .struct.field("latitude")
            .alias("latitude"),
            pl.col("sourceInfo")
            .struct.field("geoLocation")
            .struct.field("geogLocation")
            .struct.field("longitude")
            .alias("longitude"),
            pl.col("values").explode().struct.field("value").alias("daily_records_list"),
        ]
    )
    .explode("daily_records_list")
    .select(
        [
            "site_name",
            "site_code",
            "latitude",
            "longitude",
            pl.col("daily_records_list")
            .struct.field("value")
            .cast(pl.Float64)
            .alias("gage_height"),
            pl.col("daily_records_list")
            .struct.field("dateTime")
            .str.to_datetime()
            .alias("date_time"),
        ]
    )
)
num_top_readings = 10
top_readings = kerrvillegage_df.sort(by="gage_height", descending=True).head(num_top_readings)

top_readings_formatted = top_readings.with_columns(
    pl.col("date_time").dt.strftime("%B %d, %Y").alias("formatted_date_time")
)
top_readings_pd = top_readings_formatted.to_pandas()
plt.figure(figsize=(12, 7))

bars = plt.bar(
    top_readings_pd["formatted_date_time"],
    top_readings_pd["gage_height"],
    color="royalblue",
)
for bar in bars:
    yval = bar.get_height()
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        yval * 0.8,
        round(yval, 1),
        ha="center",
        va="center",
        color="white",
        fontsize=10,
        fontweight="bold",
    )
plt.xlabel("Date", fontsize=12)
plt.ylabel("Gage Height (ft)", fontsize=12)
plt.title(
    f"Top {num_top_readings} Gage Height Readings for {top_readings_pd['site_name'].iloc[0]} (since 1997-10-02)",  # noqa: E501
    fontsize=14,
)
plt.xticks(rotation=45, ha="right", fontsize=10)
plt.yticks(fontsize=10)
plt.grid(axis="y", linestyle="--", alpha=0.7)
plt.tight_layout()

plt.show()

num_top_readings = 10
top_readings = kerrvilledischarge_df.sort(by="flow_value", descending=True).head(num_top_readings)

top_readings_formatted = top_readings.with_columns(
    pl.col("date_time").dt.strftime("%B %d, %Y").alias("formatted_date_time")
)
top_readings_pd = top_readings_formatted.to_pandas()
plt.figure(figsize=(12, 7))

bars = plt.bar(
    top_readings_pd["formatted_date_time"],
    top_readings_pd["flow_value"],
    color="darkmagenta",
)
for bar in bars:
    yval = bar.get_height()
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        yval * 0.8,
        f"{yval:,.0f}",
        ha="center",
        va="center",
        color="white",
        fontsize=10,
        fontweight="bold",
    )
plt.xlabel("Date", fontsize=12)
plt.ylabel("Discharge (ft³/s)", fontsize=12)
plt.title(
    f"Top {num_top_readings} Discharge Readings for {top_readings_pd['site_name'].iloc[0]} (limited data before 1997)",  # noqa: E501
    fontsize=14,
)
plt.xticks(rotation=45, ha="right", fontsize=10)
plt.yticks(fontsize=10)
formatter = mticker.FuncFormatter(lambda x, p: f"{x:,.0f}")
plt.gca().yaxis.set_major_formatter(formatter)
plt.grid(axis="y", linestyle="--", alpha=0.7)
plt.tight_layout()

plt.show()

num_top_readings = 10
top_readings = huntdischarge_df.sort(by="flow_value", descending=True).head(num_top_readings)

top_readings_formatted = top_readings.with_columns(
    pl.col("date_time").dt.strftime("%B %d, %Y").alias("formatted_date_time")
)
top_readings_pd = top_readings_formatted.to_pandas()
plt.figure(figsize=(12, 7))

bars = plt.bar(
    top_readings_pd["formatted_date_time"],
    top_readings_pd["flow_value"],
    color="darkmagenta",
)
for bar in bars:
    yval = bar.get_height()
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        yval * 0.8,
        f"{yval:,.0f}",
        ha="center",
        va="center",
        color="white",
        fontsize=10,
        fontweight="bold",
    )
plt.xlabel("Date", fontsize=12)
plt.ylabel("Discharge (ft³/s)", fontsize=12)
plt.title(
    f"Top {num_top_readings} Discharge Readings for {top_readings_pd['site_name'].iloc[0]} (limited data before 2002)",  # noqa: E501
    fontsize=14,
)
plt.xticks(rotation=45, ha="right", fontsize=10)
plt.yticks(fontsize=10)
formatter = mticker.FuncFormatter(lambda x, p: f"{x:,.0f}")
plt.grid(axis="y", linestyle="--", alpha=0.7)
plt.tight_layout()

plt.show()

num_top_readings = 10
top_readings = comfortdischarge_df.sort(by="flow_value", descending=True).head(num_top_readings)

top_readings_formatted = top_readings.with_columns(
    pl.col("date_time").dt.strftime("%B %d, %Y").alias("formatted_date_time")
)
top_readings_pd = top_readings_formatted.to_pandas()
plt.figure(figsize=(12, 7))

bars = plt.bar(
    top_readings_pd["formatted_date_time"],
    top_readings_pd["flow_value"],
    color="darkmagenta",
)
for bar in bars:
    yval = bar.get_height()
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        yval * 0.8,
        f"{yval:,.0f}",
        ha="center",
        va="center",
        color="white",
        fontsize=10,
        fontweight="bold",
    )
plt.xlabel("Date", fontsize=12)
plt.ylabel("Discharge (ft³/s)", fontsize=12)
plt.title(
    f"Top {num_top_readings} Discharge Readings for {top_readings_pd['site_name'].iloc[0]} (limited data before 2002)",  # noqa: E501
    fontsize=14,
)
plt.xticks(rotation=45, ha="right", fontsize=10)
plt.yticks(fontsize=10)
formatter = mticker.FuncFormatter(lambda x, p: f"{x:,.0f}")
plt.grid(axis="y", linestyle="--", alpha=0.7)
plt.tight_layout()

plt.show()
