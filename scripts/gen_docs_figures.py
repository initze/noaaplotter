#!/usr/bin/env python3
"""Regenerate EVERY figure used in README.md and the MkDocs site from the
local data/ parquet files (gitignored, but present in the working tree) —
deterministic, offline, one command:

    uv run python scripts/gen_docs_figures.py

Canonical outputs land under figures/ and are mirrored into docs/figures/
(static PNGs) and docs/interactive/ (plotly HTML), matching the paths the
docs reference. After any plotting-code change, run this, `git add` the
updated figures/, and commit.

- data/kotzebue.parquet            -> no wind columns (NOAA), 2-row daily plots
- data/NTaymyr_ERA5_75.6_98.7.parquet -> ERA5 with WSPD/WDIR, 3-row wind daily
- potsdam/ERA5 examples reuse files NOT in data/ (documented only) and are
  intentionally NOT regenerated here.
"""
import shutil
import sys
from pathlib import Path
import warnings

warnings.filterwarnings("ignore")
import matplotlib
matplotlib.use("Agg")
from noaaplotter.noaaplotter import NOAAPlotter

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "figures"
DOCS_FIG = ROOT / "docs" / "figures"
DOCS_INT = ROOT / "docs" / "interactive"
KOTZ = "data/kotzebue.parquet"
TAYM = "data/NTaymyr_ERA5_75.6_98.7.parquet"


def _plot_daily(infile, start, end, out, engine="matplotlib",
                t_range=None, p_range=None, snow_acc=False):
    tmin, tmax = ("auto", "auto") if t_range is None else t_range
    n = NOAAPlotter(str(ROOT / infile))
    n.plot_weather_series(
        start_date=start, end_date=end,
        show_snow_accumulation=snow_acc, plot_extrema=True,
        show_plot=False, plot_tmin=tmin, plot_tmax=tmax,
        plot_pmax=(float(p_range) if p_range is not None else "auto"),
        save_path=str(FIG / out), engine=engine,
    )
    print("  wrote figures/" + out)


def main() -> None:
    FIG.mkdir(exist_ok=True)
    DOCS_FIG.mkdir(parents=True, exist_ok=True)
    DOCS_INT.mkdir(parents=True, exist_ok=True)

    print("daily (no wind — NOAA data):")
    _plot_daily(KOTZ, "1992-01-01", "1992-12-31", "kotzebue_daily_1992.png",
                t_range=(-45, 25), p_range=50)
    _plot_daily(KOTZ, "1992-01-01", "1992-12-31", "kotzebue_daily_1992.html",
                engine="plotly")
    _plot_daily(KOTZ, "2017-07-01", "2018-06-30", "kotzebue_daily_winter.png",
                p_range=50, snow_acc=True)
    _plot_daily(KOTZ, "2017-07-01", "2018-06-30", "kotzebue_daily_winter.html",
                engine="plotly", snow_acc=True)

    print("daily (wind — ERA5 data):")
    _plot_daily(TAYM, "2020-01-01", "2020-12-31", "NTaymyr_ERA5_75.6_98.7_daily.png")
    _plot_daily(TAYM, "2020-01-01", "2020-12-31", "NTaymyr_ERA5_75.6_98.7_daily.html",
                engine="plotly")

    print("monthly / stripes / heatmap:")
    n = NOAAPlotter(str(ROOT / KOTZ))
    n.plot_monthly_barchart(start_date="1980-01-01", end_date="2021-08-31",
                            information="Temperature", trailing_mean=12,
                            show_plot=False, save_path=str(FIG / "kotzebue_monthly_t.png"))
    n.plot_monthly_barchart(start_date="1980-01-01", end_date="2021-08-31",
                            information="Temperature", trailing_mean=12, anomaly=True,
                            show_plot=False, save_path=str(FIG / "kotzebue_monthly_t_anomaly.png"))
    n.plot_monthly_barchart(start_date="1980-01-01", end_date="2021-08-31",
                            information="Precipitation", trailing_mean=12,
                            show_plot=False, save_path=str(FIG / "kotzebue_monthly_p.png"))
    n.plot_warming_stripes(start_date="1980-01-01", end_date="2018-12-31",
                           information="Temperature", show_plot=False,
                           save_path=str(FIG / "kotzebue_stripes.png"))
    n.plot_activity_heatmap("1980-01-01", "2018-12-31", information="Temperature",
                            scale="anomaly", show_plot=False,
                            save_path=str(FIG / "kotzebue_heatmap_anomaly.png"))
    n.plot_activity_heatmap("1980-01-01", "2018-12-31", information="Precipitation",
                            scale="absolute", show_plot=False,
                            save_path=str(FIG / "kotzebue_heatmap_precip.png"))
    print("  wrote monthly/stripes/heatmap PNGs")

    # mirror into docs/
    for png in ["kotzebue_daily_1992.png", "kotzebue_daily_winter.png",
                "kotzebue_monthly_t.png", "kotzebue_monthly_t_anomaly.png",
                "kotzebue_monthly_p.png", "kotzebue_stripes.png",
                "kotzebue_heatmap_anomaly.png", "kotzebue_heatmap_precip.png",
                "NTaymyr_ERA5_75.6_98.7_daily.png"]:
        shutil.copy2(FIG / png, DOCS_FIG / png)
        print("  mirrored docs/figures/" + png)
    for html in ["kotzebue_daily_1992.html", "kotzebue_daily_winter.html",
                 "NTaymyr_ERA5_75.6_98.7_daily.html"]:
        shutil.copy2(FIG / html, DOCS_INT / html)
        print("  mirrored docs/interactive/" + html)
    print("done.")


if __name__ == "__main__":
    sys.exit(main())
