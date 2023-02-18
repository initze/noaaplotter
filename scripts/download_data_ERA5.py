#!/usr/bin/python
# -*- coding: utf-8 -*-
# Imports
import argparse
import os
import pandas as pd
import ee
import geemap


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


def download_era5_from_gee(latitude, longitude, end_date, start_date, output_file):
    ee.Initialize()
    EE_LAYER = 'ECMWF/ERA5/DAILY'
    location = ee.Geometry.Point([longitude, latitude])
    # load ImageCollection
    col = ee.ImageCollection(EE_LAYER).filterBounds(location).filterDate(start_date, end_date)
    # Download data
    print("Start downloading daily ERA5 data.")
    print("Download may take a while.\n1yr: ~5 seconds\n10yrs: ~35 seconds\n50yrs: ~8 min")
    result = geemap.extract_pixel_values(col, region=location)
    out_dict = result.getInfo()
    df_gee = pd.DataFrame(data=[out_dict.keys(), out_dict.values()]).T
    # parse dates and values
    df_gee['time'] = df_gee[0].apply(lambda x: f'{x[:4]}-{x[4:6]}-{x[6:8]}')
    df_gee['feature'] = df_gee[0].apply(lambda x: x[9:])
    df_gee['value'] = df_gee[1]
    df = df_gee.pivot_table(values='value', columns=['feature'], index='time')  # .reset_index(drop=False)
    # #### recalculate values
    df_new = pd.DataFrame(index=df.index)
    temperature_cols = ['mean_2m_air_temperature', 'minimum_2m_air_temperature', 'maximum_2m_air_temperature',
                        'dewpoint_2m_temperature']
    precipitation_cols = ['total_precipitation']
    df_joined = df_new.join(df[temperature_cols] - 273.15).join(df[precipitation_cols] * 1e3).reset_index(drop=False)
    # Create Output
    rename_dict = {'time': 'DATE', 'total_precipitation': 'PRCP', 'mean_2m_air_temperature': 'TAVG',
                   'maximum_2m_air_temperature': 'TMAX', 'minimum_2m_air_temperature': 'TMIN'}
    df_renamed = df_joined.rename(columns=rename_dict)
    df_renamed['NAME'] = ''
    df_renamed['STATION'] = ''
    df_renamed['SNWD'] = ''
    output_cols = ["STATION", "NAME", "DATE", "PRCP", "SNWD", "TAVG", "TMAX", "TMIN"]
    df_save = df_renamed[output_cols].astype(str)
    df_save.to_csv(output_file, index=False)


if __name__ == "__main__":
    main()
