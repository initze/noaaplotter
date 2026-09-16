"""Interactive (plotly) year x month activity heatmap.

GitHub-style matrix: months on x, years on y (most recent on top), each cell
a monthly anomaly. Colours: cool-blue below, warm-red above, white at zero.
Mirrors the matplotlib `plot_activity_heatmap`.
"""
import math

import plotly.graph_objects as go

# House palette (same as the rest of the interactive figures)
C_HIGH = "#d6604d"
C_LOW = "#4393c3"

MONTHS = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]


def _not_nan(v):
    return v is not None and not (isinstance(v, float) and math.isnan(v))


def _scale(matrix):
    vals = [abs(float(v)) for row in matrix for v in row if _not_nan(v)]
    return max([1e-6] + vals)


def make_heatmap_figure(matrix, years, title, month_labels=None, height=None, unit="°C"):
    """Build the interactive year x month heatmap.

    matrix  : 2-D list, shape (n_years x n_months) of anomalies (None/NaN for missing)
    years   : list of year ints aligned to the rows (row 0 = top)
    title   : figure title
    month_labels : optional 12 short labels (default single letters)
    unit    : unit suffix for the colourbar / hover (e.g. "°C" or "mm")
    """
    months = month_labels or MONTHS
    scale = _scale(matrix)
    z = [[None if not _not_nan(v) else float(v) for v in row] for row in matrix]
    ylabels = [str(int(y)) for y in years]
    height = height or (40 + 26 * len(years))
    fig = go.Figure(
        go.Heatmap(
            z=z,
            y=ylabels,
            x=months,
            colorscale=[[0.0, C_LOW], [0.5, "#ffffff"], [1.0, C_HIGH]],
            zmin=-scale,
            zmax=scale,
            colorbar=dict(title=f"{unit} vs climate", lenmode="fraction", len=0.8),
            hovertemplate=f"%{{y}}-%{{x}}: %{{z:.1f}}{unit} vs climate",
        )
    )
    fig.update_layout(
        template="plotly_white",
        height=height,
        width=760,
        xaxis=dict(tickfont=dict(size=13)),
        yaxis=dict(autorange="reversed"),
        margin=dict(l=15, r=35, t=55, b=60),
        title=dict(text=title, x=0),
        hovermode="closest",
    )
    return fig
