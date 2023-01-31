#!/usr/bin/python
# -*- coding: utf-8 -*-

########################
# Credits here
# author: Ingmar Nitze, Alfred Wegener Institute for Polar and Marine Research
# contact: ingmar.nitze@awi.de
# version: 2020-12-09

########################
import pandas as pd
import datetime as dt
from datetime import timedelta, datetime
import requests, json
import os
import numpy as np
import pandas as pd
import tqdm
from joblib import delayed, Parallel
import csv
#import datetime


def parse_dates(date):
    """

    :param date:
    :return:
    """
    if isinstance(date, str):
        return dt.datetime.strptime(date, '%Y-%m-%d')
    elif isinstance(date, dt.datetime):
        return date
    else:
        raise ('Wrong date format. Either use native datetime format or "YYYY-mm-dd"')


def calc_trailing_mean(df, length, feature, new_feature):
    """
    :param df:
    :param length:
    :param feature:
    :param new_feature:
    :return:

    """
    df[new_feature] = df[feature].rolling(length).mean()
    return df


def parse_dates_YM(date):
    """
    :param date:
    :return:
    """
    if isinstance(date, str):
        return dt.datetime.strptime(date, '%Y-%m')
    elif isinstance(date, dt.datetime):
        return date
    else:
        raise('Wrong date format. Either use native datetime format or "YYYY-mm-dd"')


def dl_noaa_api(i, dtypes_string, station_id, Token, date_start, date_end, split_size):
    """
    function to download from NOAA API
    """
    dt_start = dt.datetime.strptime(date_start, '%Y-%m-%d')
    dt_end = dt.datetime.strptime(date_end, '%Y-%m-%d')

    split_start = dt_start + timedelta(days=i)
    split_end = dt_start + timedelta(days=i + split_size - 1)
    if split_end > dt_end:
        split_end = dt_end

    date_start_split = split_start.strftime('%Y-%m-%d')
    date_end_split = split_end.strftime('%Y-%m-%d')

    # make the api call
    r = requests.get(
        f'https://www.ncdc.noaa.gov/cdo-web/api/v2/data?datasetid=GHCND&{dtypes_string}&limit=1000&stationid={station_id}&startdate={date_start_split}&enddate={date_end_split}',
        headers={'token': Token})
    # load the api response as a json
    d = json.loads(r.text)

    # workaround to skip empty returns (no data within period)
    try:
        result = pd.DataFrame(d['results'])
    except:
        result = None
    return result


def download_from_noaa(output_file, start_date, end_date, datatypes, loc_name, station_id, noaa_api_token):
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
    datasets_list = Parallel(n_jobs=4)(
        delayed(dl_noaa_api)(i, dtypes_string, station_id, noaa_api_token, start_date, end_date, split_size)
        for i in tqdm.tqdm(split_range[:])
    )
    # Merge subsets and create DataFrame
    df = pd.concat(datasets_list)
    #### Pivot table to correct form
    df_pivot = df.pivot(index='date', columns='datatype', values='value')
    #### adapt  factor
    df_pivot.loc[:, :] /= 10
    df_pivot = df_pivot.reset_index(drop=False)
    df_pivot['DATE'] = df_pivot.apply(lambda x: datetime.fromisoformat(x['date']).strftime('%Y-%m-%d'), axis=1)
    dr = pd.DataFrame(pd.date_range(start=start_date, end=end_date), columns=['DATE'])
    dr['DATE'] = dr['DATE'].astype(str)
    df_merged = pd.concat([df_pivot.set_index('DATE'), dr.set_index('DATE')], join='outer', axis=1,
                          sort=True)
    df_merged['DATE'] = df_merged.index
    df_merged['STATION'] = station_id
    df_merged['NAME'] = loc_name
    df_merged['TAVG'] = None
    df_merged['SNWD'] = None
    final_cols = ["STATION", "NAME", "DATE", "PRCP", "SNWD", "TAVG", "TMAX", "TMIN"]
    df_final = df_merged[final_cols]
    df_final = df_final.replace({np.nan: None})
    print(f'Saving data to {output_file}')
    df_final.to_csv(output_file, index=False, quoting=csv.QUOTE_ALL)
    return 0