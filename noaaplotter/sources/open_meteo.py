"""Open-Meteo Archive API source (ERA5, no API key).

Returns the canonical NOAA daily-summaries schema so it can be used exactly
like a NOAA station file. Coverage is ERA5 back to 1940; single geographic
point (lat/lon). Snow is reported in cm (SNWD).
"""
import polars as pl
import requests

API_URL = "https://archive-api.open-meteo.com/v1/archive"

_DAILY_VARS = [
    "temperature_2m_mean",   # -> TAVG
    "temperature_2m_min",    # -> TMIN
    "temperature_2m_max",    # -> TMAX
    "precipitation_sum",     # -> PRCP (mm)
    "snowfall_sum",          # -> SNOW (cm)
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
    """
    from datetime import datetime, timedelta

    dt_start = datetime.strptime(start, "%Y-%m-%d")
    dt_end = datetime.strptime(end, "%Y-%m-%d")
    station_id = f"{latitude:.4f},{longitude:.4f}"

    frames = []
    cur = dt_start
    while cur <= dt_end:
        chunk_end = min(cur + timedelta(days=CHUNK_DAYS - 1), dt_end)
        frames.append(_fetch_chunk(latitude, longitude, cur, chunk_end, station_id))
        cur = chunk_end + timedelta(days=1)

    df = pl.concat(frames) if frames else _empty()
    return df.with_columns(pl.lit(name).alias("NAME"))


def _empty():
    return pl.DataFrame(
        {
            "STATION": [None], "NAME": [None],
            "DATE": pl.Series([], dtype=pl.Date),
            "TAVG": [None], "TMAX": [None], "TMIN": [None],
            "PRCP": [None], "SNOW": [None],
        }
    )


def _fetch_chunk(latitude, longitude, dt_start, dt_end, station_id):
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": dt_start.strftime("%Y-%m-%d"),
        "end_date": dt_end.strftime("%Y-%m-%d"),
        "daily": ",".join(_DAILY_VARS),
        "timezone": "UTC",
    }
    r = requests.get(API_URL, params=params, timeout=60)
    if r.status_code != 200:
        raise RuntimeError(f"Open-Meteo request failed ({r.status_code}): {r.text[:300]}")
    d = r.json()
    if "error" in d:
        raise RuntimeError(f"Open-Meteo error: {d['error']} — {d.get('reason', '')}")

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
    for c in ("TAVG", "TMAX", "TMIN", "PRCP", "SNOW"):
        if c in df.columns:
            df = df.with_columns(pl.col(c).cast(pl.Float64, strict=False))
    df.write_parquet(output_file)
    return output_file
