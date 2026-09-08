"""
CLI Commands for noaaplotter
"""

import typer
from typing import Optional, Tuple

# Import the core functionality
from noaaplotter.utils.config import get_noaa_token
from noaaplotter.utils.download_utils import download_from_noaa
from noaaplotter.noaaplotter import NOAAPlotter
from noaaplotter.sources import get_source
from noaaplotter.sources.open_meteo import save_to_parquet

# Create Typer app instance for commands
app = typer.Typer(no_args_is_help=True)


@app.command("download-data")
def download_data(
    output_file: str = typer.Option(..., "-o", "--output-file", help="Output file path (parquet)"),
    station_id: Optional[str] = typer.Option(None, "-sid", "--station-id", help='NOAA station id, e.g. "USW00026616" (Kotzebue)'),
    latitude: Optional[float] = typer.Option(None, "-lat", "--latitude", help="Latitude for coordinate-based sources (required for open_meteo/cds)"),
    longitude: Optional[float] = typer.Option(None, "-lon", "--longitude", help="Longitude for coordinate-based sources (required for open_meteo/cds)"),
    start_date: str = typer.Option(..., "-start", "--start-date", help="Start date (YYYY-MM-DD)"),
    end_date: str = typer.Option(..., "-end", "--end-date", help="End date (YYYY-MM-DD)"),
    token: Optional[str] = typer.Option(None, "-t", "--token", help="NOAA API token (default: NOAA_API_TOKEN from environment or .env)"),
    source: str = typer.Option("noaa", "--source", help="Data source: noaa, open_meteo, or cds"),
    datatypes: str = typer.Option("TMIN,TMAX,PRCP,SNOW", "--datatypes", help="Comma-separated datatypes (NOAA only)"),
    n_jobs: int = typer.Option(1, "-n_jobs", "--n-jobs", help="Number of parallel processes (NOAA only)"),
    loc_name: Optional[str] = typer.Option(None, "-loc", "--location-name", help="Location name for the output"),
):
    """Download weather data (NOAA station or reanalysis by coordinates).

    NOAA station:        noaaplotter download-data -o data/kotzebue.parquet -sid USW00026616 -start 1970-01-01 -end 2021-12-31
    ERA5 (open_meteo):   noaaplotter download-data -o data/potsdam.parquet --source open_meteo -lat 52.4 -lon 13.05 -start 1980-01-01 -end 2021-12-31
    """
    src = source.lower()

    if src in ("open_meteo", "cds"):
        if latitude is None or longitude is None:
            raise typer.BadParameter(f"--source {src} requires both -lat and -lon")
        name = loc_name or f"{latitude:.2f},{longitude:.2f}"
        df = get_source(src)(
            latitude=latitude,
            longitude=longitude,
            start=start_date,
            end=end_date,
            name=name,
        )
        save_to_parquet(df, output_file)
        typer.echo(f"Saved {df.shape[0]} rows ({name}) to {output_file}")
        return

    # NOAA path (default)
    if not station_id:
        raise typer.BadParameter("NOAA data requires -sid (station id)")

    api_token = get_noaa_token(token)
    if not api_token:
        raise typer.BadParameter(
            "No NOAA API token found. Set NOAA_API_TOKEN in your environment or a "
            "local .env file (see .env.example), or pass it with -t."
        )

    datatypes_list = [dt.strip() for dt in datatypes.split(",") if dt.strip()]

    download_from_noaa(
        output_file=output_file,
        start_date=start_date,
        end_date=end_date,
        datatypes=datatypes_list,
        noaa_api_token=api_token,
        loc_name=loc_name,
        station_id=station_id,
        n_jobs=n_jobs,
    )
    typer.echo(f"Downloaded data for {station_id} ({start_date} .. {end_date}) to {output_file}")


def _report(save_path, show_plot, engine):
    if save_path:
        typer.echo(f"Plot written to {save_path}")
    elif show_plot:
        typer.echo("Plot displayed (in-browser / GUI)")
    else:
        if engine == "plotly":
            typer.echo("Figure created in memory - add -save_plot <x.html> to write it out")
        else:
            typer.echo("Figure created in memory - add -save_plot <x.png> to write it out")


@app.command("plot-daily")
def plot_daily(
    infile: str = typer.Option(..., "-infile", "--input-file", help="Input file (parquet/csv) with climate data"),
    start_date: str = typer.Option(..., "-start", "--start-date", help="Start date of plot (YYYY-MM-DD)"),
    end_date: str = typer.Option(..., "-end", "--end-date", help="End date of plot (YYYY-MM-DD)"),
    location: Optional[str] = typer.Option(None, "-loc", "--location", help="Location name, must be in data file"),
    save_path: Optional[str] = typer.Option(None, "-save_plot", "--save-plot", help="File path for the plot (png, or html with --engine plotly)"),
    t_range: Optional[Tuple[float, float]] = typer.Option(None, "-t_range", "--temperature-range", help="Temperature range (min, max), e.g. -45 25"),
    p_range: Optional[float] = typer.Option(None, "-p_range", "--precipitation-range", help="Maximum precipitation value in the plot"),
    s_range: Optional[float] = typer.Option(None, "-s_range", "--snow-range", help="Maximum snow accumulation value in the plot"),
    snow_acc: bool = typer.Option(False, "--snow_acc", "--snow-accumulation", help="Show snow accumulation (useful for the winter season, e.g. July to June)"),
    filtersize: int = typer.Option(7, "-filtersize", help="Smooth the climate temperature series by n days (default 7)"),
    dpi: float = typer.Option(100.0, "--dpi", help="DPI for plot output"),
    show_plot: bool = typer.Option(False, "--plot", "--show-plot", help="Open the plot in a browser/GUI"),
    figsize: Optional[Tuple[float, float]] = typer.Option(None, "-figsize", help="Figure size in inches, width height (e.g. 15 10 for 2 years)"),
    title: Optional[str] = typer.Option(None, "-title", help="Plot title"),
    engine: str = typer.Option("matplotlib", "--engine", help="Rendering engine: matplotlib (static) or plotly (interactive HTML)"),
):
    """Create a daily temperature/precipitation plot vs. climate.

    Example: noaaplotter plot-daily -infile data/kotzebue.parquet -start 1992-01-01 -end 1992-12-31 -t_range -45 25 -p_range 50 -save_plot figures/kotzebue_1992.png
    """
    tmin, tmax = ("auto", "auto") if t_range is None else t_range
    fsize = figsize if figsize is not None else (9, 6)

    if engine not in ("matplotlib", "plotly"):
        raise typer.BadParameter("engine must be 'matplotlib' or 'plotly'")
    if not infile:
        raise typer.BadParameter("-infile is required")

    n = NOAAPlotter(infile, location=location, climate_filtersize=filtersize)

    n.plot_weather_series(
        start_date=start_date,
        end_date=end_date,
        show_snow_accumulation=snow_acc,
        plot_extrema=True,
        show_plot=show_plot,
        save_path=save_path or False,
        plot_tmin=tmin,
        plot_tmax=tmax,
        plot_pmax=p_range,
        plot_snowmax=s_range,
        dpi=dpi,
        figsize=fsize,
        title=title,
        engine=engine,
    )
    _report(save_path, show_plot, engine)


@app.command("plot-monthly")
def plot_monthly(
    infile: str = typer.Option(..., "-infile", "--input-file", help="Input file (parquet/csv) with climate data"),
    start_date: str = typer.Option(..., "-start", "--start-date", help="Start date of plot (YYYY-MM-DD)"),
    end_date: str = typer.Option(..., "-end", "--end-date", help="End date of plot (YYYY-MM-DD)"),
    location: Optional[str] = typer.Option(None, "-loc", "--location", help="Location name, must be in data file"),
    save_path: Optional[str] = typer.Option(None, "-save_plot", "--save-plot", help="File path for the plot (png, or html with --engine plotly)"),
    information: str = typer.Option("Temperature", "-type", "--information", help="Attribute type: Temperature or Precipitation"),
    trailing_mean: Optional[int] = typer.Option(None, "-trail", "--trailing-mean", help="Trailing/rolling mean in months (e.g. 12)"),
    anomaly: bool = typer.Option(False, "-anomaly", help="Show anomaly from climate baseline"),
    dpi: float = typer.Option(100.0, "--dpi", help="DPI for plot output"),
    show_plot: bool = typer.Option(False, "--plot", "--show-plot", help="Open the plot in a browser/GUI"),
    figsize: Optional[Tuple[float, float]] = typer.Option(None, "-figsize", help="Figure size in inches, width height"),
    engine: str = typer.Option("matplotlib", "--engine", help="Rendering engine: matplotlib (static) or plotly (interactive HTML)"),
):
    """Create a monthly temperature/precipitation bar chart.

    Example: noaaplotter plot-monthly -infile data/kotzebue.parquet -start 1980-01-01 -end 2021-12-31 -type Temperature -trail 12 -anomaly -save_plot figures/kotzebue_t_anomaly.png
    """
    if engine not in ("matplotlib", "plotly"):
        raise typer.BadParameter("engine must be 'matplotlib' or 'plotly'")
    if information not in ("Temperature", "Precipitation"):
        raise typer.BadParameter("-type must be 'Temperature' or 'Precipitation'")
    if not infile:
        raise typer.BadParameter("-infile is required")

    fsize = figsize if figsize is not None else (9, 4)

    n = NOAAPlotter(infile, location=location)

    n.plot_monthly_barchart(
        start_date=start_date,
        end_date=end_date,
        information=information,
        anomaly=anomaly,
        trailing_mean=trailing_mean,
        show_plot=show_plot,
        dpi=dpi,
        figsize=fsize,
        save_path=save_path or False,
        engine=engine,
    )
    _report(save_path, show_plot, engine)
