"""Drive the real streamlit_app.py via AppTest to verify the trigger fix.

Runs the app in a TEMP dir (so the user's real caches are untouched) with:
  - stations.z (copied)
  - a pre-seeded open_meteo_70.02_-142.56.parquet spanning 1981..today
    (synthetic, seasonal) so the ERA5 branch takes the cache-HIT path (no
    network) and the daily plot succeeds.

Verifies:
  A) fresh run            -> no pipeline run, no figure
  B) widget changes only  -> no pipeline run
  C) press Start          -> runs exactly once, figure produced
  D) widget change w/o Start -> NOT re-run, same figure, re-run hint shown
  E) press Start again    -> figure regenerated
"""
import os, sys, shutil, tempfile, datetime

STREAMLIT_DIR = r'C:\Users\initze\OneDrive\Documents\python_script\noaaplotter_streamlit'

# --- temp working dir with the files the app needs (relative paths) ---
tmp = tempfile.mkdtemp(prefix='noaa_apptest_')
shutil.copy(os.path.join(STREAMLIT_DIR, 'stations.z'), os.path.join(tmp, 'stations.z'))

# pre-seed a valid Open-Meteo-style parquet spanning the full window
import numpy as np
import polars as pl
today = datetime.date.today()
start = datetime.date(1981, 1, 1)
import pandas as _pd
dates = pl.Series(_pd.date_range(start, today))
n = len(dates)
doy = np.arange(n)  # day-of-year within the window (seasonal signal is what matters)
season = np.sin(2*np.pi*(doy-105)/365.25)   # peaks ~summer
tavg = 5 + 15*season + np.random.RandomState(0).normal(0, 1.5, n)
tmax = tavg + 4 + np.random.RandomState(1).normal(0, 1.0, n)
tmin = tavg - 4 + np.random.RandomState(2).normal(0, 1.0, n)
prcp = np.abs(np.random.RandomState(3).normal(0, 2.0, n))
snow = np.clip(-season, 0, 1)*np.abs(np.random.RandomState(4).normal(0, 1.0, n))
om = pl.DataFrame({
    'STATION': [f'{70.02:.4f},{-142.56:.4f}']*n,
    'NAME': ['Open-Meteo ERA5']*n,
    'DATE': dates,
    'TAVG': np.round(tavg,1).astype(float),
    'TMAX': np.round(tmax,1).astype(float),
    'TMIN': np.round(tmin,1).astype(float),
    'PRCP': np.round(prcp,1).astype(float),
    'SNOW': np.round(snow,2).astype(float),
})
om_path = os.path.join(tmp, 'open_meteo_70.02_-142.56.parquet')
om.write_parquet(om_path)

sys.path.insert(0, os.path.join(STREAMLIT_DIR, 'src'))
os.chdir(tmp)  # app uses relative paths

import noaaplotter_streamlit.utils as U
_orig_load_data = U.load_data
CALLS = {'n': 0}
def _counted(*a, **k):
    CALLS['n'] += 1
    return _orig_load_data(*a, **k)
U.load_data = _counted

from streamlit.testing.v1 import AppTest
at = AppTest.from_file(os.path.join(STREAMLIT_DIR, 'streamlit_app.py'), default_timeout=300)

def sb(label):
    for w in at.selectbox:
        if w.label == label: return w
    raise KeyError(label)
def ti(label):
    for w in at.text_input:
        if w.label == label: return w
    raise KeyError(label)
def btn(label):
    for w in at.button:
        if w.label == label: return w
    raise KeyError(label)
def info_texts():
    return [e.value for e in at.get('info')]

# --- A) fresh run ---
at = at.run()
assert not at.exception, f"fresh run raised: {at.exception}"
assert 'figure' not in at.session_state, "auto-ran on load!"
assert CALLS['n'] == 0, f"load_data called {CALLS['n']}x on fresh run"
print(f"A) fresh run: load_data={CALLS['n']} (0), no figure")

# --- B) configure ERA5 (widget changes must NOT run pipeline) ---
sb('Choose your data source type').select('ERA5 (reanalysis, by coordinates)')
at = at.run()
ti('Please Insert Coordinates: LAT, LON (reanalysis only)').set_value('70.02, -142.56')
at = at.run()
assert not at.exception, f"widget-config raised: {at.exception}"
assert 'figure' not in at.session_state, "auto-ran on widget change!"
assert CALLS['n'] == 0, f"widget change re-ran pipeline ({CALLS['n']})"
print(f"B) widget changes only: load_data={CALLS['n']} (0) - no auto-run")

# --- C) press Start -> one run ---
btn('Start Process').click()
at = at.run()
assert not at.exception, f"Start raised: {at.exception}"
assert 'figure' in at.session_state, "no figure after Start!"
assert CALLS['n'] == 1, f"expected 1 call, got {CALLS['n']}"
fig1 = at.session_state['figure']
n_tr = len(fig1.data)
obs = next(t for t in fig1.data if t.name == 'Observed Temperatures')
n_obs = sum(1 for v in obs.y if v is not None)
print(f"C) Start: load_data={CALLS['n']} (1), figure produced ({n_tr} traces, obs days={n_obs})")
assert n_obs > 300, f"observed series too short ({n_obs})"

# --- D) change widget WITHOUT Start -> must NOT re-run ---
sb('Choose your plot type').select('monthly')
at = at.run()
assert not at.exception, f"post-Start widget change raised: {at.exception}"
assert CALLS['n'] == 1, f"widget change re-ran pipeline ({CALLS['n']})"
assert at.session_state['figure'] is fig1, "figure changed -> re-ran!"
assert any('Start Process' in (v or '') for v in info_texts()), f"no re-run hint: {info_texts()}"
print(f"D) widget change w/o Start: load_data={CALLS['n']} (1), same figure, hint shown")

# --- E) press Start again -> figure regenerated ---
sb('Choose your plot type').select('daily')
at = at.run()
fig_before = at.session_state['figure']
btn('Start Process').click()
at = at.run()
assert not at.exception, f"2nd Start raised: {at.exception}"
fig_after = at.session_state['figure']
assert fig_after is not fig_before, "figure not regenerated on 2nd Start!"
print(f"E) 2nd Start: figure regenerated (load_data={CALLS['n']}, memoized data is fine)")

print("\nALL TRIGGER-LOGIC ASSERTIONS PASS")
shutil.rmtree(tmp, ignore_errors=True)
