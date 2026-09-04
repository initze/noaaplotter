#!/usr/bin/python
# -*- coding: utf-8 -*-
# Imports
import argparse

from noaaplotter.utils.config import get_noaa_token
from noaaplotter.utils.download_utils import download_from_noaa


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
        default="data/parquet.csv",
        help="parquet file to save results",
    )

    parser.add_argument(
        "--source",
        dest="source",
        type=str,
        required=False,
        default="noaa",
        choices=["noaa", "open_meteo", "cds"],
        help="data source: noaa (GHCND station), open_meteo (ERA5 by "
        "coordinates, no key) or cds (CDS/ERA5 by coordinates, account required)",
    )

    parser.add_argument(
        "-t", dest="token", type=str, required=False, default="",
        help="NOAA API token (default: NOAA_API_TOKEN from environment or .env file)",
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
        "-lat",
        dest="latitude",
        type=float,
        required=False,
        default=None,
        help="latitude for coordinate-based sources (open_meteo)",
    )

    parser.add_argument(
        "-lon",
        dest="longitude",
        type=float,
        required=False,
        default=None,
        help="longitude for coordinate-based sources (open_meteo)",
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

    parser.add_argument(
        "-n_jobs",
        dest="n_jobs",
        type=int,
        required=False,
        default=1,
        help="number of parallel processes",
    )

    args = parser.parse_args()

    if args.source in ("open_meteo", "cds"):
        # coordinate-based reanalysis sources (identical interface)
        if args.latitude is None or args.longitude is None:
            parser.error(f"{args.source} source requires -lat and -lon")
        from noaaplotter.sources import get_source

        name = args.loc_name or f"{args.latitude:.2f},{args.longitude:.2f}"
        df = get_source(args.source)(
            latitude=args.latitude,
            longitude=args.longitude,
            start=args.start_date,
            end=args.end_date,
            name=name,
        )
        from noaaplotter.sources.open_meteo import save_to_parquet

        save_to_parquet(df, args.output_file)
        print(f"Saved {df.shape[0]} rows ({name}) to {args.output_file}")
        return

    # NOAA path (default)
    token = get_noaa_token(args.token)
    if not token:
        parser.error(
            "No NOAA API token found. Set NOAA_API_TOKEN in your environment or a "
            "local .env file (see .env.example), or pass it with -t."
        )

    download_from_noaa(
        output_file=args.output_file,
        start_date=args.start_date,
        end_date=args.end_date,
        datatypes=args.datatypes,
        noaa_api_token=token,
        loc_name=args.loc_name,
        station_id=args.station_id,
        n_jobs=args.n_jobs,
    )


if __name__ == "__main__":
    main()
