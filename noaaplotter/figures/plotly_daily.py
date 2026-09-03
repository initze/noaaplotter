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


def _clean(v):
    v = float(v)
    return None if np.isnan(v) else v


def _grey_band(xs, top, bottom):
    """Closed light-grey polygon between two curves (no hover action)."""
    xs = list(xs)
    top_y = [_clean(v) for v in top]
    bot_y = [_clean(v) for v in bottom]
    return go.Scatter(x=xs + xs[::-1], y=top_y + bot_y[::-1],
                      fill="toself", fillcolor="rgba(190,190,190,0.18)",
                      line=dict(width=0), hoverinfo="skip",
                      showlegend=False)


def _fill_band(xs, bottom, top, hexcolor, alpha, name=None, showlegend=False):
    """Closed polygon between two curves (NaNs break the band); optional legend entry."""
    xs = list(xs)
    bot_y = [_clean(v) for v in bottom]
    top_y = [_clean(v) for v in top]
    r, g, b = (int(hexcolor[i:i + 2], 16) for i in (1, 3, 5))
    return go.Scatter(x=xs + xs[::-1], y=bot_y + top_y[::-1],
                      fill="toself", fillcolor=f"rgba({r},{g},{b},{alpha})",
                      line=dict(width=0), hoverinfo="skip",
                      name=name, showlegend=showlegend)


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

    # --- temperature: soft light-grey climatological +/- sigma envelope (no hover)
    fig.add_trace(_grey_band(dates, clim_hi, clim_lo), 1, 1)
    # --- temperature: anomaly fills between the observed line and the climate
    #     baseline (mirrors the static render): light within +/- 1 std, darker
    #     once the observation exceeds the envelope (no hover action)
    # within 1 std: mean -> obs (or mean -> sigma edge if obs is outside the band)
    upper_in = np.fmax(clim, np.fmin(obs, clim_hi))
    lower_in = np.fmin(clim, np.fmax(obs, clim_lo))
    # beyond 1 std: ONLY in the region actually exceeded by the observation
    upper_out = np.fmax(obs, clim_hi)
    lower_out = np.fmin(obs, clim_lo)
    fig.add_trace(_fill_band(dates, clim, upper_in, C_HIGH, 0.3,
                             name="Above average Temperature",
                             showlegend=True), 1, 1)
    fig.add_trace(_fill_band(dates, clim_hi, upper_out, C_HIGH, 0.7,
                             name="Above average Temperature (> 1 std)",
                             showlegend=True), 1, 1)
    fig.add_trace(_fill_band(dates, lower_in, clim, C_LOW, 0.3,
                             name="Below average Temperature",
                             showlegend=True), 1, 1)
    fig.add_trace(_fill_band(dates, lower_out, clim_lo, C_LOW, 0.7,
                             name="Below average Temperature (> 1 std)",
                             showlegend=True), 1, 1)
    # --- reference lines + observed (visual weight matched to the static render:
    #     normals lw=2 @ 50% alpha, observed lw=1.2 @ 40% alpha,
    #     sigma edges lw=1 @ 40% alpha). Hover values truncated to 2 decimals.
    fig.add_trace(go.Scatter(x=xfull, y=clim, name="Climatological Mean",
                             line=dict(color="rgba(0,0,0,0.5)", width=2),
                             hovertemplate="Climatology: %{y:.2f} °C<extra></extra>"), 1, 1)
    fig.add_trace(go.Scatter(x=xfull, y=clim_hi, name="Std of Climatological Mean",
                             line=dict(color="rgba(0,0,0,0.4)", width=1, dash="dot"),
                             hovertemplate="Upper 1σ: %{y:.2f} °C<extra></extra>"), 1, 1)
    fig.add_trace(go.Scatter(x=xfull, y=clim_lo, showlegend=False,
                             line=dict(color="rgba(0,0,0,0.4)", width=1, dash="dot"),
                             hovertemplate="Lower 1σ: %{y:.2f} °C<extra></extra>"), 1, 1)
    fig.add_trace(go.Scatter(x=dates, y=list(pd.Series(obs).where(pd.notna(obs))),
                             name="Observed Temperatures",
                             line=dict(color="rgba(0,0,0,0.4)", width=1.2),
                             hovertemplate="Observed: %{y:.2f} °C<extra></extra>"), 1, 1)

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
                                 marker=dict(symbol="x", size=8, color=C_HIGH),
                                 hovertemplate="Record high: %{y:.2f} °C<extra></extra>"), 1, 1)
    if ext_lo is not None and len(ext_lo[0]) > 0:
        fig.add_trace(go.Scatter(x=list(ext_lo[0]), y=list(ext_lo[1]),
                                 mode="markers", name="Record Low on Date",
                                 marker=dict(symbol="x", size=8, color=C_LOW),
                                 hovertemplate="Record low: %{y:.2f} °C<extra></extra>"), 1, 1)

    # --- precipitation: bars + no-data shading
    prcp_top = (float(np.nanmax(prcp) * 1.15) if np.nanmax(prcp) > 0 else 1.0)
    if plot_pmax is not None:
        prcp_top = plot_pmax
    fig.update_yaxes(range=[0, prcp_top], title="Precipitation in mm", row=2, col=1)
    fig.add_trace(go.Bar(x=dates, y=list(pd.Series(prcp).where(pd.notna(prcp))),
                         name="Precipitation", marker_color=C_LOW,
                         hovertemplate="Precipitation: %{y:.2f} mm<extra></extra>"), 2, 1)
    nan_p = [d for d, v in zip(dates, prcp) if v is None or pd.isna(v)]
    if nan_p:
        fig.add_trace(go.Bar(x=nan_p, y=[prcp_top] * len(nan_p), base=0, width=1,
                             marker_color="rgba(0,0,0,0.2)",
                             name="No Data", showlegend=True), 2, 1)

    # --- snowfall accumulation: its OWN secondary axis on the precipitation row.
    # NOTE: add_trace() WITHOUT row/col on purpose — subplot row/col pinning would
    # force the trace onto the precipitation axis (y2) and hide the rain bars.
    if show_snow_accumulation and snow_dates is not None:
        snow_max = float(np.nanmax(snow_acc) / 10) if np.nanmax(snow_acc) > 0 else 1.0
        snow_top = plot_snowmax if plot_snowmax is not None else snow_max * 1.1
        fig.add_trace(go.Scatter(x=list(snow_dates),
                                 y=[v / 10 for v in snow_acc],
                                 name="Cumulative Snowfall",
                                 line=dict(width=0),
                                 fillcolor="rgba(0,0,0,0.2)",
                                 fill="tozeroy", yaxis="y3",
                                 hovertemplate="Snow: %{y:.2f} cm<extra></extra>"))
        fig.update_layout(yaxis3=dict(title="Cumulative Snowfall in cm", side="right",
                                      overlaying="y2", anchor="free", position=1.0,
                                      range=[0, snow_top]))
        if snow_tail is not None:
            fig.add_trace(go.Scatter(x=list(snow_tail[0]), y=list(snow_tail[1]),
                                     opacity=0.2,
                                     line=dict(color="black", width=1, dash="dash"),
                                     showlegend=False, yaxis="y3"))

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
