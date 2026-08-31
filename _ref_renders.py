# -*- coding: utf-8 -*-
"""Render the current matplotlib outputs (daily + monthly) as reference PNGs
so the plotly refactor can be proved byte-faithful afterwards."""
import matplotlib
matplotlib.use("Agg")
import warnings; warnings.filterwarnings("ignore")
import os

from noaaplotter.noaaplotter import NOAAPlotter

OUT = os.path.join("tests", "fixtures", "render")
os.makedirs(OUT, exist_ok=True)

np = NOAAPlotter("tests/fixtures/kotzebue.parquet", location="Kotzebue")

f1 = np.plot_weather_series(
    start_date="2009-01-01", end_date="2010-12-31",
    show_plot=False, show_snow_accumulation=False, plot_extrema=True,
    return_plot=True,
)
f1.savefig(os.path.join(OUT, "before_daily.png"), dpi=150)

f2 = np.plot_monthly_barchart(
    start_date="2008-01-01", end_date="2010-12-31",
    information="Temperature", anomaly=True, trailing_mean=12,
    show_plot=False, return_plot=True,
)
f2.savefig(os.path.join(OUT, "before_monthly.png"), dpi=150)

print("REFERENCE RENDERS WRITTEN to", OUT)
print("daily axes:", len(f1.axes), "| monthly axes:", len(f2.axes))
