"""Interactive (plotly) months × years activity heatmap.

GitHub-style matrix: months on x (J–D), years on y (most recent on top).
Square cells of 20 px each (reduced from 34 px for a smaller, screen-fitting figure).
"""
import math
from typing import Sequence

import numpy as np
import plotly.graph_objects as go


# House palette (matches the static heatmap) — RdBu has whitish colour in the centre.
DIVERGING_COLORS = [
    "#1b4e89",  # 0.0 → deep blue (cold/wet)
    "#3788c6",  # 0.2 → medium blue
    "#1ba1e2",  # 0.4 → light/blue (cooler)
    "#76c2f5",  # 0.53 → sky blue (slightly below mean)
    "#ffffff",  # 0.67 → pure white (mean/median)
    "#eaf6f0",  # 0.8  → pale cream/yellow-green (slightly above mean)
    "#bfeab9",  # 0.9  → cream/pale yellow
    "#f4cae4",  # 1.0  → light red/pale pink (upper tail)
    "#fc8d59",  # 1.2  → salmon/red
    "#e99b8e",  # 1.33 → deep red (hot/drought)
]


def _normalize_z(z_val: float, clip: bool = True) -> float:
    """Convert display value [−1.5..+3.5] to a normalized colormapscale ∈ [0...1].

    Mapping (piecewise linear):

        −1.5 → 0.0       (deep blue)
        −1.0 → 0.22      (blue)
        −0.4 → 0.50      (white-ish, ~mean)
        +0.4 → 0.75      (cream / pale yellow)
        +1.0 → 1.0       (deep red)

    Args:
        z_val: display value in [−1.5..+3.5].
        clip: if True, clamp to [−1..4] before mapping.

    Returns:
        Normalised colormapscale ∈ [0..1].
    """
    vmin, vmax = -1.5, 3.5
    if clip:
        z_val = np.clip(z_val, vmin, vmax)
    return (z_val - vmin) / (vmax - vmin)


def _normalize_z_to_colorscale(z_min: float, z_max: float, z_val: float, zmin: float, zmax: float):
    """Map a display value to normalized colormapscale using clip [zmin..zmax]."""
    z_val_clipped = np.clip(z_val, zmin, zmax)