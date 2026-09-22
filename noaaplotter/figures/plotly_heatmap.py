"""Interactive (plotly) months x years activity heatmap.

GitHub-style matrix: months on x (J–D), years on y (most recent on top).
Square cells: the layout's width and height are computed from ``cell_px``
so every cell is exactly ``cell_px`` on both axes.
"""
import math

import plotly.graph_objects as go

# House palette (matches the static heatmap)
C_HIGH = "#d6604d"
C_LOW = "#4393c3"
MONTHS = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]


def _not_nan(v):
    return v is not None and not (isinstance(v, float) and math.isnan(v))


def make_heatmap_figure(
    matrix,
    years,
    title,
    month_labels=None,
    colorscale=None,
    zmin=0.0,
    zmax=1.0,
    colorbar_title="",
    format_spec=".1f",
    hover_ctx="°C vs climate",
    cell_px=None,
):
    """Build the interactive months × years heatmap.

    matrix       : (n_years x 12) of display values; None / NaN for missing.
    years        : year ints aligned to the rows (row 0 = top / most recent).
    title        : figure title.
    month_labels : override for the x labels (default: "J","F",…,"D").
    colorscale   : plotly colorscale; default = diverging cool-blue/white/warm-red.
    zmin / zmax  : color-scale bounds in the *display value* units.
    colorbar_title : label for the colorbar ("" -> no colorbar).
    format_spec : printf-style numeric format in the hover text.
    hover_ctx   : text after the hover number (e.g. "°C", "th percentile").
    cell_px     : square cell size in px. Default None = auto: cells scale so the
                  whole figure fits ~700px tall (a standard 720p screen) whether
                  the record spans 40 or 200+ years (clamped to 4..20 px).
    """
    if colorscale is None:
        colorscale = [[0.0, C_LOW], [0.5, "#ffffff"], [1.0, C_HIGH]]
    months = month_labels or MONTHS

    n_years = len(years)
    z = [[None if not _not_nan(v) else float(v) for v in row] for row in matrix]
    ylabels = [str(int(y)) for y in years]
    show_colorbar = bool(colorbar_title)

    hm = dict(
        z=z,
        y=ylabels,
        x=months,
        colorscale=colorscale,
        zmin=zmin,
        zmax=zmax,
        showscale=show_colorbar,
        hovertemplate=(
            "%{{y}}-%{{x}}: %{{z:{0}}} {1}".format(format_spec, hover_ctx)
        ),
    )
    if show_colorbar:
        hm["colorbar"] = dict(title=colorbar_title, lenmode="fraction", len=0.8)
    fig = go.Figure(go.Heatmap(**hm))

    # Square cells: auto-scale so the whole figure fits ~700px tall
    # (a standard 720p screen) unless the caller fixes cell_px.
    if cell_px is None:
        cell_px = int(max(4, min(16, 700 / max(n_years, 1))))
    plot_w = 12 * cell_px
    plot_h = n_years * cell_px
    fig.update_layout(
        template="plotly_white",
        height=plot_h + 70,      # +70 for title + x labels + margin
        width=plot_w + 110,     # +110 for y labels + colorbar
        xaxis=dict(tickfont=dict(size=13)),
        yaxis=dict(autorange="reversed", tickfont=dict(size=11)),
        margin=dict(l=55, r=(90 if show_colorbar else 30), t=55, b=50),
        title=dict(text=title, x=0),
        hovermode="closest",
        dragmode=False,
    )
    return fig
