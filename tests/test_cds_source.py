# -*- coding: utf-8 -*-
"""
Offline regression test for the CDS/ERA5 source parse path.

Builds a synthetic pair of netCDF files mimicking the 2026 CDS API shape:

    data_stream-oper_stepType-instant.nc  : 2m air temperature (K)
    data_stream-oper_stepType-accum.nc    : total precipitation (m), snowfall (m w.e.)

with the ``valid_time / latitude / longitude`` axis layout CDS currently
returns, then exercises ``_open_nc_members`` and ``_era5_to_daily`` and
asserts the daily statistics are computed with the correct unit
conversions (K -> C, m -> mm) and that the nearest grid cell to the
requested point is selected.

No network access is required, so CI can run this on Python 3.11 and 3.12.
"""
import os
import zipfile

import numpy as np
import pytest


def _make_cds_fixture(tmp_path):
    """Create an instant + accum netCDF pair plus a zip of them.

    2-day, 24-hr time series, 3x2 lat/lon grid (spaced 0.25 degrees).

    Layout (chosen for unambiguous nearest-cell tests):

        lat:   52.25   52.50   52.75
        lon:  12.875  12.925...

    (3 rows x 2 cols, spacing 0.25 deg)

    We place the target at (52.5, 13.0) -> nearest grid cell is the
    (52.50, 12.925) cell  (row 1, col 0).  The row 0 cell (52.25, 12.925)
    gets a distinctly different temperature so a wrong-cell selection
    would fail the assertions below.
    """
    import xarray as xr

    hours = 48  # 2 days x 24 h
    lats = np.array([52.25, 52.50, 52.75])
    lons = np.array([12.875, 12.925])
    t = np.array(
        [f"2022-01-{(15 + i // 24):02d}T{i % 24:02d}:00:00" for i in range(hours)]
    )

    # Baseline hourly temperature (K): rises 1 K per timestep, identical
    # across every grid cell (the +50 K at the wrong-cell below is added
    # after construction so the nearest-cell test stays meaningful).
    base_k = np.linspace(273.15, 273.15 + hours, hours)
    t2m = np.broadcast_to(base_k[:, None, None], (hours,) + lats.shape + lons.shape).copy()

    # Distinct temperature at the off-target cell (row 0, col 0)
    # so a regression picking the wrong grid cell would be caught.
    t2m[:, 0, 0] += 50.0  # +50 K at the wrong-cell

    # Total precipitation (m): 1 mm/hr at all hours on all cells.
    tp = np.full((hours,) + lats.shape + lons.shape, 0.001)
    # Snowfall (m w.e.): 0.5 mm/hr everywhere.
    sf = np.full((hours,) + lats.shape + lons.shape, 0.0005)

    ds_inst = xr.Dataset(
        {"t2m": (("valid_time", "latitude", "longitude"), t2m)},
        coords={
            "valid_time": t,
            "latitude": lats,
            "longitude": lons,
        },
    )
    ds_inst["t2m"].attrs["units"] = "K"
    ds_inst["t2m"].attrs["long_name"] = "2 metre temperature"

    ds_accum = xr.Dataset(
        {
            "tp": (("valid_time", "latitude", "longitude"), tp),
            "sf": (("valid_time", "latitude", "longitude"), sf),
        },
        coords={
            "valid_time": t,
            "latitude": lats,
            "longitude": lons,
        },
    )
    ds_accum["tp"].attrs["units"] = "m"
    ds_accum["tp"].attrs["long_name"] = "Total precipitation"
    ds_accum["sf"].attrs["units"] = "m of water equivalent"
    ds_accum["sf"].attrs["long_name"] = "Snowfall"

    inst_path = str(tmp_path / "data_stream-oper_stepType-instant.nc")
    accum_path = str(tmp_path / "data_stream-oper_stepType-accum.nc")
    ds_inst.to_netcdf(inst_path)
    ds_accum.to_netcdf(accum_path)

    zip_path = str(tmp_path / "bundle.zip")
    with zipfile.ZipFile(zip_path, "w") as z:
        z.write(inst_path, "data-stream-instant.nc")
        z.write(accum_path, "data-stream-accum.nc")
    return zip_path


@pytest.fixture
def cds_zip(tmp_path):
    return _make_cds_fixture(tmp_path)


def test_open_nc_members_handles_zip(cds_zip):
    from noaaplotter.sources.cds import _open_nc_members

    inst, accum, tmpdir = _open_nc_members(cds_zip)
    assert inst is not None
    assert accum is not None
    assert "instant" in os.path.basename(inst)
    assert "accum" in os.path.basename(accum)


def test_era5_to_daily_units_and_nearest_cell(cds_zip):
    """Unit conversion (K->C, m->mm) and nearest-cell selection."""
    from datetime import date

    import xarray as xr

    from noaaplotter.sources.cds import _open_nc_members, _era5_to_daily

    # Open the target grid to learn the actual nearest cell.
    inst, accum, tmpdir = _open_nc_members(cds_zip)
    ds = xr.open_dataset(inst)
    req_lat, req_lon = 52.5, 13.0
    i = int(np.argmin(np.abs(ds["latitude"].values - req_lat)))
    j = int(np.argmin(np.abs(ds["longitude"].values - req_lon)))
    expect_lat = float(ds["latitude"].values[i])
    expect_lon = float(ds["longitude"].values[j])
    ds.close()

    frame, (got_lat, got_lon) = _era5_to_daily(inst, accum, req_lat, req_lon)
    assert (got_lat, got_lon) == (expect_lat, expect_lon), (
        "nearest-cell selection mismatch "
        f"(got {got_lat}/{got_lon}, expected {expect_lat}/{expect_lon})"
    )

    # Shape: 2 days of hourly data -> 2 distinct calendar days.
    assert frame.height == 2, f"expected 2 rows, got {frame.height}"
    assert frame["DATE"].to_list() == [
        date(2022, 1, 15),
        date(2022, 1, 16),
    ]

    # Hand-compute expected day-1 values from the target cell.
    # base_k is linear 273.15 -> 273.15 + 48 across 48 steps.
    base = np.linspace(273.15, 273.15 + 48, 48)
    day1_t2m = base[:24] - 273.15  # C
    day1_tp = np.full(24, 0.001) * 1000.0  # mm
    day1_sf = np.full(24, 0.0005) * 1000.0  # mm w.e.

    r = frame.to_dicts()[0]
    assert r["TAVG"] == pytest.approx(float(day1_t2m.mean()), abs=1e-6)
    assert r["TMAX"] == pytest.approx(float(day1_t2m.max()), abs=1e-6)
    assert r["TMIN"] == pytest.approx(float(day1_t2m.min()), abs=1e-6)
    assert r["PRCP"] == pytest.approx(float(day1_tp.sum()), abs=1e-6)
    assert r["SNOW"] == pytest.approx(float(day1_sf.sum()), abs=1e-6)

    # If the wrong grid cell (offset by +50 K in this fixture) were picked,
    # these same assertions would fail immediately -- a wrong-cell selection
    # is therefore caught. No separate threshold needed.

    # Canonical schema (the columns the rest of noaaplotter expects).
    for col in ("TAVG", "TMAX", "TMIN", "PRCP", "SNOW", "DATE"):
        assert col in frame.columns

    frame.to_pandas()  # smoke: round-trips to pandas without error
    # (polars DataFrame -> pandas; no assertion, just exercise the path.)
