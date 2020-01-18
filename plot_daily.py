#!/usr/bin/python
# -*- coding: utf-8 -*-
from noaaplotter.noaaplotter import NOAAPlotter
import argparse

def main():
    """
    Main Function
    :return:
    """
    ##### Parse arguments #####
    parser = argparse.ArgumentParser(description='Parse arguments.')

    parser.add_argument('-infile', dest='infile', type=str, required=True,
                        help='input file with climate data')

    parser.add_argument('-start', dest='start_date', type=str, required=True,
                        help='start date of plot ("yyyy-mm-dd")')

    parser.add_argument('-end', dest='end_date', type=str, required=True,
                        help='end date of plot ("yyyy-mm-dd")')

    parser.add_argument('-season', dest='season_mode', nargs=1, required=False,
                        default='summer', type=str,
                        help='plot_mode {summer, winter}')

    parser.add_argument('-loc', dest='location', required=False,
                        type=str, default=None,
                        help='Location name, must be in data file')

    parser.add_argument('-save_plot', dest='save_path', type=str, required=False,
                        default=None,
                        help='filepath for plot')

    parser.add_argument('-p_range', dest='p_range', type=float, required=False,
                        default=None,
                        help='maximum precipitation value in plot')

    parser.add_argument('-t_range', dest='t_range', type=float, nargs=2, required=False,
                        default=[None, None],
                        help='temperature range in plot')

    parser.add_argument('-dpi', dest='dpi', type=float, required=False,
                        default=100,
                        help='dpi for plot output')

    parser.add_argument('-plot', dest='show_plot', required=False,
                        default=False, action='store_true',
                        help='Location name, must be in data file')

    parser.add_argument('-figsize', dest='figsize', type=float, nargs=2, required=False,
                        default=[15, 10],
                        help='figure size in inches width x height. 15 10 recommended for 1 year, 30 10 for 2 years ...')

    args = parser.parse_args()

    ##### Run Plotting function #####
    n = NOAAPlotter(args.infile,
                    location=args.location)

    n.plot_weather_series(start_date=args.start_date, end_date=args.end_date,
    show_snow_accumulation=False, show_plot=args.show_plot, kwargs_fig={'dpi':args.dpi},
    plot_extrema=True, save_path=args.save_path,
    plot_tmin=args.t_range[0], plot_tmax=args.t_range[1], plot_pmax=args.p_range,
    figsize=args.figsize)

if __name__ == "__main__":
    main()
