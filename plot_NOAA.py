#!/usr/bin/python
# -*- coding: utf-8 -*-
from noaaplotter.noaaplotter import NOAAPlotter

# Plot Kotzebue Winter Year 2016/2017
n = NOAAPlotter(r'data/weather_station_kotzebue.csv')
n.plot_weather_series(start_date='2016-07-01', end_date='2017-06-30',
                      show_plot=False,
                      save_path='figures/kotzebue_20162017.png', kwargs_fig={'dpi':100})

# Plot Bismarck 1986
n = NOAAPlotter(r'data/weather_station_bismarck.csv')
n.plot_weather_series(start_date='1986-01-01', end_date='1986-12-31',
                      show_snow_accumulation=False, show_plot=False,
                      save_path='figures/bismarck_1986.png', kwargs_fig={'dpi':100})

# Plot San Francisco 2018
n = NOAAPlotter(r'data/weather_station_sanfrancisco.csv')
n.plot_weather_series(start_date='2018-01-01', end_date='2018-12-31',
                      show_snow_accumulation=False, show_plot=False,
                      save_path='figures/sanfrancisco_2018.png', kwargs_fig={'dpi':100})

# Plot Orlando 2000
n = NOAAPlotter(r'data/weather_station_orlando.csv')
n.plot_weather_series(start_date='2000-01-01', end_date='2000-12-31',
                      show_snow_accumulation=False, show_plot=True,
                      save_path='figures/orlando_2000.png', kwargs_fig={'dpi':100})

# Plot Sterlegova
n = NOAAPlotter(r'data/1696868.csv', location='sterlegova')
n.plot_weather_series(start_date='2018-07-01', end_date='2019-06-30',
                      show_snow_accumulation=False, show_plot=True,
                      kwargs_fig={'dpi':100})

# Show Heatmap Kotzebue
n = NOAAPlotter(r'data/weather_station_kotzebue.csv',
                location='Kotzebue')
n.plot_monthly_heatmap('1958-01-01', '2018-12-31', information='Precipitation', anomaly=False)
n.plot_monthly_heatmap('1958-01-01', '2018-12-31', information='Temperature', anomaly=True)