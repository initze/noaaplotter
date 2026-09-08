"""
CLI Commands for noaaplotter
"""

import typer
from typing import Optional
import os
from pathlib import Path

# Import the core functionality
from noaaplotter.utils.config import get_noaa_token
from noaaplotter.utils.download_utils import download_from_noaa
from noaaplotter.noaaplotter import NOAAPlotter
from noaaplotter.sources import get_source
from noaaplotter.sources.open_meteo import save_to_parquet

# Create Typer app instance for commands
app = typer.Typer()

@app.command()
def download_data(
    output_file: str = typer.Option(..., "-o", "--output-file", help="Output file path"),
    station_id: Optional[str] = typer.Option(None, "-sid", "--station-id", help="NOAA Station ID"),
    latitude: Optional[float] = typer.Option(None, "-lat", "--latitude", help="Latitude for reanalysis"),
    longitude: Optional[float] = typer.Option(None, "-lon", "--longitude", help="Longitude for reanalysis"),
    start_date: str = typer.Option(..., "-start", "--start-date", help="Start date (YYYY-MM-DD)"),
    end_date: str = typer.Option(..., "-end", "--end-date", help="End date (YYYY-MM-DD)"),
    token: Optional[str] = typer.Option(None, "-t", "--token", help="NOAA API token"),
    source: str = typer.Option("noaa", "--source", help="Data source: noaa, open_meteo, or cds"),
    datatypes: str = typer.Option("TMIN,TMAX,PRCP,SNOW", "--datatypes", help="Comma-separated datatypes"),
    n_jobs: int = typer.Option(1, "--n-jobs", help="Number of parallel processes"),
    loc_name: Optional[str] = typer.Option(None, "-loc", "--location-name", help="Location name"),
):
    """
    Download weather data from various sources.
    
    For NOAA stations: --source noaa --station-id USW00026616
    For reanalysis (ERA5): --source open_meteo --latitude 52 --longitude 12
    """
    try:
        # Handle coordinate-based sources (open_meteo, cds)
        if source in ("open_meteo", "cds"):
            if latitude is None or longitude is None:
                raise typer.BadParameter("Coordinate-based sources require both --latitude and --longitude")
            
            name = loc_name or f"{latitude:.2f},{longitude:.2f}"
            df = get_source(source)(
                latitude=latitude,
                longitude=longitude,
                start=start_date,
                end=end_date,
                name=name,
            )
            save_to_parquet(df, output_file)
            typer.echo(f"Saved {df.shape[0]} rows ({name}) to {output_file}")
            return
        
        # Handle NOAA (default)
        if not station_id:
            raise typer.BadParameter("NOAA data requires --station-id")
        
        token = get_noaa_token(token)
        if not token:
            raise typer.BadParameter(
                "No NOAA API token found. Set NOAA_API_TOKEN in your environment or a "
                "local .env file (see .env.example), or pass it with --token."
            )
        
        # Parse datatypes
        datatypes_list = [dt.strip() for dt in datatypes.split(",") if dt.strip()]
        
        download_from_noaa(
            output_file=output_file,
            start_date=start_date,
            end_date=end_date,
            datatypes=datatypes_list,
            noaa_api_token=token,
            loc_name=loc_name,
            station_id=station_id,
            n_jobs=n_jobs,
        )
        
        typer.echo(f"Downloaded data for {station_id} from {start_date} to {end_date}")
        
    except Exception as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(code=1)

@app.command()
def plot_daily(
    infile: str = typer.Option(..., "-infile", "--input-file", help="Input file with climate data"),
    start_date: str = typer.Option(..., "-start", "--start-date", help="Start date (YYYY-MM-DD)"),
    end_date: str = typer.Option(..., "-end", "--end-date", help="End date (YYYY-MM-DD)"),
    location: Optional[str] = typer.Option(None, "-loc", "--location", help="Location name"),
    save_path: Optional[str] = typer.Option(None, "-save-plot", "--save-plot", help="File path for plot"),
    t_range: Optional[str] = typer.Option(None, "-t-range", "--temperature-range", help="Temperature range (min max)"),
    p_range: Optional[float] = typer.Option(None, "-p-range", "--precipitation-range", help="Maximum precipitation value"),
    s_range: Optional[float] = typer.Option(None, "-s-range", "--snow-range", help="Maximum snow accumulation value"),
    snow_acc: bool = typer.Option(False, "--snow-accumulation", help="Show snow accumulation"),
    filtersize: int = typer.Option(7, "--filtersize", help="Filter size for climate smoothing"),
    dpi: float = typer.Option(100.0, "--dpi", help="DPI for plot output"),
    show_plot: bool = typer.Option(False, "--show-plot", help="Show plot in GUI"),
    figsize: str = typer.Option("9,6", "--figsize", help="Figure size in inches (width,height)"),
    title: Optional[str] = typer.Option(None, "-title", "--title", help="Plot title"),
    engine: str = typer.Option("matplotlib", "--engine", help="Rendering engine: matplotlib or plotly"),
):
    """
    Create daily weather plots.
    
    Example: noaaplotter plot-daily -infile data/kotzebue.parquet -start 2020-01-01 -end 2024-06-30
    """
    try:
        # Parse figsize
        if figsize:
            width, height = map(float, figsize.split(","))
            figsize_tuple = (width, height)
        else:
            figsize_tuple = (9, 6)
        
        # Parse temperature range
        t_min, t_max = None, None
        if t_range:
            t_min, t_max = map(float, t_range.split(" "))
        
        # Create NOAAPlotter instance
        n = NOAAPlotter(infile, location=location, climate_filtersize=filtersize)
        
        # Create plot
        n.plot_weather_series(
            start_date=start_date,
            end_date=end_date,
            show_snow_accumulation=snow_acc,
            plot_extrema=True,
            show_plot=show_plot,
            save_path=save_path,
            plot_tmin=t_min,
            plot_tmax=t_max,
            plot_pmax=p_range,
            plot_snowmax=s_range,
            dpi=dpi,
            figsize=figsize_tuple,
            title=title,
            engine=engine,
        )
        
        if save_path:
            typer.echo(f"Plot saved to {save_path}")
        elif show_plot:
            typer.echo("Plot displayed in GUI")
        else:
            typer.echo("Plot created (use --show-plot or --save-plot)")
            
    except Exception as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(code=1)

@app.command()
def plot_monthly(
    infile: str = typer.Option(..., "-infile", "--input-file", help="Input file with climate data"),
    start_date: str = typer.Option(..., "-start", "--start-date", help="Start date (YYYY-MM-DD)"),
    end_date: str = typer.Option(..., "-end", "--end-date", help="End date (YYYY-MM-DD)"),
    location: Optional[str] = typer.Option(None, "-loc", "--location", help="Location name"),
    save_path: Optional[str] = typer.Option(None, "-save-plot", "--save-plot", help="File path for plot"),
    information: str = typer.Option("Temperature", "--type", help="Attribute type: Temperature or Precipitation"),
    trailing_mean: Optional[int] = typer.Option(None, "--trailing-mean", help="Trailing/rolling mean in months"),
    anomaly: bool = typer.Option(False, "--anomaly", help="Show anomaly from climate"),
    dpi: float = typer.Option(100.0, "--dpi", help="DPI for plot output"),
    show_plot: bool = typer.Option(False, "--show-plot", help="Show plot in GUI"),
    figsize: str = typer.Option("9,4", "--figsize", help="Figure size in inches (width,height)"),
):
    """
    Create monthly weather plots.
    
    Example: noaaplotter plot-monthly -infile data/kotzebue.parquet -start 2020-01-01 -end 2024-06-30
    """
    try:
        # Parse figsize
        if figsize:
            width, height = map(float, figsize.split(","))
            figsize_tuple = (width, height)
        else:
            figsize_tuple = (9, 4)
        
        # Create NOAAPlotter instance
        n = NOAAPlotter(infile, location=location)
        
        # Create plot
        n.plot_monthly_barchart(
            start_date=start_date,
            end_date=end_date,
            information=information,
            anomaly=anomaly,
            trailing_mean=trailing_mean,
            show_plot=show_plot,
            dpi=dpi,
            figsize=figsize_tuple,
            save_path=save_path,
        )
        
        if save_path:
            typer.echo(f"Plot saved to {save_path}")
        elif show_plot:
            typer.echo("Plot displayed in GUI")
        else:
            typer.echo("Plot created (use --show-plot or --save-plot)")
            
    except Exception as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(code=1)