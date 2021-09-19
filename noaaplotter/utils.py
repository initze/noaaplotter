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
from datetime import timedelta
import requests, json


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


def download_from_noaa(station_id, token):

    pass
    #return df


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