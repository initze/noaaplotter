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
from noaaplotter.utils.download_utils import dl_noaa_api
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

    #parser.add_argument('-dt', dest='datatypes', type=list, required=False, default=['TMIN', 'TMAX', 'PRCP', 'SNOW'])

    parser.add_argument('-start', dest='start_date', type=str, required=True,
                        help='start date of plot ("yyyy-mm-dd")')

    parser.add_argument('-end', dest='end_date', type=str, required=True,
                        help='end date of plot ("yyyy-mm-dd")')

    args = parser.parse_args()

    # remove file if exists
    if os.path.exists(args.output_file):
        os.remove(args.output_file)
    
    ee.Initialize()

    EE_LAYER = "NOAA/CDR/OISST/V2_1"
    
    location = ee.Geometry.Point([args.lon, args.lat])
    
    # load ImageCollection
    col = ee.ImageCollection(EE_LAYER).filterBounds(location).filterDate(args.start_date, args.end_date).select('sst')
        
    # Download data
    print("Start downloading NOAA CDR OISST v02r01 data.")
    print("Download may take a while.\n1yr: ~5 seconds\n10yrs: ~35 seconds\n50yrs: ~8 min")

    out_dict = geemap.extract_pixel_values(col, location, getInfo=True)
    df_gee = pd.DataFrame(data=[out_dict.keys(), out_dict.values()]).T
    
    # parse dates and values
    df_gee['time'] = df_gee[0].apply(lambda x: f'{x[:4]}-{x[4:6]}-{x[6:8]}')
    df_gee['feature'] = df_gee[0].apply(lambda x: x[9:])
    df_gee['value'] = df_gee[1]
    
    df = df_gee.pivot_table(values='value', columns=['feature'], index='time')#.reset_index(drop=False)
    
    # #### recalculate values 
    df_new = pd.DataFrame(index=df.index)
    
    temperature_cols = ['sst']
    #precipitation_cols = ['total_precipitation']
    df_joined = df_new.join(df[temperature_cols]*0.01)#.join(df[precipitation_cols] *1e3).reset_index(drop=False)
    
    # Create Output
    df_joined.reset_index(drop=False, inplace=True)
    rename_dict = {'time': 'DATE', 'sst': 'TMAX'}
    df_renamed = df_joined.rename(columns=rename_dict)
    df_renamed['NAME'] = ''
    df_renamed['STATION'] = ''
    df_renamed['SNWD'] = ''
    df_renamed['PRCP'] = ''
    df_renamed['TAVG'] = df_renamed['TMAX']
    df_renamed['TMIN'] = df_renamed['TMAX']
    
    output_cols = ["STATION","NAME","DATE","PRCP","SNWD","TAVG","TMAX","TMIN"]
    df_save = df_renamed[output_cols].astype(str)
    
    df_save.to_csv(args.output_file, index=False)


if __name__ == "__main__":
    main()
