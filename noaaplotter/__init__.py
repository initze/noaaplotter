"""noaaplotter — plot NOAA / reanalysis weather data.

Public API:
    from noaaplotter import NOAAPlotter

See the documentation for the full API reference and CLI reference.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from noaaplotter.noaaplotter import NOAAPlotter

__all__ = ["NOAAPlotter", "__version__"]

try:
    __version__ = version("noaaplotter")
except PackageNotFoundError:  # installed without metadata (e.g. source checkout)
    __version__ = "unknown"
