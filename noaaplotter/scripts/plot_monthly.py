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

    parser.add_argument('-loc', dest='location', required=False,
                        type=str, default=None,
                        help='Location name, must be in data file')

    parser.add_argument('-save_plot', dest='save_path', type=str, required=False,
                        default=None,
                        help='filepath for plot')

    parser.add_argument('-type', dest='type', type=str, required=True,
                        help='Attribute Type: {Temperature, Precipitation}',
                        default='Temperature')

    parser.add_argument('-trail', dest='trailing_mean', type=int, required=False,
                        default=None,
                        help='trailing/rolling mean value in months')

    parser.add_argument('-anomaly', dest='anomaly', required=False,
                        default=False, action='store_true',
                        help='show anomaly from climate')

    parser.add_argument('-dpi', dest='dpi', type=float, required=False,
                        default=100,
                        help='dpi for plot output')

    parser.add_argument('-plot', dest='show_plot', required=False,
                        default=False, action='store_true',
                        help='Location name, must be in data file')

    parser.add_argument('-figsize', dest='figsize', type=float, nargs=2, required=False,
                        default=[9, 4],
                        help='figure size in inches width x height. 9 4 recommended 30 years')

    args = parser.parse_args()

    ##### Run Plotting function #####
    n = NOAAPlotter(args.infile,
                    location=args.location)

    n.plot_monthly_barchart(args.start_date,
                            args.end_date,
                            information=args.type,
                            anomaly=args.anomaly,
                            trailing_mean=args.trailing_mean,
                            show_plot=args.show_plot,
                            dpi=args.dpi,
                            figsize=args.figsize,
                            save_path=args.save_path)

if __name__ == "__main__":
    main()
