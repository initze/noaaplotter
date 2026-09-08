# noaaplotter
A python package to create fancy plots with NOAA weather data (stations) and ERA5 reanalysis (by coordinates).

## Install

### Recommended: uv
```bash
uv venv
uv pip install -e .          # install this package + all dependencies
# or from GitHub:
uv pip install git+https://github.com/initze/noaaplotter.git
```

### Requirements
matplotlib, numpy, pandas, requests, joblib, tqdm, polars, pyarrow, plotly,
python-dotenv, typer (all listed in `pyproject.toml` and installed automatically).

## Quick start (3 steps)

```bash
# 1. Download data (NOAA station data needs an API token from
#    https://www.ncdc.noaa.gov/cdo-web/token - or put NOAA_API_TOKEN in a local .env)
noaaplotter download-data -o data/kotzebue.parquet -sid USW00026616 -start 1970-01-01 -end 2021-12-31

# 2. Create a daily plot (temperature vs. climate + precipitation, incl. 7-day rolling sum)
noaaplotter plot-daily -infile data/kotzebue.parquet -start 1992-01-01 -end 1992-12-31 -t_range -45 25 -p_range 50 -save_plot figures/kotzebue_1992.png

# 3. ...or an interactive HTML plot
noaaplotter plot-daily -infile data/kotzebue.parquet -start 1992-01-01 -end 1992-12-31 --engine plotly -save_plot figures/kotzebue_1992.html
```

## Command Line Interface (CLI)

Unified command line interface: `noaaplotter <command> [OPTIONS]`.
Every command supports `-h` / `--help` for detailed usage.

### `noaaplotter download-data`
Download weather data to a parquet file.

```bash
# NOAA station (token required; from env, .env, or -t)
noaaplotter download-data -o data/kotzebue.parquet -sid USW00026616 -start 1970-01-01 -end 2021-12-31

# ERA5 reanalysis by coordinates (open_meteo, no token needed)
noaaplotter download-data -o data/potsdam.parquet --source open_meteo -lat 52.4 -lon 13.05 -start 1980-01-01 -end 2021-12-31
```

| Option | Meaning |
|---|---|
| `-o` / `--output-file` | output parquet file (required) |
| `-sid` / `--station-id` | NOAA station id, e.g. `USW00026616` (Kotzebue) |
| `-lat`, `-lon` | coordinates for `--source open_meteo` / `cds` |
| `-start`, `-end` | start / end date, `YYYY-MM-DD` |
| `-t` / `--token` | NOAA API token (defaults to `NOAA_API_TOKEN` env / `.env`) |
| `--source` | `noaa` (default), `open_meteo`, `cds` |
| `--datatypes` | `TMIN,TMAX,PRCP,SNOW` (NOAA only) |
| `-n_jobs` | parallel processes (NOAA only) |
| `-loc` | location name for the output file |

Data files are cached: re-running only fetches the missing dates.

### `noaaplotter plot-daily`
Daily temperature (observed vs. climate mean ± 1σ, with anomaly fills) + precipitation (bars + 7-day rolling sum).

```bash
noaaplotter plot-daily -infile data/kotzebue.parquet -start 1992-01-01 -end 1992-12-31 -t_range -45 25 -p_range 50 -save_plot figures/kotzebue_1992.png
noaaplotter plot-daily -infile data/kotzebue.parquet -start 2017-07-01 -end 2018-06-30 --snow_acc --engine plotly -save_plot figures/kotzebue_winter.html
```

| Option | Meaning |
|---|---|
| `-infile` | input parquet/csv (required) |
| `-start`, `-end` | plot window, `YYYY-MM-DD` (end date may be in the future; the plot just stops at the last available data) |
| `-t_range` | temperature range `min max`, e.g. `-45 25` |
| `-p_range` | max precipitation value (mm) |
| `-s_range` | max snow accumulation (cm) |
| `--snow_acc` | show cumulative snowfall (winter season) |
| `-filtersize` | climate smoothing window in days (default 7) |
| `-figsize` | figure size in inches `width height` |
| `-title` | plot title |
| `-save_plot` | write the plot (`.png` for matplotlib, `.html` for plotly) |
| `--plot` | open in a browser/GUI |
| `--engine` | `matplotlib` (default) or `plotly` |

### `noaaplotter plot-monthly`
Monthly bar chart of temperature or precipitation, with anomaly and trailing mean.

```bash
# Absolute values
noaaplotter plot-monthly -infile data/kotzebue.parquet -start 1980-01-01 -end 2021-08-31 -type Temperature -trail 12 -save_plot figures/kotzebue_t.png

# Anomaly from climate (1981-2010)
noaaplotter plot-monthly -infile data/kotzebue.parquet -start 1980-01-01 -end 2021-08-31 -type Precipitation -trail 12 -anomaly -save_plot figures/kotzebue_p_anomaly.png
```

| Option | Meaning |
|---|---|
| `-infile` | input parquet/csv (required) |
| `-start`, `-end` | plot window, `YYYY-MM-DD` |
| `-type` | `Temperature` (default) or `Precipitation` |
| `-trail` | trailing/rolling mean in months, e.g. `12` |
| `-anomaly` | show anomaly from the climate baseline |
| `-save_plot` | write the plot (`.png` / `.html`) |
| `--engine` | `matplotlib` (default) or `plotly` |

## Examples

### Download data
**Option 1 — NOAA Daily Summaries via CLI** (Kotzebue, 1970-2021)
* NOAA API Token required: https://www.ncdc.noaa.gov/cdo-web/token

`noaaplotter download-data -o data/kotzebue.parquet -sid USW00026616 -start 1970-01-01 -end 2021-12-31`

**Option 2 — NOAA Daily Summaries via browser**
CSV files of "daily summaries" (https://www.ncdc.noaa.gov/cdo-web/search),
values: metric, file type: csv.

**Option 3 — ERA5 via CLI** (Potsdam, 13.05°E / 52.4°N, 1980-2021 — no token)
`noaaplotter download-data -o data/potsdam.parquet --source open_meteo -lat 52.4 -lon 13.05 -start 1980-01-01 -end 2021-12-31`

### Daily Mean Temperature and Precipitation vs. Climate
Entire year 1 January until 31 December (e.g. 1992):

`noaaplotter plot-daily -infile data/kotzebue.parquet -start 1992-01-01 -end 1992-12-31 -t_range -45 25 -p_range 50 -save_plot figures/kotzebue_daily_1992.png`

### Monthly aggregates
Temperature, absolute (12-month trailing mean):

`noaaplotter plot-monthly -infile data/kotzebue.parquet -start 1980-01-01 -end 2021-08-31 -type Temperature -trail 12 -save_plot figures/kotzebue_monthly_t.png`

![Kotzebue monthly temperature](https://user-images.githubusercontent.com/4864803/133925329-540933c1-b30a-4d31-a66f-0ba624223abf.png)

Temperature, anomaly from climate (1981-2010):

`noaaplotter plot-monthly -infile data/kotzebue.parquet -start 1980-01-01 -end 2021-08-31 -type Temperature -trail 12 -anomaly -save_plot figures/kotzebue_monthly_t_anomaly.png`

![Kotzebue monthly temperature anomaly](https://user-images.githubusercontent.com/4864803/133923928-9ca78105-3718-48d9-80c5-efaf0bfa3217.png)

Precipitation, absolute (12-month trailing mean):

`noaaplotter plot-monthly -infile data/kotzebue.parquet -start 1980-01-01 -end 2021-08-31 -type Precipitation -trail 12 -save_plot figures/kotzebue_monthly_p.png`

![Kotzebue monthly precipitation](https://user-images.githubusercontent.com/4864803/133925351-5d7513df-2794-472a-b00d-780538f68ce6.png)

## Advanced Usage

### Get help for any command
```bash
noaaplotter --help
noaaplotter download-data --help
noaaplotter plot-daily --help
noaaplotter plot-monthly --help
```

### Interactive (plotly) plots
Use `--engine plotly` and save to `.html` to get interactive plots
(zoom, hover, range slider). Daily plots also show a 7-day rolling sum of precipitation.

### Python API
The package is a normal Python library as well:
```python
from noaaplotter import NOAAPlotter

n = NOAAPlotter("data/kotzebue.parquet", location="Kotzebue", climate_filtersize=7)
fig = n.plot_weather_series(start_date="1992-01-01", end_date="1992-12-31",
                            show_plot=False, return_plot=True, engine="plotly")
fig.write_html("figures/kotzebue_1992.html")
```
