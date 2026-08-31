"""Smoke + parity tests for the plotly figure engine (Phase 3)."""
import matplotlib
matplotlib.use("Agg")
import warnings
warnings.filterwarnings("ignore")

from noaaplotter.noaaplotter import NOAAPlotter

FIXTURE = "tests/fixtures/kotzebue.parquet"


def test_daily_plotly_figure():
    n = NOAAPlotter(FIXTURE, location="Kotzebue")
    fig = n.plot_weather_series(
        start_date="2009-01-01", end_date="2010-12-31",
        engine="plotly", show_plot=False,
        show_snow_accumulation=False, plot_extrema=True,
    )
    assert fig is not None
    names = [t.name for t in fig.data]
    for expected in ("Observed Temperatures", "Climatological Mean",
                     "Precipitation", "Above average Temperature",
                     "Below average Temperature"):
        assert expected in names, f"missing trace: {expected}"


def test_monthly_plotly_parity_vs_matplotlib():
    n = NOAAPlotter(FIXTURE, location="Kotzebue")
    kwargs = dict(start_date="2016-01-01", end_date="2018-12-31",
                  information="Temperature", anomaly=True, trailing_mean=12)
    mpl_fig = n.plot_monthly_barchart(show_plot=False, return_plot=True, **kwargs)
    mpl_vals = sorted(p.get_height() for ax in mpl_fig.axes for p in ax.patches)

    pl_fig = n.plot_monthly_barchart(engine="plotly", **kwargs)
    pl_vals = sorted(v for t in pl_fig.data if t.type == "bar"
                     for v in t.y if v is not None)
    assert len(mpl_vals) == len(pl_vals)
    assert abs(sum(mpl_vals) - sum(pl_vals)) < 1e-6
    assert abs(max(mpl_vals) - max(pl_vals)) < 1e-6


def test_monthly_plotly_precipitation():
    n = NOAAPlotter(FIXTURE, location="Kotzebue")
    fig = n.plot_monthly_barchart("2016-01-01", "2018-12-31",
                                  information="Precipitation", anomaly=True,
                                  engine="plotly")
    assert any(t.type == "bar" for t in fig.data)


def test_engine_default_is_matplotlib():
    n = NOAAPlotter(FIXTURE, location="Kotzebue")
    fig = n.plot_weather_series("2018-01-01", "2018-12-31",
                                show_plot=False, show_snow_accumulation=False,
                                return_plot=True)
    assert hasattr(fig, "savefig")  # matplotlib Figure
