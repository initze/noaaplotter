# Changelog

> Full history lives in the repository's
> [`CHANGELOG.md`](https://github.com/initze/noaaplotter/blob/master/CHANGELOG.md)
> — the single source of truth (the release workflow folds each release's
> entries there). This page mirrors the two most recent releases.

## 1.1.4 — 2026-11-25

- Dependency updates only (`certifi` 2026.10.18, `pillow` 13.0.0). No
  user-facing changes.

## 1.1.3 — 2026-10-14

- **Redesigned wind row in the daily plot.** One dot per day placed by wind
  direction (dots coloured by speed) plus a wind-speed line on a right-hand
  secondary axis, replacing the colour-ribbon rendering. Plotly hover shows
  the direction in degrees + 16-point compass name (N, NNE, NE, ...) and the
  speed in m/s. Row heights are shared between engines
  (temperature / precipitation / wind ≈ 0.41 / 0.27 / 0.21).
- **Docs:** new "Daily plot with wind (ERA5)" example (North Taymyr 2020,
  static + interactive) and `scripts/gen_docs_figures.py`, which regenerates
  every gallery figure offline from `data/*.parquet` in one command.

