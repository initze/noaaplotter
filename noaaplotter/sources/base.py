"""DataSource registry + canonical schema.

Every source fetches daily weather data and maps it into the canonical
schema (the parquet NOAA downloader already writes), so downstream
(plotting, climate stats) is schema-agnostic.
"""
import polars as pl

#: canonical schema — all sources must return these columns
CANONICAL_COLUMNS = [
    "STATION", "NAME", "DATE", "TAVG", "TMAX", "TMIN", "PRCP", "SNOW",
]


def validate_schema(df: pl.DataFrame) -> pl.DataFrame:
    """Check that df has the canonical schema; raise if not."""
    missing = [c for c in CANONICAL_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Source output missing canonical columns: {missing}")
    return df


def _noaa_source(**kwargs):
    """NOAA GHCND source (existing download_from_noaa, incremental parquet).

    Requires `station_id`, `start`, `end`, `output_file`; token from
    `token` kwarg or NOAA_API_TOKEN (env / .env).
    """
    from noaaplotter.utils.config import get_noaa_token
    from noaaplotter.utils.download_utils import download_from_noaa

    token = get_noaa_token(kwargs.pop("token", None))
    if not token:
        raise ValueError(
            "NOAA source needs an API token: set NOAA_API_TOKEN (env or .env) "
            "or pass token=. See .env.example."
        )
    required = ["station_id", "start", "end"]
    missing = [k for k in required if kwargs.get(k) in (None, "")]
    if missing:
        raise ValueError(f"noaa source missing required kwarg(s): {missing}")
    return download_from_noaa(
        output_file=kwargs.get("output_file") or "noaa_data.parquet",
        start_date=kwargs["start"],
        end_date=kwargs["end"],
        datatypes=kwargs.get("datatypes") or ["TMIN", "TMAX", "PRCP", "SNOW"],
        loc_name=kwargs.get("loc_name") or "",
        station_id=kwargs["station_id"],
        noaa_api_token=token,
        n_jobs=kwargs.get("n_jobs", 1),
    )


def _open_meteo_source(**kwargs):
    """Open-Meteo Archive source (ERA5, no API key).

    Requires `latitude`, `longitude`, `start`, `end`.
    """
    from noaaplotter.sources.open_meteo import fetch_open_meteo

    return _coordinate_source(fetch_open_meteo, **kwargs)


def _cds_source(**kwargs):
    """Copernicus CDS source (ERA5, account required).

    Requires `latitude`, `longitude`, `start`, `end` (same as open_meteo).
    """
    from noaaplotter.sources.cds import fetch_cds_era5

    return _coordinate_source(fetch_cds_era5, **kwargs)


def _coordinate_source(fetch, **kwargs):
    missing = [
        k
        for k in ("latitude", "longitude", "start", "end")
        if kwargs.get(k) in (None, "")
    ]
    if missing:
        raise ValueError(f"source missing required kwarg(s): {missing}")
    return fetch(
        float(kwargs["latitude"]),
        float(kwargs["longitude"]),
        kwargs["start"],
        kwargs["end"],
        **{k: v for k, v in kwargs.items() if k not in ("latitude", "longitude", "start", "end")},
    )


#: source name -> callable(**kwargs) -> DataFrame / path
SOURCES = {
    "noaa": _noaa_source,
    "open_meteo": _open_meteo_source,
    "cds": _cds_source,
}


def get_source(name: str):
    if name not in SOURCES:
        raise ValueError(f"Unknown source '{name}'. Available: {sorted(SOURCES)}")
    return SOURCES[name]
