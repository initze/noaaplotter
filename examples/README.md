# examples

Runnable examples for `noaaplotter`.

Each script reads a committed fixture and writes a plot into `figures/` (gitignored).

| File | What it shows |
|---|---|
| `example_plotly.py` | Daily + monthly interactive figures for a **NOAA GHCN** station (Kotzebue, AK) |
| `era5_potsdam.py` | Daily + monthly (interactive & static) for a **reanalysis** coordinate (Potsdam, DE) — the no-API-key path (`open_meteo` source) |
| `test_all_updates.py` | Full end-to-end run: NOAA download → static & plotly daily/monthly. Supports `-source noaa|open_meteo|cds` |

## Run them

```bash
# install the package in editable mode
uv venv && source .venv/Scripts/activate      # or: .venv/bin/activate
uv pip install -e .

# example 1: NOAA station
python examples/example_plotly.py

# example 2: ERA5 / reanalysis, no API key needed
python examples/era5_potsdam.py

# example 3: end-to-end (uses the fixtures that are already committed)
python examples/test_all_updates.py
```

## Notes

- All fixtures are in `tests/fixtures/` (small parquets).
- The example data in `data/` (local working copies) is *regenerable* via the CLI, but the committed fixtures in `tests/fixtures/` always work offline.
- Reanalysis examples (`--source open_meteo`) do not need an API key; NOAA station data does — set `NOAA_API_TOKEN` in a `.env` file at the repo root (see `.env.example`).
