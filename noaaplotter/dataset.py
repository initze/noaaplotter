#!/usr/bin/python
# -*- coding: utf-8 -*-

########################
# Credits here
# author: Ingmar Nitze, Alfred Wegener Institute for Polar and Marine Research
# contact: ingmar.nitze@awi.de
# version: 2020-02-18

########################
import pandas as pd
import numpy as np
from .utils import *


class NOAAPlotterDailySummariesDataset(object):
    """
    This class/module creates nice plots of observed weather data from NOAA
    """
    def __init__(self,
                 input_filepath,
                 location=None,
                 remove_feb29=False):
        self.input_filepath = input_filepath
        self.location = location
        self.remove_feb29 = remove_feb29
        self.data = None
        self._load_file()
        self._update_datatypes()
        self._get_datestring()
        self._get_tmean()
        self._remove_feb29()
        self._filter_to_location()

    def print_locations(self):
        """
        Print all locations names
        """
        print(pd.unique(self.data['NAME']))

    def _load_file(self):
        """
        load csv file into Pandas DataFrame
        :return:
        """
        self.data = pd.read_csv(self.input_filepath)

    def _update_datatypes(self):
        """

        :return:
        """
        self.data['DATE'] = pd.to_datetime(self.data['DATE'])

    def _get_datestring(self):
        self.data['DATE_MD'] = self.data['DATE'].dt.strftime('%m-%d')
        self.data['DATE_YM'] = self.data['DATE'].dt.strftime('%Y-%m')
        self.data['DATE_M'] = self.data['DATE'].dt.strftime('%m')

    def _get_tmean(self):
        """
        calculate mean daily temperature from min and max
        :return:
        """
        self.data['TMEAN'] = self.data[['TMIN', 'TMAX']].mean(axis=1)

    def _remove_feb29(self):
        """

        :return:
        """
        if self.remove_feb29:
            self.data = self.data[~self.data['DATE_MD'] != '02-29']

    def _filter_to_location(self):
        """

        :return:
        """
        if self.location:
            filt = self.data['NAME'].str.lower().str.contains(self.location.lower())
            if len(filt) > 0:
                self.data = self.data.loc[filt]
            else:
                raise ValueError('Location Name is not valid')

    def _filter_to_climate(self, climate_start, climate_end):
        """

        :return:
        """
        df_clim = self.data[(self.data['DATE'] >= climate_start) & (self.data['DATE'] <= climate_end)]
        df_clim = df_clim[df_clim['DATE'].apply(lambda x: x.dayofyear != 366)]
        return df_clim

    @staticmethod
    def get_daily_stats(df):
        """

        :param df:
        :type df: pandas.DataFrame
        :return:
        """
        df_out = pd.DataFrame()
        df_out['tmean_doy_mean'] = df[['DATE', 'TMEAN']].groupby(df['DATE_MD']).mean().TMEAN
        df_out['tmean_doy_std'] = df[['DATE', 'TMEAN']].groupby(df['DATE_MD']).std().TMEAN
        df_out['tmean_doy_max'] = df[['DATE', 'TMEAN']].groupby(df['DATE_MD']).max().TMEAN
        df_out['tmean_doy_min'] = df[['DATE', 'TMEAN']].groupby(df['DATE_MD']).min().TMEAN
        df_out['tmax_doy_max'] = df[['DATE', 'TMAX']].groupby(df['DATE_MD']).max().TMAX
        df_out['tmax_doy_std'] = df[['DATE', 'TMAX']].groupby(df['DATE_MD']).std().TMAX
        df_out['tmin_doy_min'] = df[['DATE', 'TMIN']].groupby(df['DATE_MD']).min().TMIN
        df_out['tmin_doy_std'] = df[['DATE', 'TMIN']].groupby(df['DATE_MD']).std().TMIN
        if 'SNOW' in df.columns:
            df_out['snow_doy_mean'] = df[['DATE', 'SNOW']].groupby(df['DATE_MD']).mean().SNOW
        return df_out

    @staticmethod
    def get_monthly_stats(df):
        """

        :param df:
        :type df: pandas.DataFrame
        :return:
        """
        df_out = pd.DataFrame()
        df_out['tmean_doy_mean'] = df[['DATE', 'TMEAN']].groupby(df['DATE_YM']).mean().TMEAN
        df_out['tmean_doy_std'] = df[['DATE', 'TMEAN']].groupby(df['DATE_YM']).std().TMEAN
        df_out['tmax_doy_max'] = df[['DATE', 'TMAX']].groupby(df['DATE_YM']).max().TMAX
        df_out['tmax_doy_std'] = df[['DATE', 'TMAX']].groupby(df['DATE_YM']).std().TMAX
        df_out['tmin_doy_min'] = df[['DATE', 'TMIN']].groupby(df['DATE_YM']).min().TMIN
        df_out['tmin_doy_std'] = df[['DATE', 'TMIN']].groupby(df['DATE_YM']).std().TMIN
        if 'SNOW' in df.columns:
            df_out['snow_doy_mean'] = df[['DATE', 'SNOW']].groupby(df['DATE_YM']).mean().SNOW
        df_out['prcp_sum'] = df[['DATE', 'PRCP']].groupby(df['DATE_YM']).sum().PRCP
        return df_out

    @staticmethod
    def get_monthy_climate(df):
        """
        :param df:
        :return:
        """
        df_out = pd.DataFrame()
        df['Month'] = df.apply(lambda x: parse_dates_YM(x['DATE_YM']).month, axis=1)
        df_out['tmean_mean'] = df[['Month', 'TMEAN']].groupby(df['Month']).mean().TMEAN
        df_out['tmean_std'] = df[['Month', 'TMEAN']].groupby(df['Month']).std().TMEAN
        df_out['tmax_max'] = df[['Month', 'TMAX']].groupby(df['Month']).max().TMAX
        df_out['tmax_std'] = df[['Month', 'TMAX']].groupby(df['Month']).std().TMAX
        df_out['tmin_min'] = df[['Month', 'TMIN']].groupby(df['Month']).min().TMIN
        df_out['tmin_std'] = df[['Month', 'TMIN']].groupby(df['Month']).std().TMIN
        if 'SNOW' in df.columns:
            df_out['snow_mean'] = df[['Month', 'SNOW']].groupby(df['Month']).mean().SNOW
        unique_years = len(np.unique(df.apply(lambda x: parse_dates_YM(x['DATE_YM']).year, axis=1)))
        df_out['prcp_mean'] = df[['Month', 'PRCP']].groupby(df['Month']).mean().PRCP * unique_years
        return df_out.reset_index(drop=False)
