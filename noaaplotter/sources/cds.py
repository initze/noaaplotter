"""CDS / Copernicus ERA5 source (account required: https://cds.climate.copernicus.eu).

Fetches daily reanalysis for a single point (lat/lon) and maps it into the
canonical NOAA daily-summaries schema, so it plots exactly like a station file.

Credentials (see noaaplotter/utils/config.py):
    CDS_API_KEY     full "https://...api:token" string for the cdsapi key, OR
    CDS_API_TOKEN   token, combined with CDS_API_URL (optional override)
Get a token at https://cds.climate.copernicus.eu (login -> My Data -> API).

Requires: cdsapi, xarray
Data lag: about 2-5 days.
"""
import os
import tempfile
from datetime import date, timedelta, datetime as dt

import polars as pl

VARIABLES = ["2m_temperature", "total_precipitation", "snowfall"]


def _key_file():
    """Create a cdsapi key file (path: `url:token`) and return its path."""
    key = os.environ.get("CDS_API_KEY", "")
    if not key:
        from noaaplotter.utils.config import get_cds_credentials

        token, url = get_cds_credentials()
        if not token:
            raise ValueError(
                "CDS source needs credentials: set CDS_API_KEY ('url:token') or "
                "CDS_API_TOKEN (+ optional CDS_API_URL) in your environment or .env "
                "(see .env.example). Get a token at https://cds.climate.copernicus.eu "
                "(login -> My Data -> API)."
            )
        key = f"{url}:{token}"
    path = os.path.join(tempfile.gettempdir(), "noaaplotter_cds_keyfile")
    with open(path, "w") as f:
        f.write(key)
    os.chmod(path, 0o600)
    return path


def _client():
    """Build a cdsapi client using the key file we wrote."""
    import cdsapi

    # `Client(key=...)` is the canonical API in cdsapi>=0.7; some builds
    # expose the class as `CDS` for backward compatibility.
    cls = getattr(cdsapi, "Client", None) or getattr(cdsapi, "CDS")
    try:
        return cls(key=_key_file())
    except TypeError:
        # older cdsapi without the `key` argument: copy the key file to the
        # default location and use the parameterless constructor.
        default = os.path.join(
            os.path.expanduser("~"), ".config", "ecmwf", "apiclient"
        )
        os.makedirs(os.path.dirname(default), exist_ok=True)
        os.replace(_key_file(), default)
        return cls()


def fetch_cds_era5(latitude, longitude, start, end, name="CDS ERA5"):
    """Fetch daily ERA5 (CDS) for a single point into the canonical schema.

    One CDS request per calendar month. Daily statistics derived locally:
        TAVG  = mean(t2m)          PRCP = sum(total_precipitation)
        TMAX  = max (t2m)          SNOW = sum(snowfall)
        TMIN  = min (t2m)

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

    frames = []
    month = date(dt_start.year, dt_start.month, 1)
    while month <= dt_end:
        out_path = os.path.join(
            tempfile.gettempdir(),
            f"noaaplotter_era5_{month.year:04d}{month.month:02d}.nc",
        )
        last_day = min(dt_end, month + timedelta(days=31))
        client.retrieve(
            "reanalysis-era5-single-levels",
            {
                "product_type": "reanalysis",
                "variable": VARIABLES,
                "area": [latitude, longitude, latitude, longitude],  # single point
                "start_date": month.strftime("%Y-%m-%d"),
                "end_date": last_day.strftime("%Y-%m-%d"),
                "time": ["%02d:00" % h for h in range(24)],
                "format": "netcdf",
            },
            out_path,
        )

        import xarray as xr

        with xr.open_dataset(out_path) as ds:
            d = ds.groupby("time.day").agg(
                tmean=("t2m", "mean"),
                tmax=("t2m", "max"),
                tmin=("t2m", "min"),
                prcp=("tp", "sum"),
                snow=("snowfall", "sum"),
            )
            rows = d.reset_index()
            frames.append(
                pl.DataFrame(
                    {
                        "DATE": [
                            r["time"].date() for r in rows.itertuples(index=False)
                        ],
                        "TAVG": rows["tmean"].tolist(),
                        "TMAX": rows["tmax"].tolist(),
                        "TMIN": rows["tmin"].tolist(),
                        "PRCP": rows["prcp"].tolist(),
                        "SNOW": rows["snow"].tolist(),
                    }
                )
            )
        os.remove(out_path)
        month = date(
            month.year + (1 if month.month == 12 else 0),
            1 if month.month == 12 else month.month + 1,
            1,
        )

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
