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

No token needed — data comes from the public [NCEI Access Data
Service](https://www.ncei.noaa.gov/access/search/documentation/data-service):

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

### Warming stripes & activity heatmap (anomaly vs climate)

Two at-a-glance views of change over time. Both are temperature by default;
`-type Precipitation` works too (and inverts the palette — see below).

**Warming stripes** — one band, a stripe per year (default) or per month,
coloured by its anomaly from the climate. `-start`/`-end` are optional
(whole record by default). Output is the bare band by default; add
`--annotations` for title, tick labels and a colourbar:

```bash
noaaplotter plot-stripes \
    -infile data/kotzebue.parquet \
    -type Temperature -res year \
    -save_plot figures/kotzebue_stripes.png

noaaplotter plot-stripes \
    -infile data/kotzebue.parquet \
    -start 1980-01-01 -end 2021-12-31 \
    --annotations -save_plot figures/kotzebue_stripes_ann.png
```

**Activity heatmap** — months on x, years on y (most recent on top), square
cells. `-scale` picks what each cell encodes (default `anomaly`): the
anomaly from the climate, the month's percentile rank 0–100 across the full
record, or the raw monthly value:

```bash
noaaplotter plot-heatmap \
    -infile data/kotzebue.parquet \
    -type Temperature -save_plot figures/kotzebue_heatmap.png

noaaplotter plot-heatmap \
    -infile data/kotzebue.parquet \
    -type Precipitation -scale percentile \
    -save_plot figures/kotzebue_pcp_pctl.png
```

**Colour convention.** Temperature: warm-red = hot, cool-blue = cold.
Precipitation inverts this (the "vice versa" you asked for): wet-blue = high,
dry-red = low. This applies to all `-scale` modes.

**Inspect a data file** — a quick sanity check of an input file before
plotting (location, observation period, information types, row count):

```bash
noaaplotter inspect-data -infile data/kotzebue.parquet -loc Kotzebue
```

Both plots also support `--engine plotly` for an interactive HTML version
(hover for values, zoom, pan).

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
    If `download-data` fails for station data, check the station id exists in
    the [NOAA station catalogue](https://www.ncei.noaa.gov/access/monitor/location-search.html)
    and that the dates fall inside its record. No token is required for the
    NOAA source — if one is set anyway it is ignored with a `DeprecationWarning`.

    If plotting a window fails because the record is short or has gaps, widen
    the window or use `--full-series` (Plotly only) to embed the entire record.
