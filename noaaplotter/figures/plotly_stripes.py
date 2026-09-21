"""Interactive (plotly) warming-stripes figure.

One horizontal band of one cell per year or month. The caller supplies the
display values and the colorscale/bounds (so the builder stays mode-agnostic).
"""
import math

import plotly.graph_objects as go

# House palette (matches the static stripes: cool-blue low, warm-red high)
C_HIGH = "#d6604d"
C_LOW = "#4393c3"


def _not_nan(v):
    return v is not None and not (isinstance(v, float) and math.isnan(v))


def make_stripes_figure(
    values,
    labels,
    title,
    height=220,
    colorscale=None,
    zmin=0.0,
    zmax=1.0,
    colorbar_title="",
    format_spec=".1f",
    hover_ctx="°C vs climate",
    annotations=False,
):
    """Build the interactive warming-stripes figure.

    Parameters
    ----------
    values : list of float (or None / NaN)
        One value per stripe — already in the units the caller wants to show.
    labels : list of str
        Aligned x labels ("1980", "1981", … or "Jan-1980", "Feb-1980", …).
    title : str
        Figure title, shown only when ``annotations=True``.
    height : int
        Figure height in px.
    colorscale : list of [t, hex]
        Plotly colorscale. When None, the default diverging cool-warm
        palette is used.
    zmin / zmax : float
        Color-scale bounds in the *display value* units.
    colorbar_title : str
        Label for the colorbar ("", or None, to hide the colorbar).
    format_spec : str
        printf-style numeric format in the hover text.
    hover_ctx : str
        Text following the hover number (e.g. "°C vs climate").
    annotations : bool
        When True, show the title, x-ticks and colorbar. When False (default)
        the figure is the bare band — no chrome at all.
    """
    if colorscale is None:
        colorscale = [[0.0, C_LOW], [0.5, "#ffffff"], [1.0, C_HIGH]]

    n = len(values)
    z = [[None if not _not_nan(v) else float(v) for v in values]]
    show_colorbar = bool(colorbar_title) and annotations
    hm = dict(
        z=z,
        x=[str(x) for x in labels],
        y=[""],
        colorscale=colorscale,
        zmin=zmin,
        zmax=zmax,
        showscale=show_colorbar,
        hovertemplate=(
            "%{{x}}: %{{z:{0}}} {1}<extra>Warming stripes</extra>".format(
                format_spec, hover_ctx
            )
        ),
    )
    if show_colorbar:
        hm["colorbar"] = dict(title=colorbar_title, lenmode="fraction", len=0.55)
    fig = go.Figure(go.Heatmap(**hm))

    # With N cells and height H, we want the *cell width* to be about 1/N of
    # the figure width — so the band fills the figure edge-to-edge with no
    # gaps.  The overall band is kept wide-and-short: width : height = 8 : 1.
    fig_width = int(height * 8) + (90 if annotations else 25)
    fig.update_layout(
        template="plotly_white",
        height=height,
        width=fig_width,
        xaxis=dict(
            visible=annotations,   # hide the entire axis (line + ticks) when bare
            showticklabels=annotations,
            tickangle=-45,
        ),
        yaxis=dict(showticklabels=False, zeroline=False, showgrid=False),
        margin=dict(
            l=15,
            r=(70 if annotations else 20),
            t=(45 if annotations else 15),
            b=(45 if annotations else 15),
        ),
        title=dict(text=title if annotations else "", x=0),
        hovermode="x",
        dragmode=False,
    )
    return fig
