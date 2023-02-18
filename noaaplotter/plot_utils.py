#!/usr/bin/python
# -*- coding: utf-8 -*-

########################
# Credits here
# author: Ingmar Nitze, Alfred Wegener Institute for Polar and Marine Research
# contact: ingmar.nitze@awi.de
# version: 2021-09-11

########################

# TODO: move to external file
def setup_monthly_plot_props(information, anomaly):
    plot_kwargs = {}
    if information == 'Temperature':
        plot_kwargs['cmap'] = 'RdBu_r'
        plot_kwargs['fc_low'] = '#4393c3'
        plot_kwargs['fc_high'] = '#d6604d'
        if anomaly:
            plot_kwargs['value_column'] = 'tmean_diff'
            plot_kwargs['y_label'] = 'Temperature departure [°C]'
            plot_kwargs['title'] = 'Monthly departure from climatological mean (1981-2010)'
            plot_kwargs['legend_label_above'] = 'Above average'
            plot_kwargs['legend_label_below'] = 'Below average'
        else:
            plot_kwargs['value_column'] = 'tmean_doy_mean'
            plot_kwargs['y_label'] = 'Temperature [°C]'
            plot_kwargs['title'] = 'Monthly Mean Temperature'
            plot_kwargs['legend_label_above'] = 'Above freezing'
            plot_kwargs['legend_label_below'] = 'Below freezing'

    elif information == 'Precipitation':
        plot_kwargs['fc_low'] = '#d6604d'
        plot_kwargs['fc_high'] = '#4393c3'
        if anomaly:
            plot_kwargs['cmap'] = 'RdBu'
            plot_kwargs['value_column'] = 'prcp_diff'
            plot_kwargs['y_label'] = 'Precipitation departure [mm]'
            plot_kwargs['title'] = 'Monthly departure from climatological mean (1981-2010)'
            plot_kwargs['legend_label_above'] = 'Above average'
            plot_kwargs['legend_label_below'] = 'Below average'
        else:
            plot_kwargs['cmap'] = 'Blues'
            plot_kwargs['value_column'] = 'prcp_sum'
            plot_kwargs['y_label'] = 'Precipitation [mm]'
            plot_kwargs['title'] = 'Monthly Precipitation'
            plot_kwargs['legend_label_below'] = ''
            plot_kwargs['legend_label_above'] = 'Monthly Precipitation'
    return plot_kwargs