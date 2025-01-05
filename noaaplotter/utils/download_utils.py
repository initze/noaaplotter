import datetime as dt
import json
import os
from datetime import datetime, timedelta

import ee
import geemap
import numpy as np
import pandas as pd
import polars as pl
import requests
import tqdm
from joblib import Parallel, delayed

from noaaplotter.utils.utils import assign_numeric_datatypes


# move some logic outside
def download_from_noaa(
    output_file,
    start_date,
    end_date,
    datatypes,
    loc_name,
    station_id,
    noaa_api_token,
    n_jobs=4,
):
    # Check if file exists and load it
    if os.path.exists(output_file):
        existing_df = pl.read_parquet(output_file).drop_nulls(subset='STATION')
        existing_dates = set(existing_df['DATE'].to_list())
    else:
        existing_df = None
        existing_dates = set()

    # Convert datestrings to datetime
    dt_start = datetime.strptime(start_date, "%Y-%m-%d")
    dt_end = datetime.strptime(end_date, "%Y-%m-%d")

    # Calculate date range
    all_dates = set(pd.date_range(start=dt_start, end=dt_end).strftime("%Y-%m-%d"))
    missing_dates = sorted(list(all_dates - existing_dates))

    if not missing_dates:
        print("No new data to download.")
        return 0

    # Find contiguous date ranges to download
    date_ranges = []
    range_start = missing_dates[0]
    prev_date = datetime.strptime(missing_dates[0], "%Y-%m-%d")

    for date_str in missing_dates[1:] + [None]:  # Add None to handle the last range
        if date_str is None or datetime.strptime(date_str, "%Y-%m-%d") - prev_date > timedelta(days=1):
            date_ranges.append((range_start, prev_date.strftime("%Y-%m-%d")))
            if date_str is not None:
                range_start = date_str
        prev_date = datetime.strptime(date_str, "%Y-%m-%d") if date_str else None

    # Data Loading
    print("Downloading missing data through NOAA API")
    all_new_data = []

    for start, end in date_ranges:
        print(f"Downloading data from {start} to {end}")
        n_days = (datetime.strptime(end, "%Y-%m-%d") - datetime.strptime(start, "%Y-%m-%d")).days + 1
        split_size = np.floor(1000 / len(datatypes))
        split_range = np.arange(0, n_days, split_size)

        datasets_list = Parallel(n_jobs=n_jobs)(
            delayed(dl_noaa_api)(
                i, datatypes, station_id, noaa_api_token, start, end, split_size
            )
            for i in tqdm.tqdm(split_range[:])
        )

        # Drop empty/None from datasets_list
        datasets_list = [i for i in datasets_list if i is not None]
        all_new_data.extend(datasets_list)

    # Merge subsets and create DataFrame
    df = pd.concat(all_new_data)

    df_pivot = assign_numeric_datatypes(df)
    df_pivot["DATE"] = df_pivot.apply(
        lambda x: datetime.fromisoformat(x["DATE"]).strftime("%Y-%m-%d"), axis=1
    )

    df_pivot = df_pivot.reset_index(drop=False)
    dr = pd.DataFrame(pd.date_range(start=start_date, end=end_date), columns=["DATE"])
    dr["DATE"] = dr["DATE"].astype(str)
    df_merged = pd.concat(
        [df_pivot.set_index("DATE"), dr.set_index("DATE")],
        join="outer",
        axis=1,
        sort=True,
    )
    df_merged["DATE"] = df_merged.index
    df_merged["NAME"] = loc_name
    if "TAVG" not in df_merged.columns:
        df_merged["TAVG"] = None
    if "SNWD" not in df_merged.columns:
        df_merged["SNWD"] = None
    final_cols = ["STATION", "NAME", "DATE", "PRCP", "SNWD", "TAVG", "TMAX", "TMIN"]
    df_final = df_merged[final_cols]
    df_final = df_final.replace({np.nan: None})

    # Merge with existing data if it exists
    if existing_df is not None:
        df_final = pd.concat([existing_df.to_pandas(), df_final]).drop_duplicates(subset=["DATE"], keep="last")

    print(f"Saving data to {output_file}")
    df_final.to_parquet(output_file)
    return 0



def dl_noaa_api(i, dtypes, station_id, Token, date_start, date_end, split_size):
    """
    function to download from NOAA API
    """
    dt_start = dt.datetime.strptime(date_start, "%Y-%m-%d")
    dt_end = dt.datetime.strptime(date_end, "%Y-%m-%d")

    split_start = dt_start + timedelta(days=i)
    split_end = dt_start + timedelta(days=i + split_size - 1)
    if split_end > dt_end:
        split_end = dt_end

    date_start_split = split_start.strftime("%Y-%m-%d")
    date_end_split = split_end.strftime("%Y-%m-%d")

    # make the api call
    request_url = "https://www.ncei.noaa.gov/access/services/data/v1"
    request_params = dict(
        dataset="daily-summaries",
        dataTypes=dtypes,  # ['PRCP', 'TMIN', 'TMAX'],
        stations=station_id,
        limit=1000,
        startDate=date_start_split,
        endDate=date_end_split,
        units="metric",
        format="json",
    )
    r = requests.get(request_url, params=request_params, headers={"token": Token})

    # workaround to skip empty returns (no data within period)
    try:
        # load the api response as a json
        d = json.loads(r.text)
        result = pd.DataFrame(d)
    except json.JSONDecodeError:
        print(
            f"Warning: No data available for period {date_start_split} to {date_end_split}. Skipping."
        )
        result = None
    return result


def download_era5_from_gee(latitude, longitude, end_date, start_date, output_file):
    ee.Initialize()
    EE_LAYER = "ECMWF/ERA5/DAILY"
    location = ee.Geometry.Point([longitude, latitude])
    # load ImageCollection
    col = (
        ee.ImageCollection(EE_LAYER)
        .filterBounds(location)
        .filterDate(start_date, end_date)
    )
    # Download data
    print("Start downloading daily ERA5 data.")
    print(
        "Download may take a while.\n1yr: ~5 seconds\n10yrs: ~35 seconds\n50yrs: ~8 min"
    )
    result = geemap.extract_pixel_values(col, region=location)
    out_dict = result.getInfo()
    df_gee = pd.DataFrame(data=[out_dict.keys(), out_dict.values()]).T
    # parse dates and values
    df_gee["time"] = df_gee[0].apply(lambda x: f"{x[:4]}-{x[4:6]}-{x[6:8]}")
    df_gee["feature"] = df_gee[0].apply(lambda x: x[9:])
    df_gee["value"] = df_gee[1]
    df = df_gee.pivot_table(
        values="value", columns=["feature"], index="time"
    )  # .reset_index(drop=False)
    # #### recalculate values
    df_new = pd.DataFrame(index=df.index)
    temperature_cols = [
        "mean_2m_air_temperature",
        "minimum_2m_air_temperature",
        "maximum_2m_air_temperature",
        "dewpoint_2m_temperature",
    ]
    precipitation_cols = ["total_precipitation"]
    df_joined = (
        df_new.join(df[temperature_cols] - 273.15)
        .join(df[precipitation_cols] * 1e3)
        .reset_index(drop=False)
    )
    # Create Output
    rename_dict = {
        "time": "DATE",
        "total_precipitation": "PRCP",
        "mean_2m_air_temperature": "TAVG",
        "maximum_2m_air_temperature": "TMAX",
        "minimum_2m_air_temperature": "TMIN",
    }
    df_renamed = df_joined.rename(columns=rename_dict)
    df_renamed["NAME"] = ""
    df_renamed["STATION"] = ""
    df_renamed["SNWD"] = ""
    output_cols = ["STATION", "NAME", "DATE", "PRCP", "SNWD", "TAVG", "TMAX", "TMIN"]
    df_save = df_renamed[output_cols].astype(str)
    df_save.to_csv(output_file, index=False)
