#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Example Script to plot monthly deviation of temperature or precipitation from the climatological mean (1981-2010).
Furthermore, the trailing mean, mean of the last n-months (here 12) is plotted.
using the noaaplotter package
author: Ingmar Nitze
"""

from noaaplotter.noaaplotter import NOAAPlotter
import logging

def main():
    logging.basicConfig(filename='example.log', filemode='w', level=logging.DEBUG)
    n = NOAAPlotter(r'../data/Kotzebue.csv',
                    location='Kotzebue')
    try:
        n.plot_monthly_barchart('1960-01-01', '2019-12-31', information='Precipitation', anomaly=True,
                                trailing_mean=12, show_plot=True,
                                kwargs_fig={'dpi': 100},
                                save_path=r'../figures/monthly_series_precipitation_12mthsTrMn_Kotzebue.png')

        n.plot_monthly_barchart('1960-01-01', '2019-12-31', information='Temperature', anomaly=True,
                                trailing_mean=12, show_plot=True,
                                kwargs_fig={'dpi': 100},
                                save_path=r'../figures/monthly_series_temperature_12mthsTrMn_Kotzebue.png')
    except Exception as e:
        print(e)

if __name__ == '__main__':
    main()