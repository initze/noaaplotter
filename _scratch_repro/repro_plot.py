"""Repro: replicate the Streamlit app's exact daily-plot calls for Fairbanks & Kotzebue."""
import os
import sys
import tempfile

import pandas as pd
import polars as pl

from dotenv import load_dotenv
load_dotenv(r'C:\Users\initze\projects\noaaplotter\.env')
TOKEN = os.environ['NOAA_API_TOKEN']

sys.path.insert(0, r'C:\Users\initze\projects\noaaplotter')
from noaaplotter.utils.download_utils import download_from_noaa
from noaaplotter.noaaplotter import NOAAPlotter

# station ids from the app's stations.z pickle
ST = r'C:\Users\initze\OneDrive\Documents\python_script\noaaplotter_streamlit\stations.z'
stations_df = pd.read_pickle(ST)
targets = {}
for kw in ['FAIRBANKS', 'KOTZEBUE']:
    m = stations_df[stations_df['Station_name'].str.contains(kw, case=False, na=False)]
    for _, r in m.iterrows():
        targets[kw] = (r['Station_name'], r['Station_ID'])
        print('found:', r['Station_ID'], r['Station_name'])

workdir = os.path.join(tempfile.gettempdir(), 'noaa_repro')
os.makedirs(workdir, exist_ok=True)

# the app's window: ref 1981-2010 + daily window (today-1y .. today)
import datetime
today = datetime.date.today()
ref_start, ref_end = pd.Timestamp(1981, 1, 1), pd.Timestamp(2010, 12, 31)
win_start = pd.Timestamp(today - pd.Timedelta(days=364))
win_end = pd.Timestamp(today)
dl_start = (min(ref_start, win_start)).strftime('%Y-%m-%d')
dl_end = (max(ref_end, win_end)).strftime('%Y-%m-%d')
start_string = win_start.strftime('%Y-%m-%d')
end_string = win_end.strftime('%Y-%m-%d')
print(f'download window: {dl_start}..{dl_end}, plot window: {start_string}..{end_string}')

for kw, (name, sid) in targets.items():
    out = os.path.join(workdir, f'NOAA_{sid}.parquet')
    print(f"\n===== {kw} ({sid}) =====")
    try:
        download_from_noaa(out, dl_start, dl_end, ['TMIN', 'TMAX', 'PRCP', 'SNOW'],
                           name, sid, TOKEN, n_jobs=4)
    except Exception as e:
        print(f'!! download raised: {type(e).__name__}: {e}')
        continue
    df = pl.read_parquet(out)
    print(f'rows={df.height}', {c: str(t) for c, t in df.schema.items()})
    print('nulls:', {c: df[c].null_count() for c in df.columns})
    print(f'date span: {df["DATE"].min()} .. {df["DATE"].max()}')

    # exact app call
    try:
        n = NOAAPlotter(out, location=name, climate_filtersize=7,
                        climate_start=ref_start.to_pydatetime(),
                        climate_end=ref_end.to_pydatetime())
        fig = n.plot_weather_series(start_date=start_string, end_date=end_string,
                                    show_snow_accumulation=True, plot_extrema=True,
                                    show_plot=False, title=name, return_plot=True,
                                    engine='plotly')
        html = os.path.join(workdir, f'daily_{kw}.html')
        fig.write_html(html)
        print(f'plot OK -> {html}')
    except Exception as e:
        import traceback
        print(f'!! plot raised: {type(e).__name__}: {e}')
        traceback.print_exc()
