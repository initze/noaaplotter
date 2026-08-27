# -*- coding: utf-8 -*-
"""
Parity tests: polars implementations in noaaplotter.utils.dataset must
reproduce the golden outputs captured from the original pandas code.

Goldens live in tests/fixtures/golden/ (see _make_goldens.py for
regeneration from the pandas implementation).
"""
import math
import os

import polars as pl
import pytest

from noaaplotter.utils.dataset import (
    NOAAPlotterDailyClimateDataset,
    NOAAPlotterDailySummariesDataset,
    NOAAPlotterMonthlyClimateDataset,
)

FIX = os.path.join("tests", "fixtures")
GOLDEN = os.path.join(FIX, "golden")
TOL = 1e-6


def _compare_frame(got, want, label):
    """Compare two polars DataFrames: shape, columns, values."""
    assert got.shape == want.shape, (
        f"{label}: shape {got.shape} != golden {want.shape}"
    )
    assert got.columns == want.columns, (
        f"{label}: columns {got.columns} != golden {want.columns}"
    )
    for col in want.columns:
        dtype = want[col].dtype
        a, b = got[col].to_list(), want[col].to_list()
        if dtype not in (pl.Float32, pl.Float64):
            assert got[col].to_list() == want[col].to_list(), (
                f"{label}: column {col!r} differs from golden"
            )
            continue
        for x, y in zip(a, b):
            if x is None or y is None:
                assert (x is None) == (y is None), f"{label}: {col} null mismatch"
                continue
            if math.isnan(x) or math.isnan(y):
                assert math.isnan(x) and math.isnan(y), f"{label}: {col} NaN mismatch"
                continue
            assert abs(x - y) <= TOL, (
                f"{label}: {col} value {x} != golden {y}"
            )


@pytest.fixture(scope="module")
def fixture_path():
    return os.path.join(FIX, "kotzebue.parquet")


@pytest.fixture(scope="module")
def dataset(fixture_path):
    return NOAAPlotterDailySummariesDataset(fixture_path, location="Kotzebue")


def test_dataset_frame_matches_golden(dataset):
    _compare_frame(
        pl.from_pandas(dataset.data),
        pl.read_parquet(os.path.join(GOLDEN, "dataset_kotzebue.parquet")),
        "dataset",
    )


def test_daily_climate_matches_golden(dataset):
    clim = NOAAPlotterDailyClimateDataset(dataset, filtersize=7)
    _compare_frame(
        pl.from_pandas(clim.data.reset_index()),
        pl.read_parquet(os.path.join(GOLDEN, "daily_climate_1981_2010_f7.parquet")),
        "daily_climate",
    )


def test_monthly_stats_match_golden(dataset):
    mstat = NOAAPlotterMonthlyClimateDataset(
        dataset, start="1980-01-01", end="2010-12-31"
    )
    mstat.calculate_monthly_statistics()
    _compare_frame(
        pl.from_pandas(mstat.monthly_aggregate.reset_index()),
        pl.read_parquet(os.path.join(GOLDEN, "monthly_stats_1980_2010.parquet")),
        "monthly_stats",
    )


def test_monthly_climate_matches_golden(dataset):
    mclim = NOAAPlotterMonthlyClimateDataset(
        dataset, start="1981-01-01", end="2010-12-31"
    )
    mclim.calculate_monthly_climate()
    _compare_frame(
        pl.from_pandas(mclim.monthly_climate.reset_index()),
        pl.read_parquet(os.path.join(GOLDEN, "monthly_climate_1981_2010.parquet")),
        "monthly_climate",
    )


def test_invalid_location_raises(fixture_path):
    with pytest.raises(ValueError):
        NOAAPlotterDailySummariesDataset(fixture_path, location="DoesNotExist")
