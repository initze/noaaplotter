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
    # the +/- sigma envelope is a single non-hoverable light-grey band (no name)
    grey = [t for t in fig.data if getattr(t, "fillcolor", None)
            and "190,190,190" in str(t.fillcolor)]
    assert grey, "grey climatological band missing"


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


def test_cli_dpi_default_is_print_quality():
    # Regression: the CLI used to default `--dpi` to 100 while the Python
    # API defaulted to 300, so `plot-daily ... -save_plot x.png` produced
    # low-resolution 900x600 images by default. Both must be print
    # quality (300) unless the user asks otherwise.
    from typer.main import get_command
    from noaaplotter.cli import app

    cmd = get_command(app)
    for sub in ("plot-daily", "plot-monthly"):
        params = cmd.commands[sub].params
        dpi = next(p for p in params if p.name == "dpi")
        assert dpi.default == 300, f"{sub} --dpi default should be 300, got {dpi.default}"


def test_engine_default_is_matplotlib():
    n = NOAAPlotter(FIXTURE, location="Kotzebue")
    fig = n.plot_weather_series("2018-01-01", "2018-12-31",
                                show_plot=False, show_snow_accumulation=False,
                                return_plot=True)
    assert hasattr(fig, "savefig")  # matplotlib Figure


def test_snow_accumulation_off_by_default():
    # Regression: the Python API historically defaulted show_snow_accumulation
    # to True, so plots generated without the flag (e.g. ERA5 examples, or any
    # non-winter window) silently drew a snowfall axis. It must be opt-in,
    # matching the CLI's `--snow_acc` (default off).
    import inspect
    from noaaplotter.noaaplotter import NOAAPlotter

    sig = inspect.signature(NOAAPlotter.plot_weather_series)
    assert sig.parameters["show_snow_accumulation"].default is False

    # and the default actually produces no snowfall trace, even for a window
    # that does contain snowfall (Nov 2017 - Mar 2018 at Kotzebue):
    n = NOAAPlotter(FIXTURE, location="Kotzebue")
    fig = n.plot_weather_series(
        start_date="2017-11-01", end_date="2018-03-01",
        engine="plotly", show_plot=False,
    )  # note: no show_snow_accumulation arg -> default
    names = [t.name for t in fig.data]
    assert "Cumulative Snowfall" not in names


def test_daily_no_snow_in_window_does_not_crash(tmp_path):
    # Regression: a window where the SNOW column exists but has zero positive
    # values used to crash on .iloc[-1] of an empty selection (IndexError).
    import numpy as np
    import pandas as pd

    dates = pd.date_range("1981-01-01", "2018-12-31", freq="D")
    rng = np.random.default_rng(42)
    df = pd.DataFrame({
        "STATION": "GHCND:TEST01",
        "NAME": "Synthetic",
        "DATE": dates.strftime("%Y-%m-%d"),
        "TMAX": rng.normal(10, 5, dates.size),
        "TMIN": rng.normal(0, 5, dates.size),
        "TAVG": None,
        "PRCP": rng.poisson(1, dates.size).astype(float),
        "SNOW": None,  # column present, but no snowfall at all
    })
    path = tmp_path / "no_snow.parquet"
    df.to_parquet(path)

    n = NOAAPlotter(str(path), location="Synthetic")
    for engine in ("plotly", "matplotlib"):
        fig = n.plot_weather_series(
            start_date="2016-07-01", end_date="2016-08-31",
            show_snow_accumulation=True, plot_extrema=True,
            show_plot=False, return_plot=True, engine=engine,
        )
        assert fig is not None


def test_download_cli_runs_without_token(tmp_path, monkeypatch):
    # Regression: download-data used to hard-fail with "No NOAA API token
    # found" unless a token was set. The NCEI endpoint is public, so it must
    # run with no token and pass an empty one through.
    import noaaplotter.cli as cli_mod

    captured = {}
    monkeypatch.setattr(cli_mod, "get_noaa_token", lambda t=None: "")
    monkeypatch.setattr(
        cli_mod, "download_from_noaa",
        lambda **kw: (captured.update(kw), 0)[1],
    )
    from typer.testing import CliRunner

    r = CliRunner().invoke(
        cli_mod.app,
        ["download-data", "-o", str(tmp_path / "x.parquet"),
         "-sid", "USW00026616", "-start", "2020-01-01", "-end", "2020-01-02"],
    )
    assert r.exit_code == 0, r.output
    assert "token" not in r.output.lower()
    assert captured.get("noaa_api_token", None) in ("", None)


def test_noaa_source_runs_without_token(tmp_path, monkeypatch):
    # Regression: get_source("noaa") raised ValueError when no token was set.
    import noaaplotter.utils.config as cfg
    import noaaplotter.utils.download_utils as dutils

    captured = {}
    monkeypatch.setattr(cfg, "get_noaa_token", lambda t=None: "")
    monkeypatch.setattr(
        dutils, "download_from_noaa",
        lambda **kw: (captured.update(kw), str(tmp_path / "out.parquet"))[1],
    )
    from noaaplotter.sources import get_source

    get_source("noaa")(
        station_id="USW00026616", start="2020-01-01", end="2020-01-02",
        output_file=str(tmp_path / "out.parquet"),
    )
    assert captured.get("noaa_api_token", None) in ("", None)


def _install_get(d, cap):
    def _get(url, params=None, headers=None, *a, **k):
        class FakeResp:
            text = "[]"  # empty result set; no network, no error
        cap["url"] = url
        cap["headers"] = headers
        return FakeResp()
    return _get


def test_dl_noaa_api_warns_when_token_supplied(monkeypatch):
    import warnings as pyw
    import noaaplotter.utils.download_utils as d

    cap = {}
    monkeypatch.setattr(d.requests, "get", _install_get(d, cap))
    with pyw.catch_warnings(record=True) as w:
        pyw.simplefilter("always")
        d.dl_noaa_api(0, ["TMAX"], "USW00026616", "MY_TOKEN",
                      "2020-01-01", "2020-01-02", 10)
    assert any(issubclass(x.category, DeprecationWarning) for x in w), \
        "a supplied token should raise a DeprecationWarning"


def test_dl_noaa_api_keyless_sends_no_token_header(monkeypatch):
    import warnings as pyw
    import noaaplotter.utils.download_utils as d

    cap = {}
    monkeypatch.setattr(d.requests, "get", _install_get(d, cap))
    with pyw.catch_warnings(record=True) as w:
        pyw.simplefilter("always")
        d.dl_noaa_api(0, ["TMAX"], "USW00026616", "",
                      "2020-01-01", "2020-01-02", 10)
    assert cap["headers"] in (None, {}), \
        f"no token header expected when keyless, got {cap['headers']!r}"
    assert not any(issubclass(x.category, DeprecationWarning) for x in w)


# ----------------------------------------------------------------------
# Warming stripes (Ed Hawkins style)
# ----------------------------------------------------------------------
def test_stripes_matplotlib_returns_figure():
    n = NOAAPlotter(FIXTURE, location="Kotzebue")
    fig = n.plot_warming_stripes(
        "1980-01-01", "2018-12-31", information="Temperature",
        resolution="year", show_plot=False, return_plot=True,
    )
    assert hasattr(fig, "savefig")
    # the figure is a base axes (stripes) plus a colorbar axes
    assert len(fig.axes) >= 2
    # count the individual stripe cells (drawn as Rectangle patches)
    import matplotlib.patches as mpt
    base = fig.axes[0]
    cells = sum(1 for p in base.patches if isinstance(p, mpt.Rectangle))
    assert 20 <= cells <= 45, f"expected ~39 yearly stripes, got {cells}"


def test_stripes_year_vs_month_cell_count():
    n = NOAAPlotter(FIXTURE, location="Kotzebue")
    # 'year' resolution produces one cell per year; 'month' one per month.
    # Count drawn rectangles on the axes (matplotlib bars as Rectangles).
    fy = n.plot_warming_stripes("1980-01-01", "2018-12-31", resolution="year",
                                return_plot=True, show_plot=False)
    fm = n.plot_warming_stripes("1980-01-01", "2018-12-31", resolution="month",
                                return_plot=True, show_plot=False)

    def _cells(f):
        import matplotlib.patches as mpt
        return sum(1 for ax in f.axes for p in ax.patches if isinstance(p, mpt.Rectangle))

    years = _cells(fy)
    months = _cells(fm)
    assert 20 <= years <= 45, f"expected ~39 years, got {years}"
    assert months > years * 3, f"expected ~12x more month cells, got {months}"


def test_stripes_plotly_figure_and_writes_html(tmp_path):
    n = NOAAPlotter(FIXTURE, location="Kotzebue")
    fig = n.plot_warming_stripes(
        "1980-01-01", "2018-12-31", information="Temperature",
        resolution="year", engine="plotly", show_plot=False,
    )
    assert fig is not None
    # a heatmap trace is the core of the stripes
    assert any(t.type == "heatmap" for t in fig.data)
    out = tmp_path / "stripes.html"
    fig.write_html(str(out))
    assert out.exists() and out.stat().st_size > 0


def test_stripes_validation_errors():
    n = NOAAPlotter(FIXTURE, location="Kotzebue")
    import pytest
    with pytest.raises(ValueError):
        n.plot_warming_stripes("1980-01-01", "2018-12-31", information="Wind")
    with pytest.raises(ValueError):
        n.plot_warming_stripes("1980-01-01", "2018-12-31", resolution="week")


# ----------------------------------------------------------------------
# Activity heatmap (months x years)
# ----------------------------------------------------------------------
def test_heatmap_matplotlib_returns_figure():
    n = NOAAPlotter(FIXTURE, location="Kotzebue")
    fig = n.plot_activity_heatmap(
        "1980-01-01", "2018-12-31", information="Temperature",
        show_plot=False, return_plot=True,
    )
    assert hasattr(fig, "savefig")


def test_heatmap_plotly_figure_and_writes_html(tmp_path):
    n = NOAAPlotter(FIXTURE, location="Kotzebue")
    fig = n.plot_activity_heatmap(
        "1980-01-01", "2018-12-31", information="Temperature",
        engine="plotly", show_plot=False,
    )
    assert any(t.type == "heatmap" for t in fig.data)
    out = tmp_path / "heat.html"
    fig.write_html(str(out))
    assert out.exists() and out.stat().st_size > 0


def test_heatmap_precipitation_runs():
    n = NOAAPlotter(FIXTURE, location="Kotzebue")
    fig = n.plot_activity_heatmap(
        "1980-01-01", "2018-12-31", information="Precipitation",
        engine="plotly", show_plot=False,
    )
    assert fig is not None


def test_new_cli_commands_registered_dpi_300():
    from typer.main import get_command
    from noaaplotter.cli import app

    cmd = get_command(app)
    for sub in ("plot-stripes", "plot-heatmap"):
        assert sub in cmd.commands, f"CLI command {sub} not registered"
        params = cmd.commands[sub].params
        # both new plot commands must default to print-quality DPI
        dpi = next(p for p in params if p.name == "dpi")
        assert dpi.default == 300, f"{sub} --dpi default should be 300"
