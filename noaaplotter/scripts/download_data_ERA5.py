#!/usr/bin/python
# -*- coding: utf-8 -*-
# Imports
import argparse
import os

from src.download_utils import download_era5_from_gee


def main():
    """
    Main Function
    :return:
    """
    ##### Parse arguments #####
    parser = argparse.ArgumentParser(description='Parse arguments.')

    parser.add_argument('-o', dest='output_file', type=str, required=True,
                        default='data/data.csv',
                        help='csv file to save results')

    parser.add_argument('-lat', dest='lat', type=float, required=True,
                        help='Latitude of selected location')
    
    parser.add_argument('-lon', dest='lon', type=float, required=True,
                        help='Longitude of selected location')
    
    parser.add_argument('-loc', dest='loc_name', type=str, required=False,
                        default='',
                        help='Location name')

    parser.add_argument('-dt', dest='datatypes', type=list, required=False, default=['TMIN', 'TMAX', 'PRCP', 'SNOW'])

    parser.add_argument('-start', dest='start_date', type=str, required=True,
                        help='start date of plot ("yyyy-mm-dd")')

    parser.add_argument('-end', dest='end_date', type=str, required=True,
                        help='end date of plot ("yyyy-mm-dd")')

    args = parser.parse_args()

    # remove file if exists
    if os.path.exists(args.output_file):
        os.remove(args.output_file)

    download_era5_from_gee(latitude=args.lat,
                           longitude = args.lon,
                           end_date= args.end_date,
                           start_date = args.start_date,
                           output_file = args.output_file)


if __name__ == "__main__":
    main()