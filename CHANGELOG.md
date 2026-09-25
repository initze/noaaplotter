# Changelog

All notable changes to `noaaplotter` are documented here.
Newer entries are added here automatically by the release workflow.

## Unreleased

- **Bugfix — CDS/ERA5 source after the 2026 CDS API migration.**
  `noaaplotter download-data --source cds` failed with `404 endpoint not
  found` on the new CDS retrieve API. The CDS source was rewritten to use
  the new request schema (`year`/`month`/`day`/`time` lists, `data_format`),
  to request a small ±0.25° box (a zero-area point is now rejected by the
  backend), and to unpack the new API's ZIP of two netCDF members
  (`data_stream-oper_stepType-{instant,accum}.nc`). Units are normalised
  to the canonical schema (K→°C, m→mm water-equivalent) and the nearest
  grid cell to the requested point is selected. `xarray` and `netCDF4`
  are now declared as dependencies. A new offline regression test
  (`tests/test_cds_source.py`) covers the parse path.
  Cross-validated against the keyless Open-Meteo ERA5 feed for the same
  point and window (Potsdam, 15 Jan – 28 Feb 2022): TAVG within ~0.4 °C
  RMS, PRCP within ~1.6 mm RMS — consistent with inter-grid differences
  for two ERA5 re-griddings.
- **New plot types — warming stripes & activity heatmap.** Two new anomaly
  figures, both available as temperature or precipitation:
  - `plot_warming_stripes` / `plot-stripes` — one horizontal band, a stripe
    per year (`-res year`, default) or per month (`-res month`), coloured by
    its anomaly from the climate (Ed Hawkins' "warming stripes"). The band is
    drawn with no gaps between cells. `-start`/`-end` are optional and default
    to the whole record in the input file. By default the figure is the bare
    band only (no title, axes or colourbar); pass `--annotations` to add
    title, year/month tick labels and a colourbar.
  - `plot_activity_heatmap` / `plot-heatmap` — a GitHub-style matrix, months
    on x, years on y (most recent on top), drawn with **square cells**.
    `-start`/`-end` are optional (default: whole record). `-scale` chooses
    what each cell encodes (`-scale {anomaly,percentile,absolute}`, default
    `anomaly`): the anomaly from the climate mean, the month's percentile
    rank (0–100) across the full record, or the raw monthly value (°C / mm).
    Temperature uses warm-red = hot / cool-blue = cold; precipitation inverts
    this (wet-blue = high, dry-red = low), as requested.
  Both support `--engine plotly` for an interactive HTML version (hover for
  values, zoom, pan) as well as the default static matplotlib PNG.
- **New CLI command `inspect-data`.** `noaaplotter inspect-data -infile
  <file> [-loc <name>]` prints a summary of an input data file: the file
  path, location (if provided, else the NAME column), the observation period
  (earliest and latest dates, span in days), the types of information
  available (which of TAVG/TMAX/TMIN, PRCP, SNOW are present), the row count,
  and the full column list. Useful for a quick sanity check before plotting.
- **NOAA source is now keyless.** The NOAA downloader already used NOAA's
  public **NCEI Access Data Service**
  ([`…/access/services/data/v1`](https://www.ncei.noaa.gov/access/search/documentation/data-service)),
  which needs **no token** — but the code still *required* one and the docs
  told users to register for one. A token (`-t` / `NOAA_API_TOKEN`) is now
  **optional**: if one is set it is forwarded for backward compatibility and a
  `DeprecationWarning` notes it is no longer required; if none is set, nothing
  changes and no error is raised. `download-data`, the Python `get_source("noaa")`
  path, and the legacy `scripts/download_data.py` no longer hard-fail on a
  missing token; README, `docs/getting-started.md`, and `.env.example` updated.
  (Verified live: a token-less request returns full GHCN-D data, HTTP 200.)
- **CLI:** `--dpi` default raised from 100 → 300 for `plot-daily` and
  `plot-monthly`, so the CLI and the Python API agree at print quality
  (a plain `plot-daily ... -save_plot x.png` now yields 2700×1800 px, not
  900×600). Shipped example figures regenerated at the new default.

## 0.6.3

- **Publishing:** added MIT `LICENSE`, real PyPI metadata (license classifier,
  `project.urls`, keywords), clean public API
  (`from noaaplotter import NOAAPlotter`, `noaaplotter.__version__`).
- **Dropped the GEE/geemap/EarthEngine path** (dead code — unreachable from
  any live entry point); `uv.lock` shrank ~1000 lines.
- **Docs:** MkDocs Material site (API + CLI + examples reference), served from
  GitHub Pages at <https://initze.github.io/noaaplotter/>.
- **CI:** all GitHub Actions bumped to Node-24 majors; flake8 gate fixed for
  both repos.

## 0.6.2

- **Interactive daily plot** (Plotly engine): full-series vs. windowed mode
  (`--full-series`), proper y-limits, year bands.
- **Record extrema** computed over the entire observed record (not just the
  plotted window), then cropped to the window.
- **7-day rolling precipitation sum** in the daily plot.
- Typer CLI: `noaaplotter download-data | plot-daily | plot-monthly`
  (`--source noaa|open_meteo|cds`, `-t_range`/`-p_range` multi-value options).

## 0.6.1

- Manual release workflow (bump version + `uv build` + GitHub Release).

## 0.6.0

- Robust handling of data gaps and out-of-range dates in station data.

## 0.5.4 - 2025-01-05

### Changed

* fixed streamlit crash
* added toml for install
* fixed accounted for nan in monthly aggregates

## 0.5.1 - 2023-02-18

### Changed

* created download_utils
* some code restructuring for noaaplotter_streamlit support (https://github.com/initze/noaaplotter_streamlit)

## 0.5.0 - 2023-02-03

### Changed

* fixed NOAA APIv2 bug for losing January February data
* some code fixes and cleanup

## 0.4.1 - 2023-01-16

### Added

* basic support for sst

## 0.4.0 - 2022-11-30

### Added

### Changed

* moved scripts to subdir and automatic package install

## 0.3.0 - 2022-06-30

### Added

* Automated ERA5 download script through Google Earthengine (later removed
  as part of the 0.6.3 cleanup)

### Changed

* code cleanup and minor changes

## 0.2.0 - 2021-09-19

### Added

* Automated NOAA API download script
* No Data visual for daily data plot

### Changed

* moved legend out of plot for daily plots
* some code cleanup
* minor bugfixes

## 0.1.8 - 2020-12-14

### Changed

- fixed truncated rolling mean at the beginning of monthly plots
- fixed crash bug for end dates after data avalability

## 0.1.7 - 2020-12-09

### Changed

- fixed crash of plot_monthly
- simplification of environement.yml
- minor style fixes

<!-- Older versions (pre-0.1) have no changelog entries yet -->
