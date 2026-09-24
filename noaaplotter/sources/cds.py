"""CDS / Copernicus ERA5 source (account required: https://cds.climate.copernicus.eu).

Fetches daily reanalysis for a single point (lat/lon) and maps it into the
canonical NOAA daily-summaries schema, so it plots exactly like a station file.

Credentials (see also noaaplotter/utils/config.py for NOAA/open-meteo):
    CDS_API_KEY     legacy full "https://….api:token" string
    CDS_API_TOKEN   token, combined with CDS_API_URL (optional override)
    ~/.cdsapirc     the standard CDS credentials file the portal suggests
                   (url + key), the easiest option.

Runtime dependencies: ``cdsapi`` (declared). The CDS API also returns
netCDF-4 files, which require ``xarray`` + a netCDF4 reader to open; both
are declared as noaaplotter dependencies since the 2026 CDS API migration
(``netCDF4`` bundles its own HDF5, so no extra h5py wheel is required).

Data lag: about 2-5 days. ERA5 single-levels are regridded to 0.25°; this
source requests a ±0.25° box around the point (guaranteeing at least one grid
cell) and picks the nearest cell, keeping each monthly download under ~200 KB.
"""
import calendar
import os
import tempfile
import zipfile
from datetime import date, datetime as dt

import polars as pl

#: CDS variable names (reanalysis-era5-single-levels, 2025/2026 schema).
VARIABLES = ["2m_temperature", "total_precipitation", "snowfall"]


def _credential_env():
    """Return (url, token) from the CDS env vars, or (None, None).

    Priority: CDS_API_KEY (legacy "https://….api:token") then
    CDS_API_TOKEN + optional CDS_API_URL.
    """
    token = os.environ.get("CDS_API_TOKEN", "")
    url = os.environ.get("CDS_API_URL")
    key = os.environ.get("CDS_API_KEY", "")
    if key and "://" in key:
        # "https://cds.climate.copernicus.eu/api:token"
        url_part, sep, tok = key.rpartition(":")
        if sep and tok:
            return url_part, tok
    if token:
        return url, token
    return None, None


def _client():
    """Build a CDS client from credentials.

    ``cdsapi`` 0.7+ bundles the ECMWF DataStores client and, when constructed
    with no explicit url/key, falls back to the standard ``~/.cdsapirc`` file
    (url + key). We therefore only need to pass url/key when the env supplies
    them; otherwise we let the client read ``~/.cdsapirc`` itself.
    """
    import cdsapi

    cls = getattr(cdsapi, "Client", None) or getattr(cdsapi, "CDS")
    url, token = _credential_env()
    if token:
        return cls(url=url, key=token)
    return cls()


def _open_nc_members(path):
    """Return (instantPath, accumPath, cleanupDir) from a CDS download.

    CDS (new API) returns a ZIP of two netCDF members:
      * data_stream-oper_stepType-instant.nc  -- t2m (K, instantaneous)
      * data_stream-oper_stepType-accum.nc    -- tp (m), sf (m water equiv.)
    Older releases may be a single .nc. Either path may be None.
    """
    if not zipfile.is_zipfile(path):
        return path, None, None
    tmpdir = tempfile.mkdtemp(prefix="noaaplotter_cds_")
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        z.extractall(tmpdir)
    inst = accum = None
    for n in names:
        if n.lower().count(".nc") == 0:
            continue
        if "instant" in n:
            inst = os.path.join(tmpdir, n)
        elif "accum" in n:
            accum = os.path.join(tmpdir, n)
        elif inst is None:
            inst = os.path.join(tmpdir, n)
        elif accum is None:
            accum = os.path.join(tmpdir, n)
    return inst, accum, tmpdir


def _nearest_series(ds, var, latitude, longitude):
    """Return (series, (lat, lon)) for the grid cell nearest the point.

    Series values are kept as numpy floats (unit-raw); conversion is the
    caller's job. Returns (None, None) if var is not present.
    """
    import numpy as np

    if var not in ds:
        return None, None
    i = int(np.argmin(np.abs(ds["latitude"].values - latitude)))
    j = int(np.argmin(np.abs(ds["longitude"].values - longitude)))
    series = np.asarray(ds[var].isel(latitude=i, longitude=j).values, dtype=np.float64)
    lat = float(ds["latitude"].values[i])
    lon = float(ds["longitude"].values[j])
    return series, (lat, lon)


def _era5_to_daily(nc_inst, nc_accum, latitude, longitude):
    """Convert CDS monthly netCDF member(s) into a per-day polars frame.

    Column mapping (units converted from CDS native):
        t2m [K] -> TAVG/TMAX/TMIN [C] = value - 273.15
        tp  [m] -> PRCP [mm]          = value * 1000
        sf  [m water equiv.] -> SNOW [mm w.e.] = value * 1000

    Returns (frame, (ne_lat, ne_lon)). Raises if no usable variables were
    found.
    """
    import numpy as np
    import pandas as pd
    import xarray as xr

    t_arr = tp_arr = sf_arr = None
    near = None
    time_axis = None
    for fname in (nc_inst, nc_accum):
        if fname is None:
            continue
        with xr.open_dataset(fname, decode_times=True) as ds:
            if time_axis is None:
                time_axis = ds["valid_time"].values
            if "t2m" in ds and t_arr is None:
                t_arr, near = _nearest_series(ds, "t2m", latitude, longitude)
            if "tp" in ds and tp_arr is None:
                tp_arr, tpcell = _nearest_series(ds, "tp", latitude, longitude)
                if near is None:
                    near = tpcell
            if "sf" in ds and sf_arr is None:
                sf_arr, _ = _nearest_series(ds, "sf", latitude, longitude)

    if time_axis is None:
        raise RuntimeError("CDS netCDF has no time axis (valid_time).")
    if t_arr is None and tp_arr is None and sf_arr is None:
        raise RuntimeError(
            "CDS netCDF has no recognised variables (t2m, tp, sf). "
            f"inst={nc_inst}, accum={nc_accum}"
        )
    if near is None:
        near = (round(latitude, 2), round(longitude, 2))

    ti = pd.to_datetime(time_axis)
    # groupby calendar day -> one block of contiguous hours per day.
    # DatetimeIndex.date returns a length-aligned ndarray of datetime.date.
    days_arr = ti.date
    day_blocks = {}
    for pos, day in enumerate(days_arr):
        day_blocks.setdefault(day, []).append(pos)

    days = []
    tavg, tmax, tmin, prcp, snow = [], [], [], [], []
    for day in sorted(day_blocks):
        idx = day_blocks[day]
        days.append(day)
        if t_arr is not None:
            v = t_arr[idx]
            tavg.append(float(np.mean(v)) - 273.15)
            tmax.append(float(np.max(v)) - 273.15)
            tmin.append(float(np.min(v)) - 273.15)
        if tp_arr is not None:
            prcp.append(float(np.sum(tp_arr[idx])) * 1000.0)
        if sf_arr is not None:
            snow.append(float(np.sum(sf_arr[idx])) * 1000.0)

    return pl.DataFrame(
        {
            "DATE": days,
            "TAVG": tavg if t_arr is not None else [None] * len(days),
            "TMAX": tmax if t_arr is not None else [None] * len(days),
            "TMIN": tmin if t_arr is not None else [None] * len(days),
            "PRCP": prcp if tp_arr is not None else [None] * len(days),
            "SNOW": snow if sf_arr is not None else [None] * len(days),
        }
    ), near


def fetch_cds_era5(latitude, longitude, start, end, name="CDS ERA5"):
    """Fetch daily ERA5 (CDS) for a single point into the canonical schema.

    One CDS request per calendar month. Daily statistics derived locally:
        TAVG  = mean(t2m - 273.15)          PRCP = sum(tp)       [mm]
        TMAX  = max (t2m - 273.15)          SNOW = sum(sf)       [mm we]
        TMIN  = min (t2m - 273.15)

    :param latitude: degrees north
    :param longitude: degrees east (negative for W)
    :param start: "yyyy-mm-dd"
    :param end:   "yyyy-mm-dd"
    :param name:  label for the NAME column
    :return: polars DataFrame with canonical columns
             (STATION, NAME, DATE, TAVG, TMAX, TMIN, PRCP, SNOW)
    """
    client = _client()
    dt_start = dt.strptime(start, "%Y-%m-%d").date()
    dt_end = dt.strptime(end, "%Y-%m-%d").date()
    station_id = f"{latitude:.4f},{longitude:.4f}"

    # Small box of ±0.25° around the point (guarantees one 0.25° grid cell).
    half = 0.25
    area = [
        f"{latitude - half:.4f}",
        f"{longitude - half:.4f}",
        f"{latitude + half:.4f}",
        f"{longitude + half:.4f}",
    ]

    frames = []
    month = date(dt_start.year, dt_start.month, 1)
    pid = os.getpid()
    while month <= dt_end:
        out_path = os.path.join(
            tempfile.gettempdir(),
            f"noaaplotter_era5_{month.year:04d}{month.month:02d}_{pid}.nc",
        )
        if os.path.exists(out_path):
            os.remove(out_path)
        # Clamp the last requested day to both the month end and dt_end.
        days_in_month = calendar.monthrange(month.year, month.month)[1]
        last_ok_day = days_in_month
        if dt_end.year == month.year and dt_end.month == month.month:
            last_ok_day = min(days_in_month, dt_end.day)
        request = {
            "product_type": ["reanalysis"],
            "variable": list(VARIABLES),
            "area": area,
            "year": [str(month.year)],
            "month": [f"{month.month:02d}"],
            "day": [f"{d:02d}" for d in range(1, last_ok_day + 1)],
            "time": ["%02d:00" % h for h in range(24)],
            "data_format": ["netcdf"],
        }
        client.retrieve("reanalysis-era5-single-levels", request, out_path)

        inst_path, accum_path, tmpdir = _open_nc_members(out_path)
        try:
            frame, _near = _era5_to_daily(inst_path, accum_path, latitude, longitude)
            frame = frame.with_columns(
                pl.lit(station_id).alias("STATION"),
                pl.lit(name).alias("NAME"),
            )
        finally:
            for p in (inst_path, accum_path):
                if p and os.path.exists(p):
                    try:
                        os.remove(p)
                    except OSError:
                        pass
            if tmpdir:
                import shutil

                shutil.rmtree(tmpdir, ignore_errors=True)
            if os.path.exists(out_path):
                try:
                    os.remove(out_path)
                except OSError:
                    pass
        frames.append(frame)

        # advance to next month (still bounded by dt_end)
        if month.month == 12:
            month = date(month.year + 1, 1, 1)
        else:
            month = date(month.year, month.month + 1, 1)

    if not frames:
        return pl.DataFrame(
            {
                "STATION": [None],
                "NAME": [name],
                "DATE": pl.Series([], dtype=pl.Date),
                "TAVG": [None],
                "TMAX": [None],
                "TMIN": [None],
                "PRCP": [None],
                "SNOW": [None],
            }
        )
    df = pl.concat(frames).filter(
        (pl.col("DATE") >= dt_start) & (pl.col("DATE") <= dt_end)
    )
    return df.with_columns(
        pl.lit(station_id).alias("STATION"),
        pl.lit(name).alias("NAME"),
    )


def save_to_parquet(df, output_file):
    """Write a canonical-schema frame to parquet (kept numeric)."""
    for c in ("TAVG", "TMAX", "TMIN", "PRCP", "SNOW"):
        if c in df.columns:
            df = df.with_columns(pl.col(c).cast(pl.Float64, strict=False))
    df.write_parquet(output_file)
    return output_file
