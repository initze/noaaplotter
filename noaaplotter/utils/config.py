# -*- coding: utf-8 -*-
"""
Central API token handling.

Tokens are read from the process environment first, then from a local
.env file (git-ignored) in the working directory. CLI arguments and
direct function arguments always take precedence over both.
"""

import os

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

if load_dotenv is not None:
    load_dotenv()


def get_noaa_token(cli_token=""):
    """Return NOAA CDO API token: CLI arg, else env / .env."""
    return cli_token or os.environ.get("NOAA_API_TOKEN", "")


def get_cds_credentials(cli_token=""):
    """Return (token, url) for the CDS API: CLI arg, else env / .env."""
    token = cli_token or os.environ.get("CDS_API_TOKEN", "")
    url = os.environ.get("CDS_API_URL", "https://cds.climate.copernicus.eu/api")
    return token, url
