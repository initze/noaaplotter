#!/usr/bin/python
# -*- coding: utf-8 -*-

########################
# Credits here
# author: Ingmar Nitze, Alfred Wegener Institute for Polar and Marine Research
# contact: ingmar.nitze@awi.de
# version: 2020-12-09

########################
import datetime as dt
from datetime import timedelta
import requests, json
import pandas as pd


#import datetime


def parse_dates(date):
    """

    :param date:
    :return:
    """
    if isinstance(date, str):
        return dt.datetime.strptime(date, '%Y-%m-%d')
    elif isinstance(date, dt.datetime) or isinstance(date, dt.date):
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


def dl_noaa_api(i, dtypes, station_id, Token, date_start, date_end, split_size):
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
    request_url = 'https://www.ncei.noaa.gov/access/services/data/v1'
    request_params = dict(
        dataset = 'daily-summaries',
        dataTypes = dtypes,#['PRCP', 'TMIN', 'TMAX'],
        stations = station_id,
        limit = 1000,
        startDate = date_start_split,
        endDate= date_end_split,
        units='metric',
        format='json'
    )
    r = requests.get(
        request_url,
        params=request_params,
        headers={'token': Token})

    # workaround to skip empty returns (no data within period)
    try:
            # load the api response as a json
        d = json.loads(r.text)
        result = pd.DataFrame(d)
    except json.JSONDecodeError:
        print(f"Warning: No data available for period {date_start_split} to {date_end_split}. Skipping.")
        result = None
    return result


def assign_numeric_datatypes(df):
    for col in df.columns:
        if df[col].dtype == 'object':
            try:
                df[col] = pd.to_numeric(df[col])
            except:
                pass
    return df