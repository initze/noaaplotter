#!/usr/bin/python
# -*- coding: utf-8 -*-

########################
# Credits here
# author: Ingmar Nitze, Alfred Wegener Institute for Polar and Marine Research
# contact: ingmar.nitze@awi.de
# version: 2020-04-25

########################
import pandas as pd
from matplotlib import pyplot as plt, dates
import numpy as np
from .utils import *
from .dataset import NOAAPlotterDailySummariesDataset as Dataset
from .dataset import NOAAPlotterDailyClimateDataset as DS_daily

pd.plotting.register_matplotlib_converters()


class NOAAPlotter(object):
    """
    This class/module creates nice plots of observed weather data from NOAA
    """

    def __init__(self,
                 input_filepath,
                 location=None,
                 remove_feb29=False,
                 climate_start=pd.datetime(1981, 1, 1),
                 climate_end=pd.datetime(2010, 12, 31),
                 climate_filtersize=7
                 ):
        """

        :param input_filepath: path to input file
        :type input_filepath: str
        :param location: name of location
        :type location: str, optional
        :param remove_feb29:
        :type remove_feb29: bool, optional
        :param climate_start: start date of climate period, defaults to 01-01-1981
        :type climate_start: datetime, optional
        :param climate_end: start date of climate period, defaults to 31-12-2010
        :type climate_end: datetime, optional
        """
        self.input_filepath = input_filepath
        self.location = location
        self.climate_start = climate_start
        self.climate_end = climate_end
        self.remove_feb29 = remove_feb29
        self.dataset = Dataset(input_filepath,
                               location=location,
                               remove_feb29=remove_feb29)
        self.df_clim_ = DS_daily(self.dataset, filtersize=climate_filtersize)

    def _make_short_dateseries(self, start_date, end_date):

        x_dates = pd.DataFrame()
        x_dates['DATE'] = pd.date_range(start=start_date, end=end_date)
        x_dates['DATE_MD'] = x_dates['DATE'].dt.strftime('%m-%d')
        # TODO: Filter Feb29
        if self.dataset.data['DATE'].max() >= end_date:
            x_dates_short = x_dates.set_index('DATE', drop=False).loc[pd.date_range(start=start_date,
                                                                                    end=end_date)]
        else:
            x_dates_short = x_dates.set_index('DATE', drop=False).loc[pd.date_range(start=start_date,
                                                                                    end=self.dataset.data[
                                                                                        'DATE'].max())]

        return x_dates, x_dates_short

    def plot_weather_series(self, start_date, end_date,
                            plot_tmax='auto', plot_tmin='auto',
                            plot_pmax='auto', plot_snowmax='auto',
                            plot_extrema=True, show_plot=True,
                            show_snow_accumulation=True, save_path=False,
                            figsize=(9, 6), legend_fontsize='x-small', dpi=300):
        """
        Plotting Function to show observed vs climate temperatures and snowfall
        :param dpi:
        :param legend_fontsize:
        :param figsize:
        :param start_date: start date of plot
        :type start_date: datetime, str
        :param end_date: end date of plot
        :type end_date: datetime, str
        :param plot_tmax:
        :type plot_tmax: int, float, str
        :param plot_tmin:
        :type plot_tmin: int, float, str
        :param plot_pmax:
        :type plot_pmax: int, float, str
        :param plot_snowmax:
        :type plot_snowmax: int, float, str
        :param plot_extrema:
        :type plot_extrema:
        :param show_plot:
        :type show_plot:
        :param show_snow_accumulation:
        :type show_snow_accumulation:
        :param save_path:
        :type save_path:
        :return:
        """
        start_date = parse_dates(start_date)
        end_date = parse_dates(end_date)
        x_dates, x_dates_short = self._make_short_dateseries(start_date, end_date)

        df_clim = self.df_clim_.data.loc[x_dates['DATE_MD']]

        df_clim['DATE'] = x_dates['DATE'].values
        df_clim = df_clim.set_index('DATE', drop=False)
        df_obs = self.dataset.data.set_index('DATE', drop=False).loc[x_dates_short['DATE']]

        clim_locs_short = x_dates_short['DATE']  # short series for incomplete years (actual data)

        # get mean and mean+-standard deviation of daily mean temperatures of climate series
        y_clim = df_clim['tmean_doy_mean']
        y_clim_std_hi = df_clim[['tmean_doy_mean', 'tmean_doy_std']].sum(axis=1)
        y_clim_std_lo = df_clim['tmean_doy_mean'] - df_clim['tmean_doy_std']

        # Prepare data for filled plot areas
        t_above = np.vstack([df_obs['TMEAN'].values, y_clim.loc[clim_locs_short].values]).max(axis=0)
        t_above_std = np.vstack([df_obs['TMEAN'].values, y_clim_std_hi.loc[clim_locs_short].values]).max(axis=0)
        t_below = np.vstack([df_obs['TMEAN'].values, y_clim.loc[clim_locs_short].values]).min(axis=0)
        t_below_std = np.vstack([df_obs['TMEAN'].values, y_clim_std_lo.loc[clim_locs_short].values]).min(axis=0)

        # Calculate the date of last snowfall and cumulative sum of snowfall
        if not show_snow_accumulation:
            None
        elif (show_snow_accumulation) and ('SNOW' in df_obs.columns):
            last_snow_date = df_obs[df_obs['SNOW'] > 0].iloc[-1]['DATE']
            snow_acc = np.cumsum(df_obs['SNOW'])
        elif ('SNOW' not in df_obs.columns):
            show_snow_accumulation = False
            raise Warning('No snow information available')

            # PLOT
        fig = plt.figure(figsize=figsize, dpi=dpi)
        ax = fig.add_subplot(211)
        ax2 = fig.add_subplot(212, sharex=ax)

        # climate series (red line)
        cm, = ax.plot(x_dates['DATE'], y_clim, c='k', alpha=0.5, lw=2)
        cm_hi, = ax.plot(x_dates['DATE'], y_clim_std_hi, c='r', ls='--', alpha=0.4, lw=1)
        cm_low, = ax.plot(x_dates['DATE'], y_clim_std_lo, c='r', ls='--', alpha=0.4, lw=1)

        # observed series (grey line)
        fb, = ax.plot(x_dates_short['DATE'], df_obs['TMEAN'], c='k', alpha=0.4, lw=1.2)

        # difference of observed and climate (grey area)
        fill_r = ax.fill_between(x_dates_short['DATE'].values,
                                 y1=t_above,
                                 y2=y_clim.loc[clim_locs_short].values,
                                 facecolor='#d6604d',
                                 alpha=0.5)
        fill_rr = ax.fill_between(x_dates_short['DATE'].values,
                                  y1=t_above_std,
                                  y2=y_clim_std_hi.loc[clim_locs_short].values,
                                  facecolor='#d6604d',
                                  alpha=0.7)
        fill_b = ax.fill_between(x_dates_short['DATE'].values,
                                 y1=y_clim.loc[clim_locs_short].values,
                                 y2=t_below,
                                 facecolor='#4393c3',
                                 alpha=0.5)
        fill_bb = ax.fill_between(x_dates_short['DATE'].values,
                                  y1=y_clim_std_lo.loc[clim_locs_short].values,
                                  y2=t_below_std,
                                  facecolor='#4393c3',
                                  alpha=0.7)

        # plot extremes
        if plot_extrema:
            tmax = self.dataset.data.groupby('DATE_MD').max()['TMEAN']
            tmin = self.dataset.data.groupby('DATE_MD').min()['TMEAN']
            local_obs = df_obs[['DATE', 'DATE_MD', 'TMEAN']].set_index('DATE_MD', drop=False)
            idx = local_obs.index
            local_max = tmax.loc[idx] == local_obs['TMEAN']
            local_min = tmin.loc[idx] == local_obs['TMEAN']
            # extract x and y values
            x_max = local_obs[local_max]['DATE']
            y_max = local_obs[local_max]['TMEAN']
            x_min = local_obs[local_min]['DATE']
            y_min = local_obs[local_min]['TMEAN']
            xtreme_hi = ax.scatter(x_max.values, y_max.values, c='#d6604d', marker='x')
            xtreme_lo = ax.scatter(x_min.values, y_min.values, c='#4393c3', marker='x')

        xlim = ax.get_xlim()
        ax.hlines(0, *xlim, linestyles='--')
        # grid
        ax.grid()

        # labels
        ax.set_xlim(start_date, end_date)
        if not (plot_tmin == 'auto' and plot_tmin == 'auto'):
            ax.set_ylim(plot_tmin, plot_tmax)
        ax.set_ylabel('Temperature in °C')
        ax.set_xlabel('Date')
        ax.set_title('Observed temperatures {s} to {e} vs. climatological mean (1981-2010)'.format(
            s=start_date.strftime('%Y-%m-%d'),
            e=end_date.strftime('%Y-%m-%d')))

        # add legend
        legend_handle = [fb, cm, cm_hi, fill_r, fill_b]
        legend_text = ['Observed Temperatures',
                       'Climatological Mean',
                       'Std of Climatological Mean',
                       'Above average Temperature',
                       'Below average Temperature']
        if plot_extrema:
            legend_handle.extend([xtreme_hi, xtreme_lo])
            legend_text.extend(['Record High on Date', 'Record Low on Date'])
        ax.legend(legend_handle, legend_text, loc='best', fontsize=legend_fontsize)

        # PRECIPITATION#
        # legend handles
        legend_handle = []
        legend_text = []

        # precipitation
        rain = ax2.bar(x=x_dates_short['DATE'].values,
                       height=df_obs['PRCP'].values,
                       fc='#4393c3',
                       alpha=1)
        legend_handle.append(rain)
        legend_text.append('Precipitation')

        # grid
        ax2.grid()
        # labels
        ax2.set_ylabel('Precipitation in mm')
        ax2.set_xlabel('Date')
        # y-axis scaling
        ax2.set_ylim(bottom=0)
        if isinstance(plot_pmax, (int, float)):
            ax2.set_ylim(top=plot_pmax)

        # snow
        # TODO: make snowcheck
        if (show_snow_accumulation) and ('SNOW' in df_obs.columns):
            ax2_snow = ax2.twinx()
            # plots
            sn_acc = ax2_snow.fill_between(x=x_dates_short.loc[:last_snow_date, 'DATE'].values,
                                           y1=snow_acc.loc[:last_snow_date] / 10,
                                           facecolor='k',
                                           alpha=0.2)
            _ = ax2_snow.plot(x_dates_short.loc[last_snow_date:, 'DATE'].values,
                              snow_acc.loc[last_snow_date:] / 10,
                              c='k',
                              alpha=0.2,
                              ls='--')
            # y-axis label
            ax2_snow.set_ylabel('Cumulative Snowfall in cm')
            # legend
            legend_handle.append(sn_acc)
            legend_text.append('Cumulative Snowfall')
            # y-axis scaling
            ax2_snow.set_ylim(bottom=0)
            if isinstance(plot_snowmax, (int, float)):
                ax2_snow.set_ylim(top=plot_snowmax)

        ax2.legend(legend_handle, legend_text, loc='upper left', fontsize=legend_fontsize)
        ax2.set_title('Precipitation {s} to {e}'.format(s=start_date.strftime('%Y-%m-%d'),
                                                        e=end_date.strftime('%Y-%m-%d')))
        fig.tight_layout()

        # Save Figure
        if save_path:
            fig.savefig(save_path, figsize=figsize, dpi=dpi)
        # Show plot if chosen, destroy figure object at the end
        if show_plot:
            plt.show()
        else:
            plt.close(fig)

    def plot_monthly_barchart(self, start_date, end_date, information='Temperature', show_plot=True,
                              anomaly=False, anomaly_type='absolute', trailing_mean=None,
                              save_path=False, figsize=(9, 4), dpi=100, legend_fontsize='x-small'):

        # legend handles
        legend_handle = []
        legend_text = []

        # TODO: move to external file
        if information == 'Temperature':
            cmap = 'RdBu_r'
            fc_low = '#4393c3'
            fc_high = '#d6604d'
            if anomaly:
                value_column = 'tmean_diff'
                y_label = 'Temperature anomaly [°C]'
                title = 'Monthly anomaly from climatological mean (1981-2010)'
                legend_label_above = 'Above average'
                legend_label_below = 'Below average'
            else:
                value_column = 'tmean_doy_mean'
                y_label = 'Temperature [°C]'
                title = 'Monthly Mean Temperature'
                legend_label_above = 'Above freezing'
                legend_label_below = 'Below freezing'

        elif information == 'Precipitation':
            fc_low = '#d6604d'
            fc_high = '#4393c3'
            if anomaly:
                cmap = 'RdBu'
                value_column = 'prcp_diff'
                y_label = 'Precipitation anomaly [mm]'
                title = 'Monthly anomaly from climatological mean (1981-2010)'
                legend_label_above = 'Above average'
                legend_label_below = 'Below average'
            else:
                cmap = 'Blues'
                value_column = 'prcp_sum'
                y_label = 'Precipitation [mm]'
                title = 'Monthly Precipitation'
                legend_label_below = ''
                legend_label_above = 'Monthly Precipitation'

        data = self.dataset.get_monthly_stats(self.dataset.data.set_index('DATE', drop=False)).reset_index()
        data_clim = self.dataset.get_monthy_climate(self.df_clim_)

        data['DATE'] = data.apply(lambda x: parse_dates_YM(x['DATE_YM']), axis=1)
        data['Month'] = data.apply(lambda x: parse_dates_YM(x['DATE_YM']).month, axis=1)
        data['Year'] = data.apply(lambda x: parse_dates_YM(x['DATE_YM']).year, axis=1)
        data = data.set_index('Month', drop=False).join(data_clim.set_index('Month', drop=False),
                                                        rsuffix='_clim').sort_values(
            'DATE_YM')
        data['tmean_diff'] = data['tmean_doy_mean'] - data['tmean_mean']
        data['prcp_diff'] = data['prcp_sum'] - data['prcp_mean']
        data = data.set_index('DATE', drop=False)

        if trailing_mean:
            data = calc_trailing_mean(data, trailing_mean, value_column, 'trailing_values')

        fig = plt.figure(figsize=figsize, dpi=dpi)
        ax = fig.add_subplot(111)
        data_low = data[data[value_column] < 0]
        data_high = data[data[value_column] >= 0]
        bar_low = ax.bar(x=data_low['DATE'], height=data_low[value_column], width=30, align='edge', color=fc_low)
        # Fix for absolute values
        if len(bar_low) > 1:
            legend_handle.append(bar_low)
            legend_text.append(legend_label_below)
        bar_high = ax.bar(x=data_high['DATE'], height=data_high[value_column], width=30, align='edge', color=fc_high)
        legend_handle.append(bar_high)
        legend_text.append(legend_label_above)
        if trailing_mean:
            line_tr_mean = ax.plot(data['DATE'], data['trailing_values'], c='k')
            legend_handle.append(line_tr_mean[0])
            legend_text.append('Trailing mean: {} months'.format(trailing_mean))
        ax.xaxis.set_major_locator(dates.YearLocator())
        ax.tick_params(axis='x', rotation=90)
        ax.grid(True)

        # x-limit
        ax.set_xlim(start_date, end_date)

        # labels
        ax.set_ylabel(y_label)
        ax.set_xlabel('Date')
        ax.set_title(title)
        # add legend
        ax.legend(legend_handle, legend_text, loc='best', fontsize=legend_fontsize)

        fig.tight_layout()
        # Save Figure
        if save_path:
            fig.savefig(save_path, figsize=figsize, dpi=dpi)
        # Show plot if chosen, destroy figure object at the end
        if show_plot:
            plt.show()
        else:
            plt.close(fig)
