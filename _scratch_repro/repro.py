"""Repro: download Fairbanks + Kotzebue, inspect the resulting data shape."""
import os
import sys
import tempfile

import pandas as pd
import polars as pl

# token from the noaaplotter .env
from dotenv import load_dotenv
load_dotenv(r'C:\Users\initze\projects\noaaplotter\.env')
TOKEN = os.environ['NOAA_API_TOKEN']

sys.path.insert(0, r'C:\Users\initze\projects\noaaplotter')
from noaaplotter.utils.download_utils import download_from_noaa

stations = {
    'FAIRBANKS INTL AP': 'USW00026411',
    'KOTZEBUE': 'USC00047462',
}

workdir = os.path.join(tempfile.gettempdir(), 'noaa_repro')
os.makedirs(workdir, exist_ok=True)

# window similar to what the app builds: ref 1981-2010 + daily window
START, END = '1981-01-01', '2026-09-04'

for name, sid in stations.items():
    out = os.path.join(workdir, f'NOAA_{sid}.parquet')
    if os.path.exists(out):
        os.remove(out)
    print(f"\n===== {name} ({sid}) {START}..{END} =====")
    try:
        download_from_noaa(out, START, END, ['TMIN', 'TMAX', 'PRCP', 'SNOW'],
                           name, sid, TOKEN, n_jobs=4)
    except Exception as e:
        print(f"!! download raised: {type(e).__name__}: {e}")
        continue
    df = pl.read_parquet(out)
    print(f"rows={df.height} cols={df.columns}")
    print("dtypes:", {c: str(t) for c, t in df.dtypes.items()})
    # nulls per column
    nulls = {c: df[c].null_count() for c in df.columns}
    print("nulls:", nulls)
    # duplicates on DATE?
    ndup = df.height - df['DATE'].n_unique()
    print(f"duplicate DATE rows: {ndup}")
    # date span
    print(f"date span: {df['DATE'].min()} .. {df['DATE'].max()}")
    # SNOW coverage
    snow_nonnull = df['SNOW'].drop_nulls()
    print(f"SNOW non-null: {snow_nonnull.len()}, "
          f"mean={snow_nonnull.mean() if snow_nonnull.len() else 'NA'}")
    tavg = df['TAVG'].drop_nulls()
    print(f"TAVG non-null: {tavg.len()}")
    # head
    with pl.Config(tbl_rows=5):
        print(df.head())
