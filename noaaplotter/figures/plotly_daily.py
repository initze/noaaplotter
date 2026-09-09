"""Interactive (plotly) daily series figure.

Mirrors `NOAAPlotter.plot_weather_series`: temperature panel (observed vs
climatological mean +/- std with red/blue fill, no-data shading, record
markers) plus precipitation panel (bars, 7-day rolling sum, no-data shading,
optional cumulative snowfall on a secondary axis).

When `window=(start, end)` is given (the user's selected plotting period) the
figure carries the ENTIRE observed series and only the initial view is limited
to that window — users can zoom out step by step ("1y / 3y / All" buttons) to
browse the full record.  When no window is given the old behaviour applies
(the series shown is exactly what is passed in).
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

C_HIGH = "#d6604d"
C_LOW = "#4393c3"
YEAR_BAND = "rgba(0,0,0,0.025)"  # light grey per calendar year (even years white)


def _clean(v):
    """Convert value to float or None if NaN."""
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


def _add_year_bands(fig, dates, row):
    """Alternating light-grey / white background bands per calendar year.

    Odd years get a very light grey band, even years stay white — same
    convention as the monthly plots.  ``add_shape`` with ``yref='paper'``
    spans the full plot height of the given subplot row.
    """
    years = sorted({d.year for d in dates})
    axis = f"y{row}" if row != 1 else "y"
    for year in years:
        if year % 2 == 0:
            continue  # white: nothing to draw
        fig.add_shape(
            type="rect",
            x0=f"{year}-01-01",
            x1=f"{year}-12-31",
            y0=0, y1=1,
            yref=f"{axis} domain",
            xref=f"x{row}" if row != 1 else "x",
            fillcolor=YEAR_BAND,
            line_width=0,
            layer="below",
        )


def make_daily_figure(df_obs, x_dates, x_dates_short, y_clim, y_clim_hi, y_clim_lo,
                      ext_hi=None, ext_lo=None, snow_dates=None, snow_acc=None,
                      snow_tail=None, show_snow_accumulation=True,
                      plot_pmax=None, plot_snowmax=None, title=None,
                      figsize=(900, 600), window=None):
    """Build the interactive daily figure.

    window : (start, end) timestamps, optional
        Initial visible x-range.  When set, the full observed series is shown
        and only the initial view is clipped to this period.
    """
    if x_dates_short is not None:
        dates = list(x_dates_short["DATE"])
    else:
        dates = list(df_obs["DATE"])
    xfull = list(x_dates["DATE"]) if x_dates is not None else dates
    obs = np.asarray(df_obs["TMEAN"], dtype=float)
    prcp = np.asarray(df_obs["PRCP"], dtype=float)
    # Full-window climatology (drives the reference lines, so the x-axis still
    # runs to the requested end date even when it lies in the future).
    clim_full = np.asarray(y_clim, dtype=float)
    clim_hi_full = np.asarray(y_clim_hi if y_clim_hi is not None else y_clim, dtype=float)
    clim_lo_full = np.asarray(y_clim_lo if y_clim_lo is not None else y_clim, dtype=float)
    # Climatology aligned to the OBSERVED span. The requested window may extend
    # past the last available data (future end date); every trace derived from
    # the observed series must line up with it — mirroring the static render,
    # which fills against y_clim.loc[clim_locs_short].
    if y_clim is not None:
        clim = np.asarray(y_clim.reindex(df_obs["DATE"]), dtype=float)
        clim_hi = np.asarray(y_clim_hi.reindex(df_obs["DATE"]), dtype=float)
        clim_lo = np.asarray(y_clim_lo.reindex(df_obs["DATE"]), dtype=float)
    else:
        clim = clim_hi = clim_lo = np.full(len(df_obs), np.nan)

    # 7-day rolling sum of precipitation (computed early: the precipitation
    # y-range must include it so the full line is visible initially)
    prcp_rolling = pd.Series(prcp).rolling(window=7, min_periods=1, center=True).sum()

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        row_heights=[0.6, 0.4], vertical_spacing=0.07)

    # --- calendar-year background bands (light grey / white), both panels
    for row in (1, 2):
        _add_year_bands(fig, dates, row)

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
    fig.add_trace(go.Scatter(x=xfull, y=clim_full, name="Climatological Mean",
                             line=dict(color="rgba(0,0,0,0.5)", width=2),
                             hovertemplate="Climatology: %{y:.2f} °C<extra></extra>"), 1, 1)
    fig.add_trace(go.Scatter(x=xfull, y=clim_hi_full, name="Std of Climatological Mean",
                             line=dict(color="rgba(0,0,0,0.4)", width=1, dash="dot"),
                             hovertemplate="Upper 1σ: %{y:.2f} °C<extra></extra>"), 1, 1)
    fig.add_trace(go.Scatter(x=xfull, y=clim_lo_full, showlegend=False,
                             line=dict(color="rgba(0,0,0,0.4)", width=1, dash="dot"),
                             hovertemplate="Lower 1σ: %{y:.2f} °C<extra></extra>"), 1, 1)
    fig.add_trace(go.Scatter(x=dates, y=list(pd.Series(obs).where(pd.notna(obs))),
                             name="Observed Temperatures",
                             line=dict(color="rgba(0,0,0,0.4)", width=1.2),
                             hovertemplate="Observed: %{y:.2f} °C<extra></extra>"), 1, 1)

    # --- temperature: y-range + no-data shading + zero line.
    # The range covers EVERYTHING visible (observed series AND climatology)
    # so no value is clipped in the initial view.
    span_hi = float(np.nanmax(np.concatenate([obs, clim_hi_full])))
    span_lo = float(np.nanmin(np.concatenate([obs, clim_lo_full])))
    fig.update_yaxes(range=[span_lo, span_hi], title="Temperature in °C",
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

    # --- precipitation: bars + no-data shading.
    # y-range includes the 7-day rolling sum (often higher than the max daily
    # bar) so the full rolling line is visible in the initial view.
    rolling_max = float(np.nanmax(prcp_rolling.to_numpy()))
    rolling_max = rolling_max if np.isfinite(rolling_max) else 0.0
    if plot_pmax is not None:
        prcp_top = float(plot_pmax)
    else:
        base = float(np.nanmax(prcp)) if np.size(prcp) else 0.0
        prcp_top = max(base * 1.15, rolling_max * 1.15, 1.0)
    fig.update_yaxes(range=[0, prcp_top], title="Precipitation in mm", row=2, col=1)
    fig.add_trace(go.Bar(x=dates, y=list(pd.Series(prcp).where(pd.notna(prcp))),
                         name="Precipitation", marker_color=C_LOW,
                         hovertemplate="Precipitation: %{y:.2f} mm<extra></extra>"), 2, 1)
    nan_p = [d for d, v in zip(dates, prcp) if v is None or pd.isna(v)]
    if nan_p:
        fig.add_trace(go.Bar(x=nan_p, y=[prcp_top] * len(nan_p), base=0, width=1,
                             marker_color="rgba(0,0,0,0.2)",
                             name="No Data", showlegend=True), 2, 1)

    # --- rolling 7-day precipitation sum
    # Convert to list for Plotly
    prcp_rolling_list = list(prcp_rolling.where(pd.notna(prcp_rolling)))
    fig.add_trace(go.Scatter(x=dates, y=prcp_rolling_list,
                             name="7-Day Rolling Sum of Precipitation",
                             line=dict(color="rgba(30,144,255,0.7)", width=2),
                             hovertemplate="7-day Rolling Sum: %{y:.2f} mm<extra></extra>"), 2, 1)

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

    layout = dict(height=figsize[1], width=figsize[0],
                  template="plotly_white", hovermode="x unified",
                  showlegend=True,
                  legend=dict(orientation="h", yanchor="bottom", y=1.02,
                              xanchor="left", x=0),
                  margin=dict(l=40, r=40, t=50 if title else 40, b=30),
                  title=dict(text=title, y=0.98) if title else None,
                  xaxis_rangeslider_visible=False,
                  xaxis_title="Date")
    # --- initial x-view + zoom-out controls (window = user-selected period)
    # NOTE: with shared_xaxes the visible master axis is x2 (xaxis "matches"
    # it and is hidden), so the initial range must be applied to BOTH.
    if window is not None:
        d0 = pd.Timestamp(window[0]).strftime("%Y-%m-%d")
        d1 = pd.Timestamp(window[1]).strftime("%Y-%m-%d")
        layout["xaxis_range"] = [d0, d1]
        layout["xaxis2_range"] = [d0, d1]

        data_lo = min(dates).strftime("%Y-%m-%d")
        data_hi = max(dates).strftime("%Y-%m-%d")

        # Visible "legend-style" zoom buttons (top row, right side; the
        # legend is anchored left, so nothing is covered).  Clicks are
        # wired by the post-script (injected by write_html); each button
        # keeps the CENTER of the current view and widens around it, so
        # repeated presses step outward instead of drifting to later years.
        layout["annotations"] = [
            dict(text=lab, xref="paper", yref="paper",
                 x=0.975 - 0.045 * i, y=0.99,
                 showarrow=False, align="center",
                 bordercolor="#94a3b8", borderwidth=1, borderpad=3,
                 bgcolor="white",
                 font=dict(size=13, color="#1f2937",
                           family="Segoe UI, Arial, sans-serif"),
                 opacity=1)
            for i, lab in enumerate(["1y", "3y", "All"])
        ]
    fig.update_layout(**layout)
    return fig


def write_daily_html(fig, path, data_lo=None, data_hi=None):
    """Write the figure HTML, then inject the zoom-button click behaviour.

    The plotly Figure object rejects non-standard attributes (e.g.
    ``post_script``), so the small click handler is appended to the saved
    HTML file directly — which is fully under our control.
    """
    import re

    fig.write_html(path)
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()

    if data_lo is None or data_hi is None:
        return

    script = (
        "<script>(function(){"
        "function getGd(){"
        "if(window.Plotly&&Plotly.figs){var k=Object.keys(Plotly.figs);if(k.length)return Plotly.figs[k[0]];} "
        "var d=document.querySelectorAll('div');"
        "for(var i=0;i<d.length;i++){if(d[i]._fullLayout)return d[i];}"
        "return null;"
        "}"
        "var div=getGd();"
        "if(!div)return;"
        "var full=['" + data_lo + "','" + data_hi + "'];"
        "var DAY=86400000;"
        "function iso(ms){return new Date(ms).toISOString().slice(0,10);} "
        "function setRange(a,b){Plotly.relayout(div,{'xaxis.range':[a,b],'xaxis2.range':[a,b]});} "
        "function centerZoom(months){"
        "var r=(div.layout&&div.layout.xaxis2&&div.layout.xaxis2.range)||"
        "(div.layout&&div.layout.xaxis.range);"
        "if(!r)return;"
        "var a=Date.parse(r[0]),b=Date.parse(r[1]);"
        "if(isNaN(a)||isNaN(b))return;"
        "var span=Math.max(b-a,months*30*DAY);"
        "var mid=a+(b-a)/2;"
        "setRange(iso(mid-span/2),iso(mid+span/2));"
        "}"
        "div.addEventListener('click',function(e){"
        "var el=e.target;"
        "var g=el&&el.closest?el.closest('g'):null;"
        "var txt=((g&&g.textContent)||(el&&el.textContent)||'').trim();"
        "if(txt==='1y')centerZoom(12);"
        "else if(txt==='3y')centerZoom(36);"
        "else if(txt==='All')setRange(full[0],full[1]);"
        "});"
        "})();</script>"
    )
    html = html.replace("</body>", script + "\n</body>", 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
