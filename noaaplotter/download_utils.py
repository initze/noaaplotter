import csv
import os
from datetime import datetime

import numpy as np
import pandas as pd
import tqdm
from joblib import Parallel, delayed

import geemap
import ee

from noaaplotter.utils import dl_noaa_api, assign_numeric_datatypes


def download_from_noaa(output_file, start_date, end_date, station_id, noaa_api_token, datatypes=['TMIN', 'TMAX', 'PRCP', 'SNOW'], loc_name='', n_jobs=4):
    # remove file if exists
    if os.path.exists(output_file):
        os.remove(output_file)
    # Make query string
    dtypes_string = '&'.join([f'datatypeid={dt}' for dt in datatypes])
    # convert datestring to dt
    dt_start = datetime.strptime(start_date, '%Y-%m-%d')
    dt_end = datetime.strptime(end_date, '%Y-%m-%d')
    # calculate number of days
    n_days = (dt_end - dt_start).days
    # calculate number of splits to fit into 1000 lines/rows
    split_size = np.floor(1000 / len(datatypes))
    # calculate splits
    split_range = np.arange(0, n_days, split_size)
    # Data Loading
    print('Downloading data through NOAA API')
    datasets_list = Parallel(n_jobs=n_jobs)(
        delayed(dl_noaa_api)(i, datatypes, station_id, noaa_api_token, start_date, end_date, split_size)
        for i in tqdm.tqdm(split_range[:])
    )
    # Merge subsets and create DataFrame
    df = pd.concat(datasets_list)

    df_pivot = assign_numeric_datatypes(df)
    df_pivot['DATE'] = df_pivot.apply(lambda x: datetime.fromisoformat(x['DATE']).strftime('%Y-%m-%d'), axis=1)

    df_pivot = df_pivot.reset_index(drop=False)
    dr = pd.DataFrame(pd.date_range(start=start_date, end=end_date), columns=['DATE'])
    dr['DATE'] = dr['DATE'].astype(str)
    df_merged = pd.concat([df_pivot.set_index('DATE'), dr.set_index('DATE')], join='outer', axis=1,
                          sort=True)
    df_merged['DATE'] = df_merged.index
    df_merged['NAME'] = loc_name
    df_merged['TAVG'] = None
    df_merged['SNWD'] = None
    final_cols = ["STATION", "NAME", "DATE", "PRCP", "SNWD", "TAVG", "TMAX", "TMIN"]
    df_final = df_merged[final_cols]
    df_final = df_final.replace({np.nan: None})
    print(f'Saving data to {output_file}')
    df_final.to_csv(output_file, index=False, quoting=csv.QUOTE_ALL)
    return 0


def download_era5_from_gee(latitude, longitude, end_date, start_date, output_file):
    ee.Initialize()
    EE_LAYER = 'ECMWF/ERA5/DAILY'
    location = ee.Geometry.Point([longitude, latitude])
    # load ImageCollection
    col = ee.ImageCollection(EE_LAYER).filterBounds(location).filterDate(start_date, end_date)
    # Download data
    print("Start downloading daily ERA5 data.")
    print("Download may take a while.\n1yr: ~5 seconds\n10yrs: ~35 seconds\n50yrs: ~8 min")
    result = geemap.extract_pixel_values(col, region=location)
    out_dict = result.getInfo()
    df_gee = pd.DataFrame(data=[out_dict.keys(), out_dict.values()]).T
    # parse dates and values
    df_gee['time'] = df_gee[0].apply(lambda x: f'{x[:4]}-{x[4:6]}-{x[6:8]}')
    df_gee['feature'] = df_gee[0].apply(lambda x: x[9:])
    df_gee['value'] = df_gee[1]
    df = df_gee.pivot_table(values='value', columns=['feature'], index='time')  # .reset_index(drop=False)
    # #### recalculate values
    df_new = pd.DataFrame(index=df.index)
    temperature_cols = ['mean_2m_air_temperature', 'minimum_2m_air_temperature', 'maximum_2m_air_temperature',
                        'dewpoint_2m_temperature']
    precipitation_cols = ['total_precipitation']
    df_joined = df_new.join(df[temperature_cols] - 273.15).join(df[precipitation_cols] * 1e3).reset_index(drop=False)
    # Create Output
    rename_dict = {'time': 'DATE', 'total_precipitation': 'PRCP', 'mean_2m_air_temperature': 'TAVG',
                   'maximum_2m_air_temperature': 'TMAX', 'minimum_2m_air_temperature': 'TMIN'}
    df_renamed = df_joined.rename(columns=rename_dict)
    df_renamed['NAME'] = ''
    df_renamed['STATION'] = ''
    df_renamed['SNWD'] = ''
    output_cols = ["STATION", "NAME", "DATE", "PRCP", "SNWD", "TAVG", "TMAX", "TMIN"]
    df_save = df_renamed[output_cols].astype(str)
    df_save.to_csv(output_file, index=False)