"""Interactive (plotly) monthly barchart figure.

Mirrors `NOAAPlotter.plot_monthly_barchart`: monthly bars coloured by sign
(above/below reference), optional trailing-mean line, and a zero line.
"""
import plotly.graph_objects as go

C_HIGH = "#d6604d"
C_LOW = "#4393c3"


def make_monthly_figure(data, plot_kwargs, trailing_mean=None, title=None,
                        figsize=(900, 420)):
    """Build the interactive monthly figure.

    data : DataFrame with DATE (datetime), the value column, and optionally
           trailing_values. plot_kwargs : from setup_monthly_plot_props().
    """
    value_col = plot_kwargs["value_column"]
    value = data[value_col]
    d_low = data[value < 0]
    d_high = data[value >= 0]
    fig = go.Figure()

    fig.add_trace(go.Bar(x=d_low["DATE"], y=d_low[value_col],
                         name=plot_kwargs.get("legend_label_below") or "Below",
                         marker=dict(color=plot_kwargs["fc_low"],
                                     line=dict(width=0.5, color="white")),
                         opacity=0.92))
    fig.add_trace(go.Bar(x=d_high["DATE"], y=d_high[value_col],
                         name=plot_kwargs.get("legend_label_above") or "Above",
                         marker=dict(color=plot_kwargs["fc_high"],
                                     line=dict(width=0.5, color="white")),
                         opacity=0.92))

    if trailing_mean and "trailing_values" in data.columns:
        fig.add_trace(go.Scatter(x=data["DATE"], y=data["trailing_values"],
                                 name=f"Trailing mean: {trailing_mean} months",
                                 mode="lines", line=dict(color="black", width=1.5)))

    fig.update_yaxes(title_text=plot_kwargs["y_label"])
    fig.update_xaxes(title_text="Date")
    fig.add_hline(y=0, line_color="rgba(0,0,0,0.5)", line_dash="dash")

    fig.update_layout(height=figsize[1], width=figsize[0], template="plotly_white",
                      hovermode="x", showlegend=True,
                      legend=dict(orientation="h", yanchor="bottom", y=1.02,
                                  xanchor="left", x=0),
                      margin=dict(l=40, r=40, t=50, b=40),
                      title=title or plot_kwargs["title"])
    return fig
