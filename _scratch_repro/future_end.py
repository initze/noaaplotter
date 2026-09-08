"""Reproduce the user's exact crash: a DENSE station whose data ends before
the requested (future) end date, plotted with engine='plotly'.

Before the fix this raises:
    ValueError: operands could not be broadcast together with shapes (244,) (365,)
After the fix it should render, with the x-axis running to the selected
(future) end date and the observed series stopping at the last available date.
"""
import os, sys, tempfile, datetime
import numpy as np
import polars as pl

sys.path.insert(0, r'C:\Users\initze\projects\noaaplotter')
from noaaplotter.noaaplotter import NOAAPlotter

# --- build a dense synthetic station (mirrors a real GHCN-D station) ---
tmp = tempfile.mkdtemp(prefix='dense_station_')
first = datetime.date(2000, 1, 1)
last_avail = datetime.date(2024, 6, 30)          # "latest date where data is available"
import pandas as _pd
dates = _pd.date_range(first, last_avail)
n = len(dates)
doy = dates.dayofyear.to_numpy()
season = np.sin(2 * np.pi * (doy - 105) / 365.25)
tavg = 5 + 12 * season + np.random.RandomState(0).normal(0, 1.5, n)
tmax = tavg + 4 + np.random.RandomState(1).normal(0, 1.0, n)
tmin = tavg - 4 + np.random.RandomState(2).normal(0, 1.0, n)
prcp = np.abs(np.random.RandomState(3).normal(0, 2.0, n))
snow = np.clip(-season, 0, 1) * np.abs(np.random.RandomState(4).normal(0, 1.0, n))
df = pl.DataFrame({
    'STATION': ['TEST0001'] * n,
    'NAME': ['DENSE STATION'] * n,
    'DATE': dates.strftime('%Y-%m-%d'),
    'PRCP': np.round(prcp, 1).astype(float),
    'SNOW': np.round(snow, 2).astype(float),
    'TAVG': np.round(tavg, 1).astype(float),
    'TMAX': np.round(tmax, 1).astype(float),
    'TMIN': np.round(tmin, 1).astype(float),
})
path = os.path.join(tmp, 'dense.parquet')
df.write_parquet(path)
print(f"dense station: {n} days, {first} .. {last_avail}  (no gaps)")

ref_s, ref_e = datetime.datetime(1981, 1, 1), datetime.datetime(2010, 12, 31)
n = NOAAPlotter(path, location="DENSE STATION", climate_filtersize=7,
                climate_start=ref_s, climate_end=ref_e)


def run(tag, start_s, end_s):
    fig = n.plot_weather_series(start_date=start_s, end_date=end_s,
        show_snow_accumulation=True, plot_extrema=True, show_plot=False,
        title=f"DENSE ({tag})", return_plot=True, engine='plotly')
    obs = next(t for t in fig.data if t.name == 'Observed Temperatures')
    clim = next(t for t in fig.data if t.name == 'Climatological Mean')
    obs_x = [x for x, y in zip(obs.x, obs.y) if y is not None]
    # x-axis extent is driven by the furthest trace (the full-window climatology line)
    axis_end = max(clim.x[-1], obs_x[-1])
    print(f"\n[{tag}] window {start_s} .. {end_s}")
    print(f"  observed non-null: {len(obs_x)}  pts, first={obs_x[0].date()}, last={obs_x[-1].date()}")
    print(f"  climatology line : {clim.x[0].date()} .. {clim.x[-1].date()}")
    print(f"  x-axis extent     : .. {axis_end.date()}  (driven by full-window climatology)")
    return fig, obs_x, axis_end


print("=" * 70)
print("CASE 1: FUTURE end date (the user's crash) — window extends past last data")
print("=" * 70)
fig1, obs_x1, axis_end1 = run("future-end", "2023-01-01", "2025-12-31")
# x-axis extent must reach the selected (future) end date
assert axis_end1.strftime('%Y-%m-%d') == "2025-12-31", \
    f"x-axis extent {axis_end1} != 2025-12-31"
# observed must stop at the last available date
assert obs_x1[-1].strftime('%Y-%m-%d') == "2024-06-30", \
    f"observed last {obs_x1[-1]} != 2024-06-30"
print("  -> OK: x-axis to future end; observed stops at last data")

print("\n" + "=" * 70)
print("CASE 2: end date WITHIN data (regression check)")
print("=" * 70)
fig2, obs_x2, axis_end2 = run("in-range", "2023-01-01", "2024-06-30")
assert axis_end2.strftime('%Y-%m-%d') == "2024-06-30", \
    f"x-axis extent {axis_end2} != 2024-06-30"
print("  -> OK: in-range case unchanged")

import shutil
shutil.rmtree(tmp, ignore_errors=True)
print("\nALL FUTURE-END-DATE CHECKS PASS")
