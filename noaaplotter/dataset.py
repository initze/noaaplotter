#!/usr/bin/python
# -*- coding: utf-8 -*-

########################
# Credits here
# author: Ingmar Nitze, Alfred Wegener Institute for Polar and Marine Research
# contact: ingmar.nitze@awi.de
# version: 2020-04-25

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
        self._validate_location()
        self._update_datatypes()
        self._get_datestring()
        self._get_tmean()
        self._remove_feb29()
        self._filter_to_location()

    def print_locations(self):
        """
        Print all locations names
        """
        print(self.data['NAME'].unique())

    def _load_file(self):
        """
        load csv file into Pandas DataFrame
        :return:
        """
        self.data = pd.read_csv(self.input_filepath)

    def _validate_location(self):
        """
        raise error and message if location name cannot be found
        :return:
        """
        filt = self.data['NAME'].str.lower().str.contains(self.location.lower())
        if filt.sum() == 0:
            raise ValueError('Location Name is not valid! Valid Location identifiers: {0}'
                             .format(self.data['NAME'].unique()))

    def _update_datatypes(self):
        """
        define 'DATE' as datetime
        :return:
        """
        self.data['DATE'] = pd.to_datetime(self.data['DATE'])

    def _get_datestring(self):
        """
        write specific date formats
        :return:
        """
        self.data['DATE_MD'] = self.data['DATE'].dt.strftime('%m-%d')
        self.data['DATE_YM'] = self.data['DATE'].dt.strftime('%Y-%m')
        self.data['DATE_M'] = self.data['DATE'].dt.strftime('%m')

    def _get_tmean(self):
        """
        calculate mean daily temperature from min and max
        :return:
        """
        # TODO: check for cases where TMIN and TMAX are empty (e.g. Schonefeld). There TAVG is the main field
        self.data['TMEAN'] = self.data[['TMIN', 'TMAX']].mean(axis=1)

    def _remove_feb29(self):
        """
        Function to remove February 29 from the data
        :return:
        """
        if self.remove_feb29:
            self.data = self.data[self.data['DATE_MD'] != '02-29']

    def _filter_to_location(self):
        """
        Filter dataset to the defined location
        :return:
        """
        if self.location:
            filt = self.data['NAME'].str.lower().str.contains(self.location.lower())
            if len(filt) > 0:
                self.data = self.data.loc[filt]
            else:
                raise ValueError('Location Name is not valid')

    def filter_to_climate(self, climate_start, climate_end):
        """
        Function to create filtered dataset covering the defined climate normal period
        :return:
        """
        df_clim = self.data[(self.data['DATE'] >= climate_start) & (self.data['DATE'] <= climate_end)]
        return df_clim

    @staticmethod
    def get_monthly_stats(df):
        """
        calculate monthly statistics
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


class NOAAPlotterDailyClimateDataset(object):
    def __init__(self, daily_dataset, start='1981-01-01', end='2010-12-31', filtersize=7, impute_feb29=True):
        """
        :param start:
        :param end:
        :param filtersize:
        :param impute_feb29:
        """
        self.start = parse_dates(start)
        self.end = parse_dates(end)
        self.filtersize = filtersize
        self.impute_feb29 = impute_feb29
        self.daily_dataset = daily_dataset
        self.data_daily = None
        self.data = None
        self.date_range_valid = False

        # validate date range
        self._validate_date_range()
        # filter daily to date range
        self._filter_to_climate()
        # calculate daily statistics
        self._calculate_climate_statistics()
        # mean imputation for 29 February
        self._impute_feb29()
        # filter if desired
        self._run_filter()
        # make completeness report

    def _validate_date_range(self):
        if self.daily_dataset.data['DATE'].max() >= self.end:
            if self.daily_dataset.data['DATE'].min() <= self.end:
                self.date_range_valid = True
        else:
            raise ('Dataset is insufficient to calculate climate normals!')

    def _filter_to_climate(self):
        """
        calculate climate dataset
        :return:
        """
        df_clim = self.daily_dataset.data[(self.daily_dataset.data['DATE'] >= self.start) &
                                          (self.daily_dataset.data['DATE'] <= self.end)]
        df_clim = df_clim[(df_clim['DATE_MD'] != '02-29')]
        self.data_daily = df_clim

    def _calculate_climate_statistics(self):
        """
        Function to calculate major statistics
        :param self.data_daily:
        :type self.data_daily: pandas.DataFrame
        :return:
        """
        df_out = pd.DataFrame()
        df_out['tmean_doy_mean'] = self.data_daily[['DATE', 'TMEAN']].groupby(self.data_daily['DATE_MD']).mean().TMEAN
        df_out['tmean_doy_std'] = self.data_daily[['DATE', 'TMEAN']].groupby(self.data_daily['DATE_MD']).std().TMEAN
        df_out['tmean_doy_max'] = self.data_daily[['DATE', 'TMEAN']].groupby(self.data_daily['DATE_MD']).max().TMEAN
        df_out['tmean_doy_min'] = self.data_daily[['DATE', 'TMEAN']].groupby(self.data_daily['DATE_MD']).min().TMEAN
        df_out['tmax_doy_max'] = self.data_daily[['DATE', 'TMAX']].groupby(self.data_daily['DATE_MD']).max().TMAX
        df_out['tmax_doy_std'] = self.data_daily[['DATE', 'TMAX']].groupby(self.data_daily['DATE_MD']).std().TMAX
        df_out['tmin_doy_min'] = self.data_daily[['DATE', 'TMIN']].groupby(self.data_daily['DATE_MD']).min().TMIN
        df_out['tmin_doy_std'] = self.data_daily[['DATE', 'TMIN']].groupby(self.data_daily['DATE_MD']).std().TMIN
        if 'SNOW' in self.data_daily.columns:
            df_out['snow_doy_mean'] = self.data_daily[['DATE', 'SNOW']].groupby(self.data_daily['DATE_MD']).mean().SNOW
        self.data = df_out

    def _impute_feb29(self):
        """
        Function for mean imputation of February 29.
        :return:
        """
        if self.impute_feb29:
            self.data.loc['02-29'] = self.data.loc['02-28':'03-01'].mean(axis=0)
            self.data.sort_index(inplace=True)

    def _run_filter(self):
        """
        Function to run rolling mean filter on climate series to smooth out short fluctuations
        :return:
        """
        if self.filtersize % 2 != 0:
            data_roll = pd.concat([self.data.iloc[-self.filtersize:],
                                   self.data,
                                   self.data[:self.filtersize]]).rolling(self.filtersize).mean()
            self.data = data_roll[self.filtersize: -self.filtersize]

    def _make_report(self):
        """
        Function to create report on climate data completeness
        :return:
        """
        # input climate series (e.g. 1981-01-01 - 2010-12-31)
        pass


class NOAAPlotterMonthlyClimateDataset(object):
    def __init__(self, start, end, filtersize, feb29):
        self.start = start
        self.end = end
        self.filtersize = filtersize
        self.feb29 = feb29
        pass

    def from_daily_dataset(self, daily_dataset):
        pass
