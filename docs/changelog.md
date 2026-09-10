# Changelog

> Full history lives in the repository's
> [`CHANGELOG.md`](https://github.com/initze/noaaplotter/blob/master/CHANGELOG.md)
> — the single source of truth (the release workflow appends there). This page
> mirrors the two most recent releases.

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
