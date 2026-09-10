# Getting started

Three steps: **install**, **download data**, **plot**.

## 1. Install

From any venv, on the released version (if published) or directly from GitHub:

```bash
# recommended — uv
uv venv
uv pip install "git+https://github.com/initze/noaaplotter.git"

# or the local checkout for development
uv pip install -e .
```

Requires Python 3.11+.

## 2. Download data

### Station data (NOAA GHCN-D)

Get a NOAA CDO token first ([ncdc.noaa.gov/cdo-web/token](https://www.ncdc.noaa.gov/cdo-web/token)) and either
pass it explicitly (`-t`) or export it (`NOAA_API_TOKEN`):

```bash
noaaplotter download-data \
    -o data/kotzebue.parquet \
    -sid USW00026616 \
    -start 1970-01-01 -end 2021-12-31
```

### Coordinate-based (Open-Meteo / ERA5)

No token needed for Open-Meteo:

```bash
noaaplotter download-data \
    -o data/potsdam.parquet \
    --source open_meteo \
    -lat 52.4 -lon 13.05 \
    -start 1980-01-01 -end 2021-12-31
```

CDS/ERA5 uses the same flag surface with `--source cds` and your own credentials
in the environment (see `CDS_API_KEY` / `CDS_API_URL`).

## 3. Plot

### Static (matplotlib)

```bash
noaaplotter plot-daily \
    -infile data/kotzebue.parquet \
    -start 1992-01-01 -end 1992-12-31 \
    -t_range -45 25 -p_range 50 \
    -save_plot figures/kotzebue_1992.png
```

### Interactive (Plotly)

```bash
noaaplotter plot-daily \
    -infile data/kotzebue.parquet \
    -start 1992-01-01 -end 1992-12-31 \
    --engine plotly \
    -save_plot figures/kotzebue_1992.html
```

Open the HTML in any browser to zoom, hover, and pan.

### Monthly bar chart

```bash
noaaplotter plot-monthly \
    -infile data/kotzebue.parquet \
    -start 1980-01-01 -end 2010-12-31 \
    -type Temperature \
    -save_plot figures/kotzebue_monthly.png
```

## Using the Python API

The CLI is a thin wrapper over `NOAAPlotter`. The same figure in code:

```python
from noaaplotter import NOAAPlotter

n = NOAAPlotter(input_filepath="data/kotzebue.parquet", location="Kotzebue")
n.plot_weather_series(
    start_date="1992-01-01",
    end_date="1992-12-31",
    plot_tmax="auto",
    plot_pmax="auto",
    engine="plotly",            # or "matplotlib"
    save_path="figures/kotzebue_1992",
)
```

Full API documentation on the [API reference](api.md) page.

## Troubleshooting

!!! tip
    If you get a 401 from NOAA, check your token isn't expired and that you
    have a station id that exists in the GHCN-D catalogue (try
    [NCDC station list](https://www.ncei.noaa.gov/access/monitor/location-search.html)).

    If plotting a window fails because the record is short or has gaps, widen
    the window or use `--full-series` (Plotly only) to embed the entire record.
