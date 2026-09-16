"""Interactive (plotly) warming-stripes figure.

One horizontal band of one cell per value (a year, or a month), coloured by
its anomaly from the climate mean: cool-blue below, warm-red above, white at
zero (symmetric scale). Mirrors the matplotlib `plot_warming_stripes`.
"""
import math

import plotly.graph_objects as go

# House palette (same as the rest of the interactive figures)
C_HIGH = "#d6604d"
C_LOW = "#4393c3"


def _not_nan(v):
    return v is not None and not (isinstance(v, float) and math.isnan(v))


def _scale(values):
    vals = [abs(float(v)) for v in values if _not_nan(v)]
    return max([1e-6] + vals)


def make_stripes_figure(values, labels, title, height=230, cell_px=18, unit="°C"):
    """Build the interactive warming-stripes figure.

    values  : list of numeric anomalies (None / NaN allowed for missing)
    labels  : aligned list of x labels (e.g. years, or "Mon-YYYY")
    title   : figure title
    unit    : unit suffix for the hover text (e.g. "°C" or "mm")
    """
    scale = _scale(values)
    z = [[None if not _not_nan(v) else float(v) for v in values]]
    fig = go.Figure(
        go.Heatmap(
            z=z,
            x=[str(x) for x in labels],
            y=["Anomaly"],
            colorscale=[[0.0, C_LOW], [0.5, "#ffffff"], [1.0, C_HIGH]],
            zmin=-scale,
            zmax=scale,
            showscale=False,
            hovertemplate=f"%{{x}}: %{{z:.1f}}{unit} vs climate<extra>Warming stripes</extra>",
        )
    )
    fig.update_layout(
        template="plotly_white",
        height=height,
        width=int(len(labels) * cell_px) + 150,
        xaxis_tickangle=-45,
        xaxis_title="",
        yaxis=dict(showticklabels=False, zeroline=False),
        margin=dict(l=15, r=35, t=55, b=60),
        title=dict(text=title, x=0),
        hovermode="x",
    )
    return fig
