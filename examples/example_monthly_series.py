#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Example Script to plot monthly deviation of temperature or precipitation from the climatological mean (1981-2010).
Furthermore, the trailing mean, mean of the last n-months (here 12) is plotted.
using the noaaplotter package
author: Ingmar Nitze
"""

from src.noaaplotter import NOAAPlotter
import logging

def main():
    logging.basicConfig(filename='example.log', filemode='w', level=logging.DEBUG)
    
    LOCATION = 'Kotzebue'
    START = '1990-01-01'
    END = '2019-12-31'
    TRAILING_MEAN = 12
    DPI = 300
    FIGSIZE = (15,7)
    PERIOD = '1990-2019'
   
    n = NOAAPlotter(r'C:/Users/initze/OneDrive/noaaplotter/data/2005576.csv', location='Kotzebue')   

    try:
        n.plot_monthly_barchart(START, END, information='Precipitation', anomaly=False,
                                trailing_mean=TRAILING_MEAN, show_plot=False,
                                dpi=DPI, figsize=FIGSIZE,
                                save_path=r'./figures/{loc}_monthly_series_precipitation_12mthsTrMn_{p}.png'.format(p=PERIOD, loc=LOCATION))

        n.plot_monthly_barchart(START, END, information='Temperature', anomaly=False,
                                trailing_mean=TRAILING_MEAN, show_plot=False,
                                dpi=DPI, figsize=FIGSIZE,
                                 save_path=r'./figures/{loc}_monthly_series_temperature_12mthsTrMn_{p}.png'.format(p=PERIOD, loc=LOCATION))

        n.plot_monthly_barchart(START, END, information='Precipitation', anomaly=True,
                                trailing_mean=TRAILING_MEAN, show_plot=False,
                                dpi=DPI, figsize=FIGSIZE,
                                save_path=r'./figures/{loc}_monthly_series_precipitation_12mthsTrMn_anomaly_{p}.png'.format(p=PERIOD, loc=LOCATION))

        n.plot_monthly_barchart(START, END, information='Temperature', anomaly=True,
                                trailing_mean=TRAILING_MEAN, show_plot=False,
                                dpi=DPI, figsize=FIGSIZE,
                                save_path=r'./figures/{loc}_monthly_series_temperature_12mthsTrMn_anomaly_{p}.png'.format(p=PERIOD, loc=LOCATION))
    except Exception as e:
        print(e)

if __name__ == '__main__':
    main()