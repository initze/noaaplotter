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


def test_location_name_with_regex_metachars(tmp_path):
    # Regression: -loc used str.contains(literal=False), treating the name as a
    # regex. Real data files carry names with (ERA5), (obs), [sic] etc. — a
    # a name with parentheses/brackets used to fail to match (or match wrongly).
    # location matching must be literal.
    import pandas as pd

    dates = pd.date_range("1981-01-01", "2010-12-31", freq="D")
    df = pd.DataFrame({
        "STATION": "O2A:BRR",
        "NAME": "Barrow AK (ERA5)",   # parentheses = regex parens
        "DATE": dates.strftime("%Y-%m-%d"),
        "TMAX": [10.0] * dates.size,
        "TMIN": [0.0] * dates.size,
        "TAVG": None,
        "PRCP": [1.0] * dates.size,
        "SNOW": None,
    })
    path = tmp_path / "paren_name.parquet"
    df.to_parquet(path)

    # exact name with metacharacters must load & locate cleanly
    n = NOAAPlotter(str(path), location="Barrow AK (ERA5)")
    assert n.dataset is not None
    assert str(n.dataset.data["NAME"].iloc[0]) == "Barrow AK (ERA5)"


def test_wind_row_present_when_wspd_wdir_exist_matplotlib(tmp_path):
    # matplotlib engine (CLI default) must also draw the third wind row when
    # WSPD/WDIR are present — otherwise `plot-daily` by default would show a
    # different number of rows than `plot-daily --engine plotly` on the same
    # data file.
    import numpy as np
    import pandas as pd

    dates = pd.date_range("1981-01-01", "2018-12-31", freq="D")
    rng = np.random.default_rng(7)
    df = pd.DataFrame({
        "STATION": "GHCND:TEST04",
        "NAME": "Synthetic",
        "DATE": dates.strftime("%Y-%m-%d"),
        "TMAX": rng.normal(10, 5, dates.size),
        "TMIN": rng.normal(0, 5, dates.size),
        "TAVG": None,
        "PRCP": rng.poisson(1, dates.size).astype(float),
        "SNOW": None,
        "WSPD": rng.exponential(4, dates.size) + 0.5,
        "WDIR": rng.uniform(0, 360, dates.size).round().astype(int),
    })
    path = tmp_path / "wind_mpl.parquet"
    df.to_parquet(path)

    n = NOAAPlotter(str(path), location="Synthetic")
    fig = n.plot_weather_series(
        start_date="2016-07-01", end_date="2016-08-31",
        engine="matplotlib", show_plot=False, plot_extrema=False,
        return_plot=True, show_snow_accumulation=False,
    )
    # 4 axes in the wind layout: temperature, precipitation, wind direction
    # (primary), wind speed (twinned secondary axis). No colorbar axis.
    assert len(fig.axes) == 4, f"expected 4 axes, got {len(fig.axes)}"
    # find the wind direction axis by its "Direction" ylabel
    wind_ax = next(
        ax for ax in fig.axes if ax.get_ylabel() == "Direction"
    )
    ticks = {t.get_text() for t in wind_ax.get_yticklabels()}
    assert {"N", "S", "E", "W"} <= ticks
    # speed twin axis carries the m/s ylabel
    spd_ax = next(ax for ax in fig.axes if ax.get_ylabel() == "Wind speed in m/s")
    assert spd_ax is not wind_ax
    # direction dots: scatter collection with offsets, no line segments and
    # no per-dot colour encoding (single flat colour)
    coll = wind_ax.collections
    assert coll, "direction dots missing"
    assert not wind_ax.get_lines(), "direction must be dots WITHOUT a line"
    # speed line exists on the twin axis
    assert spd_ax.get_lines(), "wind speed line missing"
    # the twin axis must NOT draw its own date labels (shared x: only the
    # bottommost panel shows dates)
    assert all(not t.get_visible() for t in spd_ax.get_xticklabels()), \
        "speed twin must not draw duplicate date labels"
    # headroom: (inverted) ylim spans beyond the compass range so extreme dots
    # clear the axis edge
    lo, hi = wind_ax.get_ylim()
    assert max(lo, hi) > 360 and min(lo, hi) < 0, f"no ylim headroom: {lo}..{hi}"
    # only the bottom (wind) panel carries date tick labels
    ax_t, ax_p = fig.axes[0], fig.axes[1]
    assert all(not t.get_visible() for t in ax_t.get_xticklabels())
    assert all(not t.get_visible() for t in ax_p.get_xticklabels())
    assert any(t.get_visible() and t.get_text() for t in wind_ax.get_xticklabels())


def test_wind_row_present_when_wspd_wdir_exist(tmp_path):
    # WSPD + WDIR in the source -> a third "wind ribbon" row (WIND trace,
    # direction axis with compass ticks, speed colour scale).
    import numpy as np
    import pandas as pd

    dates = pd.date_range("1981-01-01", "2018-12-31", freq="D")
    rng = np.random.default_rng(7)
    df = pd.DataFrame({
        "STATION": "GHCND:TEST02",
        "NAME": "Synthetic",
        "DATE": dates.strftime("%Y-%m-%d"),
        "TMAX": rng.normal(10, 5, dates.size),
        "TMIN": rng.normal(0, 5, dates.size),
        "TAVG": None,
        "PRCP": rng.poisson(1, dates.size).astype(float),
        "SNOW": None,
        "WSPD": rng.exponential(4, dates.size) + 0.5,        # m/s
        "WDIR": rng.uniform(0, 360, dates.size).round().astype(int),  # deg FROM
    })
    path = tmp_path / "with_wind.parquet"
    df.to_parquet(path)

    n = NOAAPlotter(str(path), location="Synthetic")
    fig = n.plot_weather_series(
        start_date="2016-07-01", end_date="2016-08-31",
        engine="plotly", show_plot=False, plot_extrema=True,
    )
    names = [t.name for t in fig.data]
    assert "Wind direction" in names, f"missing wind trace, got {names}"
    assert "Wind speed" in names, f"missing speed trace, got {names}"
    # legend removed entirely; no colorscale anywhere on the wind traces
    assert fig.layout.showlegend is False
    wind = next(t for t in fig.data if t.name == "Wind direction")
    spd = next(t for t in fig.data if t.name == "Wind speed")
    assert getattr(wind.marker, "colorscale", None) in (None, False, "")
    # direction dots: on yaxis3 (row 3 primary) with compass tick text and
    # ylim headroom beyond the compass range; markers-only (no line)
    assert wind.mode == "markers"
    assert getattr(wind, "yaxis", "") == "y3"
    # regression: the speed line MUST pin the wind row's x-axis explicitly
    # (xaxis=x3). Without it plotly anchors the free-positioned y4 to its own
    # default x-axis and the line renders in a phantom axis (blank panel).
    assert getattr(spd, "xaxis", "") == "x3"
    compass_axis = fig.layout.yaxis3
    ticks = list(getattr(compass_axis, "ticktext", []) or [])
    assert "N" in ticks and "S" in ticks and "E" in ticks
    rng = [float(v) for v in (getattr(compass_axis, "range", []) or [])]
    assert rng and max(rng) > 360 and min(rng) < 0, f"no wind ylim headroom: {rng}"
    # speed line overlays on its own axis (y4), single colour
    assert spd.mode == "lines"
    assert getattr(spd, "yaxis", "") == "y4"
    assert str(spd.line.color).startswith("rgba(")
    # hover carries degrees AND the 16-point compass name
    assert "customdata" in wind.hovertemplate
    assert all(isinstance(c, (list, tuple)) for c in wind.customdata[:5])
    assert list(wind.customdata[0])[1] in (
        "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
        "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW")


def test_wind_gap_days_render_as_missing(tmp_path):
    # Regression guard for the dots+line design: days without WSPD/WDIR must
    # stay null (no dot / no line segment fabricated for them) — and the flat
    # single-colour markers make the old None-in-color-list failure impossible.
    import numpy as np
    import pandas as pd

    dates = pd.date_range("1981-01-01", "2010-12-31", freq="D")
    rng = np.random.default_rng(11)
    wspd = rng.exponential(4, dates.size) + 0.5
    wdir = rng.uniform(0, 360, dates.size).round()
    mask = (dates >= pd.Timestamp("2009-03-01")) & (dates < pd.Timestamp("2009-03-10"))
    wspd = np.where(mask, np.nan, wspd)  # wind-less stretch INSIDE the window
    wdir = np.where(mask, np.nan, wdir)
    df = pd.DataFrame({
        "STATION": "GHCND:TEST04",
        "NAME": "Synthetic",
        "DATE": dates.strftime("%Y-%m-%d"),
        "TMAX": rng.normal(10, 5, dates.size),
        "TMIN": rng.normal(0, 5, dates.size),
        "TAVG": None,
        "PRCP": rng.poisson(1, dates.size).astype(float),
        "SNOW": None,
        "WSPD": wspd,
        "WDIR": wdir,
    })
    path = tmp_path / "wind_gaps.parquet"
    df.to_parquet(path)

    n = NOAAPlotter(str(path), location="Synthetic")
    fig = n.plot_weather_series(
        start_date="2009-01-01", end_date="2010-12-31",
        engine="plotly", show_plot=False, plot_extrema=True,
    )
    wind = next(t for t in fig.data if t.name == "Wind direction")
    spd = next(t for t in fig.data if t.name == "Wind speed")
    # null days stay NaN (no fabricated values, no interpolation)
    import numpy as _np
    assert _np.isnan(spd.y).sum() >= 9, "speed nulls must stay null"
    assert _np.isnan(wind.y).any(), "direction nulls must stay null"


def test_no_wind_row_when_source_lacks_wind(tmp_path):
    # NOAA-style data with no WSPD/WDIR columns -> figure stays at 2 rows
    # (regression guard: the wind row must not be invented).
    import pandas as pd

    dates = pd.date_range("1981-01-01", "2010-12-31", freq="D")
    df = pd.DataFrame({
        "STATION": "GHCND:TEST03",
        "NAME": "Synthetic",
        "DATE": dates.strftime("%Y-%m-%d"),
        "TMAX": [10.0] * dates.size,
        "TMIN": [0.0] * dates.size,
        "TAVG": None,
        "PRCP": [1.0] * dates.size,
        "SNOW": None,
    })
    path = tmp_path / "no_wind.parquet"
    df.to_parquet(path)

    n = NOAAPlotter(str(path), location="Synthetic")
    fig = n.plot_weather_series(
        start_date="2009-01-01", end_date="2010-12-31",
        engine="plotly", show_plot=False, plot_extrema=True,
    )
    names = [t.name for t in fig.data]
    assert "Wind direction" not in names and "Wind speed" not in names


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
    # default: the bare band only -> exactly one axes, no colorbar axes
    assert len(fig.axes) == 1
    base = fig.axes[0]
    # the band is drawn with a single imshow (1-row x N-col)
    assert len(base.images) == 1
    # one cell per year: shape is (1, N) with N years
    shape = base.images[0].get_array().shape
    assert shape[0] == 1 and shape[1] >= 20, f"expected (1, >=20), got {shape}"


def test_stripes_annotations_adds_colorbar():
    n = NOAAPlotter(FIXTURE, location="Kotzebue")
    bare = n.plot_warming_stripes(
        "1980-01-01", "2018-12-31", resolution="year",
        return_plot=True, show_plot=False,
    )
    ann = n.plot_warming_stripes(
        "1980-01-01", "2018-12-31", resolution="year", annotations=True,
        return_plot=True, show_plot=False,
    )
    # bare band -> a single axes; annotated -> base axes + a colorbar axes
    assert len(bare.axes) == 1
    assert len(ann.axes) >= 2


def test_stripes_year_vs_month_cell_count():
    n = NOAAPlotter(FIXTURE, location="Kotzebue")
    # 'year' resolution -> one cell per year; 'month' -> one per month.
    # The cells are the columns of the single imshow band.
    fy = n.plot_warming_stripes("1980-01-01", "2018-12-31", resolution="year",
                                return_plot=True, show_plot=False)
    fm = n.plot_warming_stripes("1980-01-01", "2018-12-31", resolution="month",
                                return_plot=True, show_plot=False)

    def _cells(f):
        return f.axes[0].images[0].get_array().size

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


# ----------------------------------------------------------------------
# New behaviors (optional dates, --scale switch, inspect-data)
# ----------------------------------------------------------------------
def test_stripes_optional_dates_full_record():
    # no start/end -> the whole record; with a narrow window -> fewer years
    n = NOAAPlotter(FIXTURE, location="Kotzebue")
    full = n.plot_warming_stripes(resolution="year", return_plot=True, show_plot=False)
    windowed = n.plot_warming_stripes(
        start_date="2000-01-01", end_date="2010-12-31", resolution="year",
        return_plot=True, show_plot=False,
    )
    full_cells = full.axes[0].images[0].get_array().size
    win_cells = windowed.axes[0].images[0].get_array().size
    assert full_cells >= 100, f"full record should be many years, got {full_cells}"
    assert 10 <= win_cells <= 12, f"2000-2010 window should be ~11 years, got {win_cells}"


def test_heatmap_scale_switch_changes_value_range():
    # anomaly is centred on 0 (zmin<0<zmax); percentile is bounded 0..100;
    # absolute is the raw values (negative minimum for temperature).
    n = NOAAPlotter(FIXTURE, location="Kotzebue")
    anom = n.plot_activity_heatmap(information="Temperature", scale="anomaly",
                                   engine="plotly")
    pct = n.plot_activity_heatmap(information="Temperature", scale="percentile",
                                  engine="plotly")
    absf = n.plot_activity_heatmap(information="Temperature", scale="absolute",
                                   engine="plotly")
    h = lambda f: [t for t in f.data if t.type == "heatmap"][0]
    assert h(anom).zmin < 0 < h(anom).zmax
    assert abs(h(pct).zmin - 0) < 1e-9 and abs(h(pct).zmax - 100) < 1e-9
    # absolute: real °C range, with a negative minimum
    assert h(absf).zmin < 0


def test_heatmap_precipitation_palette_reversed():
    # precipitation: high=wet=blue, low=dry=red (vice versa vs temperature)
    import noaaplotter.noaaplotter as mod
    # temperature: (low=cold blue, high=warm red)
    low_t, high_t = mod.NOAAPlotter._low_high("temperature")
    low_p, high_p = mod.NOAAPlotter._low_high("precipitation")
    assert (low_t, high_t) != (low_p, high_p), "palettes must differ by information type"
    # the builder must be callable for both with a valid color
    n = NOAAPlotter(FIXTURE, location="Kotzebue")
    for info in ("Temperature", "Precipitation"):
        fig = n.plot_activity_heatmap(information=info, scale="percentile",
                                      engine="plotly")
        assert any(t.type == "heatmap" for t in fig.data)


def test_heatmap_scale_validation_error():
    import pytest
    n = NOAAPlotter(FIXTURE, location="Kotzebue")
    with pytest.raises(ValueError):
        n.plot_activity_heatmap(information="Temperature", scale="bogus")


def test_inspect_data_cli_prints_summary():
    from typer.testing import CliRunner
    from noaaplotter.cli import app

    r = CliRunner().invoke(
        app, ["inspect-data", "-infile", FIXTURE, "-loc", "Kotzebue"]
    )
    assert r.exit_code == 0, r.output
    o = r.output.lower()
    assert "kotzebue" in o          # location
    assert "observation period" in o
    assert "information types" in o
    assert "rows" in o              # row count
    assert "1897" in r.output       # earliest date
    assert "2020" in r.output       # latest date
