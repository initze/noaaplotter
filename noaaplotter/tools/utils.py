#!/usr/bin/python
# -*- coding: utf-8 -*-

########################
# Credits here
# author: Ingmar Nitze, Alfred Wegener Institute for Polar and Marine Research
# contact: ingmar.nitze@awi.de
# version: 2020-12-09

########################
import datetime as dt

import pandas as pd


def parse_dates(date):
    """

    :param date:
    :return:
    """
    if isinstance(date, str):
        return dt.datetime.strptime(date, "%Y-%m-%d")
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
        return dt.datetime.strptime(date, "%Y-%m")
    elif isinstance(date, dt.datetime):
        return date
    else:
        raise ('Wrong date format. Either use native datetime format or "YYYY-mm-dd"')


def assign_numeric_datatypes(df):
    for col in df.columns:
        if df[col].dtype == "object":
            try:
                df[col] = pd.to_numeric(df[col])
            except:
                pass
    return df
