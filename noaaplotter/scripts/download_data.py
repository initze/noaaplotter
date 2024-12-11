#!/usr/bin/python
# -*- coding: utf-8 -*-
# Imports
import argparse
import noaaplotter
#from noaaplotter.tools.download_utils import download_from_noaa
download_from_noaa = noaaplotter.tools.download_utils.download_from_noaa

def main():
    """
    Main Function
    :return:
    """
    ##### Parse arguments #####
    parser = argparse.ArgumentParser(description="Parse arguments.")

    parser.add_argument(
        "-o",
        dest="output_file",
        type=str,
        required=True,
        default="data/data.csv",
        help="csv file to save results",
    )

    parser.add_argument(
        "-t", dest="token", type=str, required=False, default="", help="NOAA API token"
    )

    parser.add_argument(
        "-sid",
        dest="station_id",
        type=str,
        required=False,
        default="",
        help='NOAA Station ID, e.g. "GHCND:USW00026616" for Kotzebue, only if loading through NOAA API',
    )

    parser.add_argument(
        "-loc",
        dest="loc_name",
        type=str,
        required=False,
        default="",
        help="Location name",
    )

    parser.add_argument(
        "-dt",
        dest="datatypes",
        type=list,
        required=False,
        default=["TMIN", "TMAX", "PRCP", "SNOW"],
    )

    parser.add_argument(
        "-start",
        dest="start_date",
        type=str,
        required=True,
        help='start date of plot ("yyyy-mm-dd")',
    )

    parser.add_argument(
        "-end",
        dest="end_date",
        type=str,
        required=True,
        help='end date of plot ("yyyy-mm-dd")',
    )

    args = parser.parse_args()

    download_from_noaa(
        args.output_file,
        args.start_date,
        args.end_date,
        args.datatypes,
        args.loc_name,
        args.station_id,
        args.token,
    )


if __name__ == "__main__":
    main()
