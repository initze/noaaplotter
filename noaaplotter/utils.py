#!/usr/bin/python
# -*- coding: utf-8 -*-

########################
# Credits here
# author: Ingmar Nitze, Alfred Wegener Institute for Polar and Marine Research
# contact: ingmar.nitze@awi.de
# version: 2020-01-28

########################
import pandas as pd


def parse_dates(date):
    """

    :param date:
    :return:
    """
    if isinstance(date, str):
        return pd.datetime.strptime(date, '%Y-%m-%d')
    elif isinstance(date, pd.datetime):
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
    trailing_values = []
    idxs = df.index
    for i in range(length, len(idxs.values)):
        trailing_values.append(df.loc[idxs[i-length:i]][feature].mean())
    df.loc[idxs[length:], new_feature] = trailing_values
    return df


def parse_dates_YM(date):
    """
    :param date:
    :return:
    """
    if isinstance(date, str):
        return pd.datetime.strptime(date, '%Y-%m')
    elif isinstance(date, pd.datetime):
        return date
    else:
        raise('Wrong date format. Either use native datetime format or "YYYY-mm-dd"')