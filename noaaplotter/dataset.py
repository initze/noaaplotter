#!/usr/bin/python
# -*- coding: utf-8 -*-

########################
# Credits here
# author: Ingmar Nitze, Alfred Wegener Institute for Polar and Marine Research
# contact: ingmar.nitze@awi.de
# version: 2020-12-09

########################
import numpy as np
import os
from .utils import *
numeric_only = True

class NOAAPlotterDailySummariesDataset(object):
    """
    This class/module creates nice plots of observed weather data from NOAA
    """

    def __init__(self,
                 input_filepath=None,
                 location=None,
                 remove_feb29=False):
        self.input_switch = None
        self.input_filepath = input_filepath
        self.location = location
        self.noaa_token = None
        self.noaa_location = None
        self.remove_feb29 = remove_feb29
        self.data = None
        self._check_data_loading()
        if self.input_switch == 'file':
            self._load_file()
        elif self.input_switch == 'noaa_api':
            self._load_noaa()
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

    def _check_data_loading(self):
        """
        function check if all requirements for loading options are met
        File loading:
        * input_filepath
        """
        if os.path.exists(self.input_filepath):
            self.input_switch = 'file'
        elif self.noaa_token and self.noaa_location:
            self.input_switch = 'noaa_api'
        else:
            raise ImportError("Please enter either correct file path or noaa station_id and API token")

    def _load_file(self):
        """
        load csv file into Pandas DataFrame
        :return:
        """
        self.data = pd.read_csv(self.input_filepath)

    def _load_noaa(self):
        """
        load data through NOAA API
        """
        pass

    def _save_noaa(self):
        """
        save loaded NOAA API data to temporary csv file
        """

    def _validate_location(self):
        """
        raise error and message if location name cannot be found
        :return:
        """
        if not self.location and len(pd.unique(self.data['NAME']) == 1):
            pass
        elif not self.location and len(pd.unique(self.data['NAME']) > 1):
            raise ValueError(
                'There is more than one location in the dataset. Please choose a location using the -loc option! '
                'Valid Location identifiers: {0} '
                .format(self.data['NAME'].unique()))
        else:
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
        df_out['tmean_doy_mean'] = df[['DATE', 'TMEAN']].groupby(df['DATE_YM']).mean(numeric_only=numeric_only).TMEAN
        df_out['tmean_doy_std'] = df[['DATE', 'TMEAN']].groupby(df['DATE_YM']).std(numeric_only=numeric_only).TMEAN
        df_out['tmax_doy_max'] = df[['DATE', 'TMAX']].groupby(df['DATE_YM']).max(numeric_only=numeric_only).TMAX
        df_out['tmax_doy_std'] = df[['DATE', 'TMAX']].groupby(df['DATE_YM']).std(numeric_only=numeric_only).TMAX
        df_out['tmin_doy_min'] = df[['DATE', 'TMIN']].groupby(df['DATE_YM']).min(numeric_only=numeric_only).TMIN
        df_out['tmin_doy_std'] = df[['DATE', 'TMIN']].groupby(df['DATE_YM']).std(numeric_only=numeric_only).TMIN
        if 'SNOW' in df.columns:
            df_out['snow_doy_mean'] = df[['DATE', 'SNOW']].groupby(df['DATE_YM']).mean(numeric_only=numeric_only).SNOW
        df_out['prcp_sum'] = df[['DATE', 'PRCP']].groupby(df['DATE_YM']).sum(numeric_only=numeric_only).PRCP
        return df_out

    @staticmethod
    def get_monthy_climate(df):
        """
        :param df:
        :return:
        """
        df_out = pd.DataFrame()
        df = df.data
        df['Month'] = df.reset_index().apply(lambda x: int(x['DATE_MD'][:2]), axis=1).values
        df_out['tmean_mean'] = df[['Month', 'TMEAN']].groupby(df['Month']).mean(numeric_only=numeric_only).TMEAN
        df_out['tmean_std'] = df[['Month', 'TMEAN']].groupby(df['Month']).std(numeric_only=numeric_only).TMEAN
        df_out['tmax_max'] = df[['Month', 'TMAX']].groupby(df['Month']).max(numeric_only=numeric_only).TMAX
        df_out['tmax_std'] = df[['Month', 'TMAX']].groupby(df['Month']).std(numeric_only=numeric_only).TMAX
        df_out['tmin_min'] = df[['Month', 'TMIN']].groupby(df['Month']).min(numeric_only=numeric_only).TMIN
        df_out['tmin_std'] = df[['Month', 'TMIN']].groupby(df['Month']).std(numeric_only=numeric_only).TMIN
        if 'SNOW' in df.columns:
            df_out['snow_mean'] = df[['Month', 'SNOW']].groupby(df['Month']).mean(numeric_only=numeric_only).SNOW
        unique_years = len(np.unique(df.apply(lambda x: parse_dates_YM(x['DATE_YM']).year, axis=1)))
        df_out['prcp_mean'] = df[['Month', 'PRCP']].groupby(df['Month']).mean(numeric_only=numeric_only).PRCP * unique_years
        return df_out.reset_index(drop=False)


class NOAAPlotterDailyClimateDataset(object):
    # TODO: make main class sub subclasses for daily/monthly
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
        df_out['tmean_doy_mean'] = self.data_daily[['DATE', 'TMEAN']].groupby(self.data_daily['DATE_MD']).mean(numeric_only=numeric_only).TMEAN
        df_out['tmean_doy_std'] = self.data_daily[['DATE', 'TMEAN']].groupby(self.data_daily['DATE_MD']).std(numeric_only=numeric_only).TMEAN
        df_out['tmean_doy_max'] = self.data_daily[['DATE', 'TMEAN']].groupby(self.data_daily['DATE_MD']).max(numeric_only=numeric_only).TMEAN
        df_out['tmean_doy_min'] = self.data_daily[['DATE', 'TMEAN']].groupby(self.data_daily['DATE_MD']).min(numeric_only=numeric_only).TMEAN
        df_out['tmax_doy_max'] = self.data_daily[['DATE', 'TMAX']].groupby(self.data_daily['DATE_MD']).max(numeric_only=numeric_only).TMAX
        df_out['tmax_doy_std'] = self.data_daily[['DATE', 'TMAX']].groupby(self.data_daily['DATE_MD']).std(numeric_only=numeric_only).TMAX
        df_out['tmin_doy_min'] = self.data_daily[['DATE', 'TMIN']].groupby(self.data_daily['DATE_MD']).min(numeric_only=numeric_only).TMIN
        df_out['tmin_doy_std'] = self.data_daily[['DATE', 'TMIN']].groupby(self.data_daily['DATE_MD']).std(numeric_only=numeric_only).TMIN
        if 'SNOW' in self.data_daily.columns:
            df_out['snow_doy_mean'] = self.data_daily[['DATE', 'SNOW']].groupby(self.data_daily['DATE_MD']).mean(numeric_only=numeric_only).SNOW
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
    def __init__(self, daily_dataset, start='1981-01-01', end='2010-12-31', impute_feb29=True):
        self.daily_dataset = daily_dataset
        self.monthly_aggregate = None
        self.start = parse_dates(start)
        self.end = parse_dates(end)
        self.impute_feb29 = impute_feb29
        self._validate_date_range()

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

    def filter_to_date(self):
        """
        calculate climate dataset
        :return:
        """
        df_clim = self.daily_dataset.data[(self.daily_dataset.data['DATE'] >= self.start) &
                                          (self.daily_dataset.data['DATE'] <= self.end)]
        df_clim = df_clim[(df_clim['DATE_MD'] != '02-29')]
        return df_clim

    def _impute_feb29(self):
        """
        Function for mean imputation of February 29.
        :return:
        """
        pass

    def calculate_monthly_statistics(self):
        """
        Function to calculate monthly statistics.
        :return:
        """

        df_out = pd.DataFrame()
        data_filtered = self.filter_to_date()
        df_out['tmean_doy_mean'] = data_filtered[['DATE', 'TMEAN']].groupby(data_filtered['DATE_YM']).mean(numeric_only=numeric_only).TMEAN
        df_out['tmean_doy_std'] = data_filtered[['DATE', 'TMEAN']].groupby(data_filtered['DATE_YM']).std(numeric_only=numeric_only).TMEAN
        df_out['tmax_doy_max'] = data_filtered[['DATE', 'TMAX']].groupby(data_filtered['DATE_YM']).max(numeric_only=numeric_only).TMAX
        df_out['tmax_doy_std'] = data_filtered[['DATE', 'TMAX']].groupby(data_filtered['DATE_YM']).std(numeric_only=numeric_only).TMAX
        df_out['tmin_doy_min'] = data_filtered[['DATE', 'TMIN']].groupby(data_filtered['DATE_YM']).min(numeric_only=numeric_only).TMIN
        df_out['tmin_doy_std'] = data_filtered[['DATE', 'TMIN']].groupby(data_filtered['DATE_YM']).std(numeric_only=numeric_only).TMIN
        if 'SNOW' in data_filtered.columns:
            df_out['snow_doy_mean'] = data_filtered[['DATE', 'SNOW']].groupby(data_filtered['DATE_YM']).mean(numeric_only=numeric_only).SNOW
        df_out['prcp_sum'] = data_filtered[['DATE', 'PRCP']].groupby(data_filtered['DATE_YM']).sum().PRCP
        self.monthly_aggregate = df_out

    def calculate_monthly_climate(self):
        """
        Function to calculate monthly climate statistics.
        :return:
        """
        df_out = pd.DataFrame()
        data_filtered = self.filter_to_date()

        data_filtered['DATE'] = data_filtered.apply(lambda x: parse_dates_YM(x['DATE_YM']), axis=1)
        data_filtered['Month'] = data_filtered.apply(lambda x: parse_dates_YM(x['DATE_YM']).month, axis=1)
        data_filtered['Year'] = data_filtered.apply(lambda x: parse_dates_YM(x['DATE_YM']).year, axis=1)

        df_out['tmean_doy_mean'] = data_filtered[['DATE', 'TMEAN']].groupby(data_filtered['Month']).mean(numeric_only=numeric_only).TMEAN
        df_out['tmean_doy_std'] = data_filtered[['DATE', 'TMEAN']].groupby(data_filtered['Month']).std(numeric_only=numeric_only).TMEAN
        df_out['tmax_doy_max'] = data_filtered[['DATE', 'TMAX']].groupby(data_filtered['Month']).max(numeric_only=numeric_only).TMAX
        df_out['tmax_doy_std'] = data_filtered[['DATE', 'TMAX']].groupby(data_filtered['Month']).std(numeric_only=numeric_only).TMAX
        df_out['tmin_doy_min'] = data_filtered[['DATE', 'TMIN']].groupby(data_filtered['Month']).min(numeric_only=numeric_only).TMIN
        df_out['tmin_doy_std'] = data_filtered[['DATE', 'TMIN']].groupby(data_filtered['Month']).std(numeric_only=numeric_only).TMIN
        if 'SNOW' in data_filtered.columns:
            df_out['snow_doy_mean'] = data_filtered[['DATE', 'SNOW']].groupby(data_filtered['Month']).mean(numeric_only=numeric_only).SNOW
        df_out['prcp_sum'] = data_filtered[['DATE', 'PRCP']].groupby(data_filtered['Month']).mean(numeric_only=numeric_only).PRCP * 30
        # df_out = df_out.set_index('DATE_YM', drop=False)
        self.monthly_climate = df_out

    def _make_report(self):
        """
        Function to create report on climate data completeness
        :return:
        """
        # input climate series (e.g. 1981-01-01 - 2010-12-31)

        pass
