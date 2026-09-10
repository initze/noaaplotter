"""Interactive (plotly) ERA5 / reanalysis figure for a coordinate-based site.

This is the **no-key** path to ERA5 data: the fixture file was captured once
from `noaaplotter download-data --source open_meteo` (Open-Meteo serves ERA5
from their public archive API — no account, no token).

Run:  python examples/example_era5_potsdam.py
Writes figures/era5_potsdam_daily.html and figures/era5_potsdam_monthly.html
(but the daily PNG is also rendered to figures/era5_potsdam_daily.png for
inclusion in the docs).
"""
import os
import warnings

import matplotlib
matplotlib.use("Agg")
import plotly
plotly.io.renderers.default = "notebook"
warnings.filterwarnings("ignore")

from noaaplotter.noaaplotter import NOAAPlotter

# Reanalysis data for Potsdam, Germany (52.40N / 13.05E).
# For coordinate-based (reanalysis) data the `location` argument is the
# **coordinate string** stored in the STATION column, not a human name,
# because reanalysis points have no station ID. So `location="52.40,13.05"`.
#
# The fixture was fetched once via:
#     noaaplotter download-data \
#         --source open_meteo -lat 52.4 -lon 13.05 \
#         -start 1980-01-01 -end 2021-12-31 \
#         -o tests/fixtures/potsdam_ERA5.parquet
np = NOAAPlotter(
    "tests/fixtures/potsdam_ERA5.parquet",
    location="52.40,13.05",  # coordinate-based (reanalysis) — must match the STATION tag
)

out_dir = os.path.join("figures")
os.makedirs(out_dir, exist_ok=True)

f_daily = np.plot_weather_series(
    start_date="2016-01-01", end_date="2018-12-31",
    engine="plotly", show_plot=False,
    save_path=os.path.join(out_dir, "era5_potsdam_daily.html"),
)
print("daily plotly figure (ERA5 Potsdam):", type(f_daily).__name__)

f_monthly = np.plot_monthly_barchart(
    start_date="2016-01-01", end_date="2018-12-31",
    information="Temperature", anomaly=True, trailing_mean=12,
    engine="plotly", show_plot=False,
    save_path=os.path.join(out_dir, "era5_potsdam_monthly.html"),
)
print("monthly plotly figure (ERA5 Potsdam):", type(f_monthly).__name__)

# also render the daily figure to a static PNG for the examples / docs page
f_daily_svg = np.plot_weather_series(
    start_date="2016-01-01", end_date="2018-12-31",
    engine="matplotlib", show_plot=False,
    save_path=os.path.join(out_dir, "era5_potsdam_daily.png"),
)
print("daily matplotlib figure (ERA5 Potsdam):", type(f_daily_svg).__name__)
