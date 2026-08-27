# -*- coding: utf-8 -*-
"""
One-off script: capture golden outputs from the CURRENT (pandas)
implementation BEFORE switching to polars. Run once; the resulting
parquet files are committed under tests/fixtures/golden/.

Also builds tests/fixtures/kotzebue.parquet from the legacy
data/Kotzebue.csv (the current loader only reads parquet).
"""
import os
import sys

sys.path.insert(0, ".")
import matplotlib

matplotlib.use("Agg")

import polars as pl
import pandas as pd

from noaaplotter.utils.dataset import (
    NOAAPlotterDailyClimateDataset,
    NOAAPlotterDailySummariesDataset,
    NOAAPlotterMonthlyClimateDataset,
)

FIX = os.path.join("tests", "fixtures")
OUT = os.path.join(FIX, "golden")
os.makedirs(OUT, exist_ok=True)

# build canonical fixture from the legacy CSV (keep the columns the
# package actually uses); pandas handles the quoted-empty CSV dialect
fixture_cols = ["STATION", "NAME", "DATE", "PRCP", "SNOW", "TAVG", "TMAX", "TMIN"]
raw = pd.read_csv("data/Kotzebue.csv", usecols=fixture_cols)
raw["TAVG"] = pd.to_numeric(raw["TAVG"], errors="coerce")
raw["PRCP"] = pd.to_numeric(raw["PRCP"], errors="coerce")
raw["SNOW"] = pd.to_numeric(raw["SNOW"], errors="coerce")
pl.from_pandas(raw).write_parquet(os.path.join(FIX, "kotzebue.parquet"))
print("fixture:", raw.shape)

ds = NOAAPlotterDailySummariesDataset(os.path.join(FIX, "kotzebue.parquet"), location="Kotzebue")

# 1) daily climate normals (the expensive part of NOAAPlotter init)
clim = NOAAPlotterDailyClimateDataset(ds, filtersize=7)
clim.data.to_parquet(os.path.join(OUT, "daily_climate_1981_2010_f7.parquet"))
print("daily_climate:", clim.data.shape)

# 2) monthly statistics
mstat = NOAAPlotterMonthlyClimateDataset(ds, start="1980-01-01", end="2010-12-31")
mstat.calculate_monthly_statistics()
mstat.monthly_aggregate.to_parquet(os.path.join(OUT, "monthly_stats_1980_2010.parquet"))
print("monthly_stats:", mstat.monthly_aggregate.shape)

# 3) monthly climate normals
mclim = NOAAPlotterMonthlyClimateDataset(ds, start="1981-01-01", end="2010-12-31")
mclim.calculate_monthly_climate()
mclim.monthly_climate.to_parquet(os.path.join(OUT, "monthly_climate_1981_2010.parquet"))
print("monthly_climate:", mclim.monthly_climate.shape)

# 4) dataset frame (TMEAN + date columns)
ds.data.to_parquet(os.path.join(OUT, "dataset_kotzebue.parquet"))
print("dataset:", ds.data.shape)

print("DONE")
