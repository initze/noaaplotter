# API reference

A small, deliberately-focused library: one main class, a Typer CLI, and a
handful of internal helpers (not a stable API).

## `NOAAPlotter`

The plotting class — load a data file, then render the daily, monthly, or
anomaly "stripes / heatmap" figures. Methods:

- `NOAAPlotter(...)` — constructor
- `plot_weather_series(...)` — the daily plot (static or interactive)
- `plot_monthly_barchart(...)` — the monthly bar chart
- `plot_warming_stripes(...)` — warming stripes (yearly or monthly anomaly,
  bare band by default, `annotations=True` to add title/ticks/colourbar)
- `plot_activity_heatmap(...)` — GitHub-style months × years heatmap, square
  cells; `scale='anomaly' | 'percentile' | 'absolute'`

::: noaaplotter.NOAAPlotter
    options:
      show_source: false
      inherited_members: false

## Package

```python
from noaaplotter import NOAAPlotter   # main class
import noaaplotter                    # package metadata
noaaplotter.__version__               # current version string
```

## CLI

The Typer application (see the [CLI reference](cli.md) for all flags):

::: noaaplotter.cli.app
    options:
      show_source: false
