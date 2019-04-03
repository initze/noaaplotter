#!/usr/bin/python
# -*- coding: utf-8 -*-
from noaaplotter.noaaplotter import NOAAPlotter

n = NOAAPlotter(r'data/weather_station_kotzebue.csv')
n.plot_weather_series(start_date='2018-07-01', end_date='2019-06-30')