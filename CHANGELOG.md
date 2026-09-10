# Changelog

All notable changes to `noaaplotter` are documented here.
Newer entries are added here automatically by the release workflow.

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
