"""Interactive (plotly) daily series figure.

Mirrors `NOAAPlotter.plot_weather_series`: temperature panel (observed vs
climatological mean +/- std with red/blue fill, no-data shading, record
markers) plus precipitation panel (bars, no-data shading, optional
cumulative snowfall on a secondary axis).
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

C_HIGH = "#d6604d"
C_LOW = "#4393c3"


def _rgba(hexcolor, alpha):
    r, g, b = (int(hexcolor[i:i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r},{g},{b},{alpha})"


def _clean(v):
    v = float(v)
    return None if np.isnan(v) else v


def _band(xs, top, bottom, hexcolor, alpha, name=None, showlegend=False):
    """Closed polygon between two curves (NaNs break the band)."""
    xs = list(xs)
    top_y = [_clean(v) for v in top]
    bot_y = [_clean(v) for v in bottom]
    return go.Scatter(x=xs + xs[::-1], y=top_y + bot_y[::-1],
                      fill="toself", fillcolor=_rgba(hexcolor, alpha),
                      line=dict(width=0), hoverinfo="skip",
                      showlegend=showlegend, name=name)


def make_daily_figure(df_obs, x_dates, x_dates_short, y_clim, y_clim_hi, y_clim_lo,
                      ext_hi=None, ext_lo=None, snow_dates=None, snow_acc=None,
                      snow_tail=None, show_snow_accumulation=True,
                      plot_pmax=None, plot_snowmax=None, title=None,
                      figsize=(900, 600)):
    dates = list(x_dates_short["DATE"])
    xfull = list(x_dates["DATE"])
    obs = np.asarray(df_obs["TMEAN"], dtype=float)
    clim = np.asarray(y_clim, dtype=float)
    clim_hi = np.asarray(y_clim_hi, dtype=float)
    clim_lo = np.asarray(y_clim_lo, dtype=float)
    prcp = np.asarray(df_obs["PRCP"], dtype=float)

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        row_heights=[0.6, 0.4], vertical_spacing=0.07)

    # --- temperature: climate band fills (mirror matplotlib fill_r/rr/b/bb)
    fig.add_trace(_band(dates, np.fmax(obs, clim), clim, C_HIGH, 0.5,
                        name="Above average Temperature", showlegend=True), 1, 1)
    fig.add_trace(_band(dates, np.fmax(obs, clim_hi), clim_hi, C_HIGH, 0.7), 1, 1)
    fig.add_trace(_band(dates, clim, np.fmin(obs, clim), C_LOW, 0.5,
                        name="Below average Temperature", showlegend=True), 1, 1)
    fig.add_trace(_band(dates, clim_lo, np.fmin(obs, clim_lo), C_LOW, 0.7), 1, 1)

    # --- temperature: reference lines + observed
    fig.add_trace(go.Scatter(x=xfull, y=clim, name="Climatological Mean", opacity=0.5,
                             line=dict(color="black", width=2)), 1, 1)
    fig.add_trace(go.Scatter(x=xfull, y=clim_hi, name="Std of Climatological Mean",
                             opacity=0.4, line=dict(color=C_HIGH, width=1, dash="dash")), 1, 1)
    fig.add_trace(go.Scatter(x=xfull, y=clim_lo, showlegend=False,
                             opacity=0.4, line=dict(color=C_LOW, width=1, dash="dash")), 1, 1)
    fig.add_trace(go.Scatter(x=dates, y=list(pd.Series(obs).where(pd.notna(obs))),
                             name="Observed Temperatures", opacity=0.4,
                             line=dict(color="black", width=1.2)), 1, 1)

    # --- temperature: y-range + no-data shading + zero line
    span_hi = float(np.nanmax(np.concatenate([obs, clim_hi])))
    span_lo = float(np.nanmin(np.concatenate([obs, clim_lo])))
    fig.update_yaxes(range=[span_lo, span_hi], title="Temperature in \u00b0C",
                     row=1, col=1)
    nan_t = [d for d, v in zip(dates, obs) if v is None or pd.isna(v)]
    if nan_t:
        fig.add_trace(go.Bar(x=nan_t, y=[span_hi - span_lo] * len(nan_t),
                             base=span_lo, width=1,
                             marker_color="rgba(0,0,0,0.2)",
                             name="No Data", showlegend=True), 1, 1)
    fig.add_hline(y=0, line=dict(color="rgba(0,0,0,0.5)", dash="dash"), row=1, col=1)

    # --- temperature: record extremes
    if ext_hi is not None and len(ext_hi[0]) > 0:
        fig.add_trace(go.Scatter(x=list(ext_hi[0]), y=list(ext_hi[1]),
                                 mode="markers", name="Record High on Date",
                                 marker=dict(symbol="x", size=8, color=C_HIGH)), 1, 1)
    if ext_lo is not None and len(ext_lo[0]) > 0:
        fig.add_trace(go.Scatter(x=list(ext_lo[0]), y=list(ext_lo[1]),
                                 mode="markers", name="Record Low on Date",
                                 marker=dict(symbol="x", size=8, color=C_LOW)), 1, 1)

    # --- precipitation: bars + no-data shading
    prcp_top = (float(np.nanmax(prcp) * 1.15) if np.nanmax(prcp) > 0 else 1.0)
    if plot_pmax is not None:
        prcp_top = plot_pmax
    fig.update_yaxes(range=[0, prcp_top], title="Precipitation in mm", row=2, col=1)
    fig.add_trace(go.Bar(x=dates, y=list(pd.Series(prcp).where(pd.notna(prcp))),
                         name="Precipitation", marker_color=C_LOW), 2, 1)
    nan_p = [d for d, v in zip(dates, prcp) if v is None or pd.isna(v)]
    if nan_p:
        fig.add_trace(go.Bar(x=nan_p, y=[prcp_top] * len(nan_p), base=0, width=1,
                             marker_color="rgba(0,0,0,0.2)",
                             name="No Data", showlegend=True), 2, 1)

    # --- snowfall accumulation on secondary axis over precipitation
    if show_snow_accumulation and snow_dates is not None:
        snow_max = float(np.nanmax(snow_acc) / 10) if np.nanmax(snow_acc) > 0 else 1.0
        snow_top = plot_snowmax if plot_snowmax is not None else snow_max * 1.1
        fig.add_trace(go.Scatter(x=list(snow_dates),
                                 y=[v / 10 for v in snow_acc],
                                 name="Cumulative Snowfall",
                                 line=dict(width=0),
                                 fillcolor="rgba(0,0,0,0.2)",
                                 fill="tozeroy", yaxis="y3"), 2, 1)
        fig.update_yaxes(title="Cumulative Snowfall in cm", side="right",
                         overlaying="y2", anchor="free", range=[0, snow_top])
        if snow_tail is not None:
            fig.add_trace(go.Scatter(x=list(snow_tail[0]), y=list(snow_tail[1]),
                                     opacity=0.2,
                                     line=dict(color="black", width=1, dash="dash"),
                                     showlegend=False, yaxis="y3"), 2, 1)

    fig.update_layout(height=figsize[1], width=figsize[0],
                      template="plotly_white", hovermode="x unified",
                      showlegend=True,
                      legend=dict(orientation="h", yanchor="bottom", y=1.02,
                                  xanchor="left", x=0),
                      margin=dict(l=40, r=40, t=50 if title else 40, b=30),
                      title=dict(text=title, y=0.98) if title else None,
                      xaxis_rangeslider_visible=False,
                      xaxis_title="Date")
    return fig
