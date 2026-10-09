"""Open-Meteo Archive API source (ERA5, no API key).

Returns the canonical NOAA daily-summaries schema so it can be used exactly
like a NOAA station file. Coverage is ERA5 back to 1940; single geographic
point (lat/lon). Snow is reported in cm (SNWD). Wind speed is normalised to
m/s and WDIR is the daily dominant BLOWING-FROM direction (0..360 deg).
"""
import os
import time

import polars as pl
import requests

API_URL = "https://archive-api.open-meteo.com/v1/archive"

_DAILY_VARS = [
    "temperature_2m_mean",   # -> TAVG
    "temperature_2m_min",    # -> TMIN
    "temperature_2m_max",    # -> TMAX
    "precipitation_sum",     # -> PRCP (mm)
    "snowfall_sum",          # -> SNOW (cm)
    "wind_speed_10m_mean",       # -> WSPD (m/s)
    "wind_direction_10m_dominant",  # -> WDIR (deg, blowing FROM)
]

CHUNK_DAYS = 92  # generous sub-chunk to stay well within rate limits


def fetch_open_meteo(latitude, longitude, start, end, name="Open-Meteo ERA5"):
    """Fetch daily ERA5 data for a point.

    :param latitude: geographic latitude (degrees)
    :param longitude: geographic longitude (degrees)
    :param start: "yyyy-mm-dd"
    :param end: "yyyy-mm-dd"
    :param name: station NAME label written into the data
    :return: polars DataFrame with canonical schema (TAVG/TMIN/TMAX/PRCP/SNOW)

    A short pause is inserted between chunk requests to stay under the
    per-minute request quota (an over-large gap-free fetch gets 429). Override
    with OPEN_METEO_CHUNK_SLEEP_S (seconds; "0" disables) if needed.
    """
    from datetime import datetime, timedelta

    dt_start = datetime.strptime(start, "%Y-%m-%d")
    dt_end = datetime.strptime(end, "%Y-%m-%d")
    station_id = f"{latitude:.4f},{longitude:.4f}"
    try:
        chunk_sleep = float(os.environ.get("OPEN_METEO_CHUNK_SLEEP_S", "0.4"))
    except ValueError:
        chunk_sleep = 0.4

    frames = []
    cur = dt_start
    first = True
    while cur <= dt_end:
        chunk_end = min(cur + timedelta(days=CHUNK_DAYS - 1), dt_end)
        frames.append(_fetch_chunk(latitude, longitude, cur, chunk_end, station_id))
        cur = chunk_end + timedelta(days=1)
        if not first and chunk_sleep > 0:
            time.sleep(chunk_sleep)
        first = False

    df = pl.concat(frames) if frames else _empty()
    return df.with_columns(pl.lit(name).alias("NAME"))


def _empty():
    return pl.DataFrame(
        {
            "STATION": [None], "NAME": [None],
            "DATE": pl.Series([], dtype=pl.Date),
            "TAVG": [None], "TMAX": [None], "TMIN": [None],
            "PRCP": [None], "SNOW": [None],
            "WSPD": [None], "WDIR": [None],
        }
    )


def _fetch_chunk(latitude, longitude, dt_start, dt_end, station_id):
    """Fetch one 92-day chunk; on 429 (per-minute rate limit) wait and retry the
    SAME chunk in place, rather than letting the whole multi-year fetch restart."""
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": dt_start.strftime("%Y-%m-%d"),
        "end_date": dt_end.strftime("%Y-%m-%d"),
        "daily": ",".join(_DAILY_VARS),
        "wind_speed_unit": "ms",
        "timezone": "UTC",
    }
    d = None
    for attempt in range(4):
        r = requests.get(API_URL, params=params, timeout=60)
        if r.status_code == 429:
            if attempt < 3:
                time.sleep(65)  # wait out the per-minute window, retry same chunk
                continue
            raise RuntimeError(
                f"Open-Meteo still 429 after 4 tries: {r.text[:200]}")
        if r.status_code != 200:
            raise RuntimeError(f"Open-Meteo request failed ({r.status_code}): {r.text[:300]}")
        d = r.json()
        if "error" in d:
            raise RuntimeError(f"Open-Meteo error: {d['error']} — {d.get('reason', '')}")
        break
    if d is None:
        raise RuntimeError("Open-Meteo: no response after retries")

    daily = d.get("daily", {})
    dates = daily.get("time", [])
    if not dates:
        return _empty()
    out = pl.DataFrame(
        {
            "STATION": [station_id] * len(dates),
            "DATE": pl.Series(dates, dtype=pl.Date),
            "TAVG": _col(daily, "temperature_2m_mean", len(dates)),
            "TMAX": _col(daily, "temperature_2m_max", len(dates)),
            "TMIN": _col(daily, "temperature_2m_min", len(dates)),
            "PRCP": _col(daily, "precipitation_sum", len(dates)),
            "SNOW": _col(daily, "snowfall_sum", len(dates)),
            "WSPD": _col(daily, "wind_speed_10m_mean", len(dates)),
            "WDIR": _col(daily, "wind_direction_10m_dominant", len(dates)),
        }
    )
    return out


def _col(daily, key, n):
    vals = daily.get(key)
    if vals is None:
        return [None] * n
    return [v if v is not None else None for v in vals]


def save_to_parquet(df, output_file):
    """Write a canonical-schema frame to parquet (numeric columns kept numeric)."""
    for c in ("TAVG", "TMAX", "TMIN", "PRCP", "SNOW", "WSPD", "WDIR"):
        if c in df.columns:
            df = df.with_columns(pl.col(c).cast(pl.Float64, strict=False))
    df.write_parquet(output_file)
    return output_file
