#!/usr/bin/python
# -*- coding: utf-8 -*-
# Imports
import argparse
import csv
from datetime import datetime
import numpy as np
import os
import pandas as pd
import tqdm
from joblib import delayed, Parallel
from noaaplotter.utils import dl_noaa_api


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

    parser.add_argument('-t', dest='token', type=str, required=False,
                        default='',
                        help='NOAA API token')

    parser.add_argument('-sid', dest='station_id', type=str, required=False,
                        default='',
                        help='NOAA Station ID, e.g. "GHCND:USW00026616" for Kotzebue, only if loading through NOAA API')

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

    # Make query string
    dtypes_string = '&'.join([f'datatypeid={dt}' for dt in args.datatypes])

    # convert datestring to dt
    dt_start = datetime.strptime(args.start_date, '%Y-%m-%d')
    dt_end = datetime.strptime(args.end_date, '%Y-%m-%d')
    # calculate number of days
    n_days = (dt_end - dt_start).days
    # calculate number of splits to fit into 1000 lines/rows
    split_size = np.floor(1000 / len(args.datatypes))
    # calculate splits
    split_range = np.arange(0, n_days, split_size)

    # Data Loading
    print('Downloading data through NOAA API')
    datasets_list = Parallel(n_jobs=4)(
        delayed(dl_noaa_api)(i, dtypes_string, args.station_id, args.token, args.start_date, args.end_date, split_size)
        for i in tqdm.tqdm(split_range[:])
    )

    # Merge subsets and create DataFrame
    df = pd.concat(datasets_list)
    #### Pivot table to correct form
    df_pivot = df.pivot(index='date', columns='datatype', values='value')
    #### adapt  factor
    df_pivot.loc[:, :] /= 10

    df_pivot = df_pivot.reset_index(drop=False)
    df_pivot['DATE'] = df_pivot.apply(lambda x: datetime.fromisoformat(x['date']).strftime('%Y-%m-%d'), axis=1)

    dr = pd.DataFrame(pd.date_range(start=args.start_date, end=args.end_date), columns=['DATE'])
    dr['DATE'] = dr['DATE'].astype(str)
    df_merged = pd.concat([df_pivot.set_index('DATE'), dr.set_index('DATE')], join='outer', axis=1,
                          sort=True)
    df_merged['DATE'] = df_merged.index
    df_merged['STATION'] = args.station_id
    df_merged['NAME'] = args.loc_name

    df_merged['TAVG'] = None
    df_merged['SNWD'] = None

    final_cols = ["STATION", "NAME", "DATE", "PRCP", "SNWD", "TAVG", "TMAX", "TMIN"]

    df_final = df_merged[final_cols]
    df_final = df_final.replace({np.nan: None})

    print(f'Saving data to {args.output_file}')
    df_final.to_csv(args.output_file, index=False, quoting=csv.QUOTE_ALL)


if __name__ == "__main__":
    main()
