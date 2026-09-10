---
title: noaaplotter
---

# noaaplotter

**Plot fancy climate & weather data** — NOAA station observations and
coordinate-based reanalysis (Open-Meteo, CDS/ERA5) rendered against a climate
baseline, as **static** PNGs (matplotlib) or **interactive** HTML (Plotly).

What you get:

- **Daily & monthly plots** — observed vs. climate temperature and
  precipitation, with record extrema and a 7-day rolling precipitation sum.
- **Two data flavours** — NOAA GHCN-D station data *or* coordinate-based
  reanalysis; pick what you have.
- **Static or interactive** — the same figure in matplotlib (print-ready PNG)
  or Plotly (zoomable HTML), one `--engine` flag apart.
- **CLI-first** — a small Typer app with three commands: `download-data`,
  `plot-daily`, `plot-monthly`.

!!! success
    **Quick start** &nbsp;·&nbsp;
    [Getting started](getting-started.md) ·
    [CLI reference](cli.md) ·
    [API reference](api.md) ·
    [Examples](examples.md)

## Who it's for

A lightweight, opinionated plotting toolkit for the climate research workflow:
pull a record (or the coordinates you have), compare it against a climate
baseline, and produce a clean figure — no framework, few moving parts.

## Install

```bash
uv venv
uv pip install "git+https://github.com/initze/noaaplotter.git"
```

Python 3.11+. Once installed:

```bash
noaaplotter --help
```

## Repository

- Source: [github.com/initze/noaaplotter](https://github.com/initze/noaaplotter)
- Issues: [github.com/initze/noaaplotter/issues](https://github.com/initze/noaaplotter/issues)
- License: [MIT](license.md)
- Cite-as: [`CITATION.cff`](https://github.com/initze/noaaplotter/blob/master/CITATION.cff) in the repo
