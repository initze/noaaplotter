"""Interactive (plotly) daily + monthly figures.

Run:  python examples/example_plotly.py
Writes figures/daily_plotly.html and figures/monthly_plotly.html.
"""
import os
import warnings

import matplotlib
matplotlib.use("Agg")
import plotly
plotly.io.renderers.default = "notebook"
warnings.filterwarnings("ignore")

from noaaplotter.noaaplotter import NOAAPlotter

np = NOAAPlotter("tests/fixtures/kotzebue.parquet", location="Kotzebue")

out_dir = os.path.join("figures")
os.makedirs(out_dir, exist_ok=True)

f_daily = np.plot_weather_series(
    start_date="2016-01-01", end_date="2018-12-31",
    engine="plotly", show_plot=False,
    show_snow_accumulation=True,
    save_path=os.path.join(out_dir, "daily_plotly.html"),
)
print("daily plotly figure:", type(f_daily).__name__)

f_monthly = np.plot_monthly_barchart(
    start_date="2016-01-01", end_date="2018-12-31",
    information="Temperature", anomaly=True, trailing_mean=12,
    engine="plotly", show_plot=False,
    save_path=os.path.join(out_dir, "monthly_plotly.html"),
)
print("monthly plotly figure:", type(f_monthly).__name__)
