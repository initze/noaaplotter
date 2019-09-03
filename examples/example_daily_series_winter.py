#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Example Script to plot daily weather data for the winter season year (July 1 to June 30 of the subsequent year)
using the noaaplotter package
author: Ingmar Nitze
"""

from noaaplotter.noaaplotter import NOAAPlotter
import logging

def main():
    logging.basicConfig(filename='example.log', filemode='w', level=logging.DEBUG)
    n = NOAAPlotter(r'../data/Kotzebue.csv',
                    location='Kotzebue')
    for year in [1984, 2017, 2018]:
        print(year)
        try:
            n.plot_weather_series(start_date='{yr}-07-01'.format(yr=year), end_date='{yr}-06-30'.format(yr=year+1),
                                  show_snow_accumulation=True, plot_extrema=True,
                                  show_plot=False, kwargs_fig={'dpi':100},
                                  save_path=r'../figures/daily_series_winter_Kotzebue_{yr0}-{yr1}.png'.format(yr0=year, yr1=year+1),
                                  plot_tmin=-45, plot_tmax=25, plot_pmax=50, plot_snowmax=300)
        except Exception as e:
            print(e)
            continue

if __name__ == '__main__':
    main()