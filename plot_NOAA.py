#!/usr/bin/python
# -*- coding: utf-8 -*-
from noaaplotter.noaaplotter import NOAAPlotter

# Plot Kotzebue Winter 2016/2017
n = NOAAPlotter(r'data/weather_station_kotzebue.csv')
n.plot_weather_series(start_date='2016-07-01', end_date='2017-06-30',
                      save_path='figures/kotzebue_20162017.png', kwargs_fig={'dpi':100})


# Plot Bismarck Summer 2018
n = NOAAPlotter(r'data/weather_station_bismarck.csv')
n.plot_weather_series(start_date='2018-01-01', end_date='2018-12-31',
                      show_snow_accumulation=False,
                      save_path='figures/bismarck_2018.png', kwargs_fig={'dpi':100})
