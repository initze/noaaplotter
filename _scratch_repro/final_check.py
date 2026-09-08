"""Full end-to-end verification: fresh full-range download + daily plot for both stations."""
import os
import sys
import tempfile
import datetime

import pandas as pd
import polars as pl

from dotenv import load_dotenv
load_dotenv(r'C:\Users\initze\projects\noaaplotter\.env')
TOKEN = os.environ['NOAA_API_TOKEN']

sys.path.insert(0, r'C:\Users\initze\projects\noaaplotter')
import matplotlib
matplotlib.use('Agg')
from noaaplotter.utils.download_utils import download_from_noaa
from noaaplotter.noaaplotter import NOAAPlotter

ST = r'C:\Users\initze\OneDrive\Documents\python_script\noaaplotter_streamlit\stations.z'
stations_df = pd.read_pickle(ST)
targets = {}
for kw in ['FAIRBANKS', 'KOTZEBUE']:
    m = stations_df[stations_df['Station_name'].str.contains(kw, case=False, na=False)]
    for _, r in m.iterrows():
        targets[kw] = (r['Station_name'], r['Station_ID'])

workdir = os.path.join(tempfile.gettempdir(), 'noaa_final')
os.makedirs(workdir, exist_ok=True)

today = datetime.date.today()
ref_start, ref_end = datetime.datetime(1981, 1, 1), datetime.datetime(2010, 12, 31)
win_start = (today - pd.Timedelta(days=364)).strftime('%Y-%m-%d')
win_end = today.strftime('%Y-%m-%d')
dl_start = '1981-01-01'
dl_end = today.strftime('%Y-%m-%d')

for kw, (name, sid) in targets.items():
    out = os.path.join(workdir, f'NOAA_{sid}.parquet')
    if os.path.exists(out):
        os.remove(out)
    print(f"\n===== {kw} ({sid}) fresh full download =====")
    download_from_noaa(out, dl_start, dl_end, ['TMIN', 'TMAX', 'PRCP', 'SNOW'],
                       name, sid, TOKEN, n_jobs=4)
    df = pl.read_parquet(out)
    idx_cols = [c for c in df.columns if c.startswith('__index')]
    print(f"rows={df.height} ncols={len(df.columns)} idx_cols={idx_cols}")
    print("nulls:", {c: df[c].null_count() for c in df.columns if c not in ('TAVG',)})

    n = NOAAPlotter(out, location=name, climate_filtersize=7,
                    climate_start=ref_start, climate_end=ref_end)
    fig = n.plot_weather_series(start_date=win_start, end_date=win_end,
                                show_snow_accumulation=True, plot_extrema=True,
                                show_plot=False, title=name, return_plot=True,
                                engine='plotly')
    html = os.path.join(workdir, f'daily_{kw}.html')
    fig.write_html(html)

    # also a static render for visual check
    fig2 = n.plot_weather_series(start_date=win_start, end_date=win_end,
                                 show_snow_accumulation=True, plot_extrema=True,
                                 show_plot=False, title=name, return_plot=True,
                                 engine='matplotlib')
    png = os.path.join(workdir, f'daily_{kw}.png')
    fig2.savefig(png, dpi=110, bbox_inches='tight')
    print(f"plot OK -> {png}")
print("\nDONE")
