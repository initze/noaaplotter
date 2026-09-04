"""Data sources: fetch daily weather data into the canonical NOAA schema.

    from noaaplotter.sources import fetch_open_meteo, fetch_cds_era5
    fetch_open_meteo(lat, lon, start, end)   # ERA5 via Open-Meteo, no key
    fetch_cds_era5(lat, lon, start, end)     # ERA5 via Copernicus CDS (account)
"""
from .base import SOURCES, get_source, validate_schema
from .cds import fetch_cds_era5
from .open_meteo import fetch_open_meteo

__all__ = [
    "SOURCES",
    "get_source",
    "validate_schema",
    "fetch_open_meteo",
    "fetch_cds_era5",
]
