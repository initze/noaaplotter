#!/usr/bin/python
# -*- coding: utf-8 -*-

########################
# Credits here
# author: Ingmar Nitze, Alfred Wegener Institute for Polar and Marine Research
# contact: ingmar.nitze@awi.de
# version: 2021-09-06

import numpy as np
from matplotlib import dates

########################
from matplotlib import pyplot as plt

from noaaplotter.utils.dataset import NOAAPlotterDailyClimateDataset as DS_daily
from noaaplotter.utils.dataset import NOAAPlotterDailySummariesDataset as Dataset
from noaaplotter.utils.dataset import NOAAPlotterMonthlyClimateDataset as DS_monthly
from noaaplotter.utils.plot_utils import *
from noaaplotter.utils.utils import *

pd.plotting.register_matplotlib_converters()
numeric_only = True


class NOAAPlotter(object):
    """
    This class/module creates nice plots of observed weather data from NOAA
    """

    def __init__(
        self,
        input_filepath=None,
        location=None,
        remove_feb29=False,
        climate_start=dt.datetime(1981, 1, 1),
        climate_end=dt.datetime(2010, 12, 31),
        climate_filtersize=7,
    ):
        """

        :param input_filepath: path to input file
        :type input_filepath: str
        :param location: name of location
        :type location: str, optional
        :param remove_feb29:
        :type remove_feb29: bool, optional
        :param climate_start: start date of climate period, defaults to 01-01-1981
        :type climate_start: datetime, optional
        :param climate_end: start date of climate period, defaults to 31-12-2010
        :type climate_end: datetime, optional
        """
        self.input_filepath = input_filepath
        self.location = location
        self.climate_start = climate_start
        self.climate_end = climate_end
        self.remove_feb29 = remove_feb29
        self.dataset = Dataset(
            input_filepath, location=location, remove_feb29=remove_feb29
        )

        # TODO: move to respective functions?
        self.df_clim_ = DS_daily(self.dataset, filtersize=climate_filtersize)
        #

    def _make_short_dateseries(self, start_date, end_date):
        x_dates = pd.DataFrame()
        x_dates["DATE"] = pd.date_range(start=start_date, end=end_date)
        x_dates["DATE_MD"] = x_dates["DATE"].dt.strftime("%m-%d")
        # TODO: Filter Feb29
        if self.dataset.data["DATE"].max() >= end_date:
            x_dates_short = x_dates.set_index("DATE", drop=False).loc[
                pd.date_range(start=start_date, end=end_date)
            ]
        else:
            x_dates_short = x_dates.set_index("DATE", drop=False).loc[
                pd.date_range(start=start_date, end=self.dataset.data["DATE"].max())
            ]

        return x_dates, x_dates_short

    def plot_weather_series(
        self,
        start_date,
        end_date,
        plot_tmax="auto",
        plot_tmin="auto",
        plot_pmax="auto",
        plot_snowmax="auto",
        plot_extrema=True,
        show_plot=True,
        show_snow_accumulation=False,
        save_path=False,
        figsize=(9, 6),
        legend_fontsize="x-small",
        dpi=300,
        title=None,
        return_plot=False,
        engine="matplotlib",
        full_series=False,
    ):
        """
        Plotting Function to show observed vs climate temperatures and snowfall
        :param engine: "matplotlib" (static, default) or "plotly" (interactive, returned as a plotly Figure)
        :type engine: str
        :param full_series: plotly only — carry the ENTIRE observed record in the figure
            and only limit the initial view to the requested window (default: plot only
            the requested window, lightweight)
        :type full_series: bool
        :param dpi:
        :param legend_fontsize:
        :param figsize:
        :param start_date: start date of plot
        :type start_date: datetime, str
        :param end_date: end date of plot
        :type end_date: datetime, str
        :param plot_tmax:
        :type plot_tmax: int, float, str
        :param plot_tmin:
        :type plot_tmin: int, float, str
        :param plot_pmax:
        :type plot_pmax: int, float, str
        :param plot_snowmax:
        :type plot_snowmax: int, float, str
        :param plot_extrema:
        :type plot_extrema:
        :param show_plot:
        :type show_plot:
        :param show_snow_accumulation: show the cumulative snowfall axis (opt-in;
            defaults to ``False`` to match the CLI's ``--snow_acc`` default).
        :type show_snow_accumulation: bool
        :param save_path:
        :type save_path:
        :return:
        """
        import warnings

        start_date = parse_dates(start_date)
        end_date = parse_dates(end_date)
        x_dates, x_dates_short = self._make_short_dateseries(start_date, end_date)

        df_clim = self.df_clim_.data.loc[x_dates["DATE_MD"]]

        df_clim["DATE"] = x_dates["DATE"].values
        df_clim = df_clim.set_index("DATE", drop=False)

        # The requested window may extend beyond the last available data date,
        # and the underlying record may have internal gaps (missing observation
        # days). Select only dates that actually exist so no KeyError is
        # raised; missing days simply appear as gaps in the plotted line.
        data = self.dataset.data
        avail_dates = set(pd.to_datetime(data["DATE"]))
        data_first = pd.Timestamp(data["DATE"].min())
        data_last  = pd.Timestamp(data["DATE"].max())

        # x_dates_short has a DatetimeIndex (DATE) plus a DATE column; filter
        # it down to the dates that actually exist in the data file so the
        # observed-panel x-axis and the climate-alignment below use the same
        # (shorter) set of dates. Keeps the DatetimeIndex for later .loc[]
        # use (e.g. `x_dates_short.loc[:last_snow_date, ...]`).
        selected = [d for d in x_dates_short.index if d in avail_dates]
        if not selected:
            raise ValueError(
                f"No data available for the requested window "
                f"({start_date.date()} .. {end_date.date()}). "
                f"Data file covers {data_first.date()} to {data_last.date()}."
            )
        df_obs = data.set_index("DATE", drop=False).loc[selected]
        x_dates_short = x_dates_short.loc[selected]

        # Warn when the user asked for a range wider than what the data file
        # actually covers, so an accidental typo (or a future end date) is
        # visible instead of silently clipped.
        if end_date > data_last:
            warnings.warn(
                f"end date {end_date.date()} is beyond the last available "
                f"data date {data_last.date()}; plot stops at the last available date.",
                stacklevel=2,
            )
        if start_date < data_first:
            warnings.warn(
                f"start date {start_date.date()} is before the first available "
                f"data date {data_first.date()}; plot starts at the first available date.",
                stacklevel=2,
            )

        clim_locs_short = x_dates_short[
            "DATE"
        ]  # short series for incomplete years (actual data)

        # get mean and mean+-standard deviation of daily mean temperatures of climate series
        y_clim = df_clim["tmean_doy_mean"]
        y_clim_std_hi = df_clim[["tmean_doy_mean", "tmean_doy_std"]].sum(axis=1)
        y_clim_std_lo = df_clim["tmean_doy_mean"] - df_clim["tmean_doy_std"]

        # Prepare data for filled plot areas
        t_above = np.vstack(
            [df_obs["TMEAN"].values, y_clim.loc[clim_locs_short].values]
        ).max(axis=0)
        t_above_std = np.vstack(
            [df_obs["TMEAN"].values, y_clim_std_hi.loc[clim_locs_short].values]
        ).max(axis=0)
        t_below = np.vstack(
            [df_obs["TMEAN"].values, y_clim.loc[clim_locs_short].values]
        ).min(axis=0)
        t_below_std = np.vstack(
            [df_obs["TMEAN"].values, y_clim_std_lo.loc[clim_locs_short].values]
        ).min(axis=0)

        # Calculate the date of last snowfall and cumulative sum of snowfall
        snow_requested = show_snow_accumulation
        if not show_snow_accumulation:
            None
        elif (show_snow_accumulation) and ("SNOW" in df_obs.columns):
            snow_pos = df_obs[df_obs["SNOW"] > 0]
            if len(snow_pos) > 0:
                last_snow_date = snow_pos.iloc[-1]["DATE"]
                snow_acc = np.cumsum(df_obs["SNOW"])
            else:
                # no snowfall in the plotted window: skip the snow overlay
                # (previously crashed on .iloc[-1] of an empty selection)
                show_snow_accumulation = False
        elif "SNOW" not in df_obs.columns:
            show_snow_accumulation = False
            raise Warning("No snow information available")

        # ----- plotly engine: interactive figure -----
        # Default: plot ONLY the requested window (lightweight). With
        # full_series=True the figure carries the ENTIRE observed record and
        # only the initial view is limited to the requested period.
        if engine == "plotly":
            from noaaplotter.figures import make_daily_figure

            if not full_series:
                # Lightweight: plot ONLY the requested window. All series are
                # aligned to the dates that actually exist in the window.
                src_df = df_obs
                src_x = x_dates_short

                # Climatology aligned to the windowed dates
                y_clim_w = y_clim.reindex(df_obs["DATE"])
                y_clim_hi_w = y_clim_std_hi.reindex(df_obs["DATE"])
                y_clim_lo_w = y_clim_std_lo.reindex(df_obs["DATE"])

                # Record extremes: analysis over the ENTIRE record (per
                # month-day), then cropped to the plotted window — exactly
                # like the static render (groupby on the full dataset).
                ext_hi = ext_lo = None
                if plot_extrema:
                    tmax = self.dataset.data.groupby("DATE_MD").max(numeric_only=numeric_only)["TMEAN"]
                    tmin = self.dataset.data.groupby("DATE_MD").min(numeric_only=numeric_only)["TMEAN"]
                    local_obs = src_df[["DATE", "DATE_MD", "TMEAN"]].set_index(
                        "DATE_MD", drop=False)
                    local_max = tmax.loc[local_obs.index] == local_obs["TMEAN"]
                    local_min = tmin.loc[local_obs.index] == local_obs["TMEAN"]
                    ext_hi = (
                        local_obs[local_max]["DATE"].values,
                        local_obs[local_max]["TMEAN"].values,
                    )
                    ext_lo = (
                        local_obs[local_min]["DATE"].values,
                        local_obs[local_min]["TMEAN"].values,
                    )

                # Snow accumulation over the window (only when requested AND
                # the window contains snowfall)
                snow_dates = snow_acc_w = snow_tail = None
                has_snow = bool(snow_requested and "SNOW" in src_df.columns
                                and (src_df["SNOW"] > 0).any())
                if has_snow:
                    snow_acc_w = np.cumsum(src_df["SNOW"].to_numpy(dtype=float))
                    pos = int((src_df["DATE"] <= src_df.loc[src_df["SNOW"] > 0, "DATE"].iloc[-1]).sum())
                    snow_dates = src_df.iloc[:pos]["DATE"].values
                    snow_tail = (src_df.iloc[pos:]["DATE"].values,
                                 (snow_acc_w[pos:] / 10))

                fig_pl = make_daily_figure(
                    src_df, src_x, None,
                    y_clim_w, y_clim_hi_w, y_clim_lo_w,
                    ext_hi=ext_hi, ext_lo=ext_lo,
                    snow_dates=snow_dates,
                    snow_acc=snow_acc_w,
                    snow_tail=snow_tail,
                    show_snow_accumulation=has_snow,
                    plot_pmax=plot_pmax if isinstance(plot_pmax, (int, float)) else None,
                    plot_snowmax=plot_snowmax if isinstance(plot_snowmax, (int, float)) else None,
                    title=title,
                    figsize=(int(figsize[0] * 100), int(figsize[1] * 100)),
                    window=None,
                )
            else:
                # Full-window observed series (all dates actually available)
                src_df = self.dataset.data.sort_values("DATE")
                src_x = pd.DataFrame({
                    "DATE": src_df["DATE"].values,
                    "DATE_MD": src_df["DATE"].dt.strftime("%m-%d").values,
                }, index=src_df.index)

                # Climatology over the full observed window
                clim_df_all = self.df_clim_.data.loc[src_x["DATE_MD"]].copy()
                clim_df_all["DATE"] = src_x["DATE"].values
                clim_df_all = clim_df_all.set_index("DATE", drop=False)
                y_clim_w = clim_df_all["tmean_doy_mean"]
                y_clim_hi_w = clim_df_all[["tmean_doy_mean", "tmean_doy_std"]].sum(axis=1)
                y_clim_lo_w = clim_df_all["tmean_doy_mean"] - clim_df_all["tmean_doy_std"]

                # Record extremes over the full window (per month-day)
                ext_hi = ext_lo = None
                if plot_extrema:
                    tmax = src_df.groupby("DATE_MD").max(numeric_only=numeric_only)["TMEAN"]
                    tmin = src_df.groupby("DATE_MD").min(numeric_only=numeric_only)["TMEAN"]
                    local_obs = src_df[["DATE", "DATE_MD", "TMEAN"]].set_index(
                        "DATE_MD", drop=False)
                    local_max = tmax.loc[local_obs.index] == local_obs["TMEAN"]
                    local_min = tmin.loc[local_obs.index] == local_obs["TMEAN"]
                    ext_hi = (
                        local_obs[local_max]["DATE"].values,
                        local_obs[local_max]["TMEAN"].values,
                    )
                    ext_lo = (
                        local_obs[local_min]["DATE"].values,
                        local_obs[local_min]["TMEAN"].values,
                    )

                # Snow accumulation over the full window
                snow_dates = snow_acc_w = snow_tail = None
                has_snow = bool(snow_requested and "SNOW" in src_df.columns
                                and (src_df["SNOW"] > 0).any())
                if has_snow:
                    snow_acc_w = np.cumsum(src_df["SNOW"].to_numpy(dtype=float))
                    pos = int((src_df["DATE"] <= src_df.loc[src_df["SNOW"] > 0, "DATE"].iloc[-1]).sum())
                    snow_dates = src_df.iloc[:pos]["DATE"].values
                    snow_tail = (src_df.iloc[pos:]["DATE"].values,
                                 (snow_acc_w[pos:] / 10))

                fig_pl = make_daily_figure(
                    src_df, src_x, None,
                    y_clim_w, y_clim_hi_w, y_clim_lo_w,
                    ext_hi=ext_hi, ext_lo=ext_lo,
                    snow_dates=snow_dates,
                    snow_acc=snow_acc_w,
                    snow_tail=snow_tail,
                    show_snow_accumulation=has_snow,
                    plot_pmax=plot_pmax if isinstance(plot_pmax, (int, float)) else None,
                    plot_snowmax=plot_snowmax if isinstance(plot_snowmax, (int, float)) else None,
                    title=title,
                    figsize=(int(figsize[0] * 100), int(figsize[1] * 100)),
                    window=(pd.Timestamp(start_date), pd.Timestamp(end_date)),
                )
            if save_path:
                fig_pl.write_html(
                    save_path if str(save_path).endswith(".html")
                    else str(save_path) + ".html"
                )
            return fig_pl

        # ----- matplotlib rendering below -----
        fig = plt.figure(figsize=figsize, dpi=dpi)
        ax_t = fig.add_subplot(211)
        ax_p = fig.add_subplot(212, sharex=ax_t)

        # climate series (red line)
        (cm,) = ax_t.plot(x_dates["DATE"].values, y_clim.values, c="k", alpha=0.5, lw=2)
        (cm_hi,) = ax_t.plot(
            x_dates["DATE"].values,
            y_clim_std_hi.values,
            c="r",
            ls="--",
            alpha=0.4,
            lw=1,
        )
        (cm_low,) = ax_t.plot(
            x_dates["DATE"].values,
            y_clim_std_lo.values,
            c="r",
            ls="--",
            alpha=0.4,
            lw=1,
        )

        # observed series (grey line)
        (fb,) = ax_t.plot(
            x_dates_short["DATE"].values,
            df_obs["TMEAN"].values,
            c="k",
            alpha=0.4,
            lw=1.2,
        )

        # difference of observed and climate (grey area)
        fill_r = ax_t.fill_between(
            x_dates_short["DATE"].values,
            y1=t_above,
            y2=y_clim.loc[clim_locs_short].values,
            facecolor="#d6604d",
            alpha=0.5,
        )
        fill_rr = ax_t.fill_between(
            x_dates_short["DATE"].values,
            y1=t_above_std,
            y2=y_clim_std_hi.loc[clim_locs_short].values,
            facecolor="#d6604d",
            alpha=0.7,
        )
        fill_b = ax_t.fill_between(
            x_dates_short["DATE"].values,
            y1=y_clim.loc[clim_locs_short].values,
            y2=t_below,
            facecolor="#4393c3",
            alpha=0.5,
        )
        fill_bb = ax_t.fill_between(
            x_dates_short["DATE"].values,
            y1=y_clim_std_lo.loc[clim_locs_short].values,
            y2=t_below_std,
            facecolor="#4393c3",
            alpha=0.7,
        )

        if plot_extrema:
            tmax = self.dataset.data.groupby("DATE_MD").max(numeric_only=numeric_only)[
                "TMEAN"
            ]
            tmin = self.dataset.data.groupby("DATE_MD").min(numeric_only=numeric_only)[
                "TMEAN"
            ]
            local_obs = df_obs[["DATE", "DATE_MD", "TMEAN"]].set_index(
                "DATE_MD", drop=False
            )
            idx = local_obs.index
            local_max = tmax.loc[idx] == local_obs["TMEAN"]
            local_min = tmin.loc[idx] == local_obs["TMEAN"]
            # extract x and y values
            x_max = local_obs[local_max]["DATE"]
            y_max = local_obs[local_max]["TMEAN"]
            x_min = local_obs[local_min]["DATE"]
            y_min = local_obs[local_min]["TMEAN"]
            xtreme_hi = ax_t.scatter(
                x_max.values, y_max.values, c="#d6604d", marker="x"
            )
            xtreme_lo = ax_t.scatter(
                x_min.values, y_min.values, c="#4393c3", marker="x"
            )

        xlim = ax_t.get_xlim()
        ax_t.hlines(0, *xlim, linestyles="--")
        # grid
        ax_t.grid()

        # labels
        ax_t.set_xlim(start_date, end_date)
        if not (plot_tmin == "auto" and plot_tmin == "auto"):
            ax_t.set_ylim(plot_tmin, plot_tmax)
        ax_t.set_ylabel("Temperature in °C")
        ax_t.set_xlabel("Date")
        if title:
            ax_t.set_title(title)

        # add legend
        legend_handle_t = [fb, cm, cm_hi, fill_r, fill_b]
        legend_text_t = [
            "Observed Temperatures",
            "Climatological Mean",
            "Std of Climatological Mean",
            "Above average Temperature",
            "Below average Temperature",
        ]
        if plot_extrema:
            legend_handle_t.extend([xtreme_hi, xtreme_lo])
            legend_text_t.extend(["Record High on Date", "Record Low on Date"])

        # PRECIPITATION#
        # legend handles
        legend_handle_p = []
        legend_text_p = []

        # precipitation
        rain = ax_p.bar(
            x=x_dates_short["DATE"].values,
            height=df_obs["PRCP"].values,
            fc="#4393c3",
            alpha=1,
        )
        legend_handle_p.append(rain)
        legend_text_p.append("Precipitation")

        # grid
        ax_p.grid()
        # labels
        ax_p.set_ylabel("Precipitation in mm")
        ax_p.set_xlabel("Date")
        # y-axis scaling
        ax_p.set_ylim(bottom=0)
        if isinstance(plot_pmax, (int, float)):
            ax_p.set_ylim(top=plot_pmax)

        # snow
        # guarded by the show_snow_accumulation reassignment above (skipped when
        # the window has no snowfall, so last_snow_date/snow_acc exist)
        if show_snow_accumulation and ("SNOW" in df_obs.columns):
            ax2_snow = ax_p.twinx()
            # plots
            sn_acc = ax2_snow.fill_between(
                x=x_dates_short.loc[:last_snow_date, "DATE"].values,
                y1=snow_acc.loc[:last_snow_date] / 10,
                facecolor="k",
                alpha=0.2,
            )
            _ = ax2_snow.plot(
                x_dates_short.loc[last_snow_date:, "DATE"].values,
                snow_acc.loc[last_snow_date:] / 10,
                c="k",
                alpha=0.2,
                ls="--",
            )
            # y-axis label
            ax2_snow.set_ylabel("Cumulative Snowfall in cm")
            # legend
            legend_handle_p.append(sn_acc)
            legend_text_p.append("Cumulative Snowfall")
            # y-axis scaling
            ax2_snow.set_ylim(bottom=0)
            if isinstance(plot_snowmax, (int, float)):
                ax2_snow.set_ylim(top=plot_snowmax)

        # Show nodata - make function
        lo, hi = ax_t.get_ylim()
        nanvals_t = x_dates_short["DATE"].loc[pd.isna(df_obs["TMEAN"])]
        nan_bar_t = ax_t.bar(
            x=nanvals_t,
            height=hi - lo,
            bottom=lo,
            width=1,
            edgecolor=None,
            facecolor="k",
            alpha=0.2,
        )
        if len(nan_bar_t) > 0:
            legend_handle_t.append(nan_bar_t)
            legend_text_t.append("No Data")

        lo, hi = ax_p.get_ylim()
        nanvals_p = x_dates_short["DATE"].loc[pd.isna(df_obs["PRCP"])]
        nan_bar_p = ax_p.bar(
            x=nanvals_p,
            height=hi - lo,
            bottom=lo,
            width=1,
            edgecolor=None,
            facecolor="k",
            alpha=0.2,
        )
        if len(nan_bar_p) > 0:
            legend_handle_p.append(nan_bar_p)
            legend_text_p.append("No Data")

        # add Legends
        ax_t.legend(
            legend_handle_t,
            legend_text_t,
            loc="lower center",
            fontsize=legend_fontsize,
            ncol=4,
            bbox_to_anchor=(0.5, 1.02),
        )  # -0.35))
        ax_p.legend(
            legend_handle_p, legend_text_p, loc="upper left", fontsize=legend_fontsize
        )

        # set locator to monthly
        locator = dates.MonthLocator()
        ax_t.xaxis.set_major_locator(locator)
        ax_p.xaxis.set_major_locator(locator)
        plt.setp(
            ax_t.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor"
        )
        plt.setp(
            ax_p.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor"
        )
        fig.tight_layout()

        # Save Figure
        if save_path:
            fig.savefig(save_path)  # , figsize=figsize, dpi=dpi)
        # Show plot if chosen, destroy figure object at the end
        if show_plot:
            plt.show()
        if return_plot:
            return fig
        else:
            plt.close(fig)

    def plot_monthly_barchart(
        self,
        start_date,
        end_date,
        information="Temperature",
        show_plot=True,
        anomaly=False,
        anomaly_type="absolute",
        trailing_mean=None,
        save_path=False,
        figsize=(9, 4),
        dpi=100,
        legend_fontsize="x-small",
        return_plot=False,
        engine="matplotlib",
    ):
        # legend handles
        legend_handle = []
        legend_text = []

        # setup plot arguments
        plot_kwargs = setup_monthly_plot_props(information, anomaly)

        # Data Preprocessing
        if parse_dates(end_date) > self.dataset.data["DATE"].max():
            end_date = self.dataset.data["DATE"].max()
        data_monthly = DS_monthly(
            self.dataset, start=self.dataset.data["DATE"].min(), end=end_date
        )
        data_monthly.calculate_monthly_statistics()
        data_clim = DS_monthly(
            self.dataset, start=self.climate_start, end=self.climate_end
        )
        data_clim.calculate_monthly_climate()

        data = data_monthly.monthly_aggregate.reset_index(drop=False)
        df_clim = data_clim.monthly_climate.reset_index(drop=False)

        if (
            plot_kwargs["value_column"] == "prcp_diff"
            and df_clim["prcp_sum"].isna().any()
        ):
            print("Invalid precipitation values, information not available!")
            return None

        data["DATE"] = data.apply(lambda x: parse_dates_YM(x["DATE_YM"]), axis=1)
        data["Month"] = data.apply(lambda x: parse_dates_YM(x["DATE_YM"]).month, axis=1)
        data["Year"] = data.apply(lambda x: parse_dates_YM(x["DATE_YM"]).year, axis=1)
        data = (
            data.set_index("Month", drop=False)
            .join(df_clim.set_index("Month", drop=False), rsuffix="_clim")
            .sort_values("DATE_YM")
        )
        data["tmean_diff"] = data["tmean_doy_mean"] - data["tmean_doy_mean_clim"]
        data["prcp_diff"] = data["prcp_sum"] - data["prcp_sum_clim"]
        data = data.set_index("DATE", drop=False)

        # trailing mean calculation
        if trailing_mean:
            data = calc_trailing_mean(
                data, trailing_mean, plot_kwargs["value_column"], "trailing_values"
            )

        # ----- plotly engine: interactive figure -----
        if engine == "plotly":
            from noaaplotter.figures import make_monthly_figure

            fig_pl = make_monthly_figure(
                data, plot_kwargs, trailing_mean=trailing_mean,
                figsize=(int(figsize[0] * 100), int(figsize[1] * 100)),
            )
            if save_path:
                fig_pl.write_html(save_path if str(save_path).endswith(".html")
                                  else str(save_path) + ".html")
            return fig_pl

        # PLOT part
        fig = plt.figure(figsize=figsize, dpi=dpi)
        ax = fig.add_subplot(111)
        data_low = data[data[plot_kwargs["value_column"]] < 0]
        data_high = data[data[plot_kwargs["value_column"]] >= 0]
        bar_low = ax.bar(
            x=data_low["DATE"],
            height=data_low[plot_kwargs["value_column"]],
            width=30,
            align="edge",
            color=plot_kwargs["fc_low"],
            edgecolor="white",
            linewidth=0.5,
        )
        # Fix for absolute values
        if len(bar_low) > 1:
            legend_handle.append(bar_low)
            legend_text.append(plot_kwargs["legend_label_below"])
        bar_high = ax.bar(
            x=data_high["DATE"],
            height=data_high[plot_kwargs["value_column"]],
            width=30,
            align="edge",
            color=plot_kwargs["fc_high"],
            edgecolor="white",
            linewidth=0.5,
        )
        legend_handle.append(bar_high)
        legend_text.append(plot_kwargs["legend_label_above"])
        if trailing_mean:
            line_tr_mean = ax.plot(data["DATE"], data["trailing_values"], c="k")
            legend_handle.append(line_tr_mean[0])
            legend_text.append("Trailing mean: {} months".format(trailing_mean))
        ax.xaxis.set_major_locator(dates.YearLocator())
        ax.tick_params(axis="x", rotation=90)
        ax.grid(True)

        # x-limit
        ax.set_xlim(start_date, end_date)

        # labels
        ax.set_ylabel(plot_kwargs["y_label"])
        ax.set_xlabel("Date")
        ax.set_title(plot_kwargs["title"])
        # add legend
        ax.legend(legend_handle, legend_text, loc="best", fontsize=legend_fontsize)

        fig.tight_layout()
        # Save Figure
        if save_path:
            fig.savefig(save_path)  # , figsize=figsize, dpi=dpi)
        # Show plot if chosen, destroy figure object at the end
        if show_plot:
            plt.show()
        if return_plot:
            return fig
        else:
            plt.close(fig)

    # ------------------------------------------------------------------
    # New plot types (warming stripes + activity heatmap)
    # ------------------------------------------------------------------
    @staticmethod
    def _diverging_cmap():
        """House diverging colormap: cool-blue -> white -> warm-red.

        Uses the exact package palette (#4393c3 / #d6604d) so the new plots
        look identical to the existing figures.
        """
        import matplotlib.colors as mcolors

        def _hex2rgb(h):
            h = h.lstrip("#")
            return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))

        return mcolors.LinearSegmentedColormap.from_list(
            "noaaplotter_diverging",
            [_hex2rgb("#4393c3"), (1.0, 1.0, 1.0), _hex2rgb("#d6604d")],
        )

    def _monthly_anomaly(self, end_date):
        """Monthly anomalies vs the configured climate, for the full record
        up to ``end_date``. Returns a DataFrame with columns
        Year, Month, value (the month's mean), clim, anomaly."""
        dmax = self.dataset.data["DATE"].max()
        if parse_dates(end_date) > dmax:
            end_date = dmax

        data_clim = DS_monthly(
            self.dataset, start=self.climate_start, end=self.climate_end
        )
        data_clim.calculate_monthly_climate()
        clim_by_month = {
            int(m): v for m, v in data_clim.monthly_climate["tmean_doy_mean"].items()
        }
        clim_pr = {
            int(m): v for m, v in data_clim.monthly_climate["prcp_sum"].items()
        }

        data_monthly = DS_monthly(
            self.dataset, start=self.dataset.data["DATE"].min(), end=end_date
        )
        data_monthly.calculate_monthly_statistics()
        monthly = data_monthly.monthly_aggregate.reset_index(drop=False)
        monthly["Year"] = monthly["DATE_YM"].str[:4].astype(int)
        monthly["Month"] = monthly["DATE_YM"].str[5:7].astype(int)
        monthly["clim_t"] = monthly["Month"].map(clim_by_month)
        monthly["clim_p"] = monthly["Month"].map(clim_pr)
        monthly["anom_t"] = monthly["tmean_doy_mean"] - monthly["clim_t"]
        monthly["anom_p"] = monthly["prcp_sum"] - monthly["clim_p"]
        return monthly, end_date

    def plot_warming_stripes(
        self,
        start_date,
        end_date,
        information="Temperature",
        resolution="year",
        title=None,
        figsize=(12, 2.2),
        dpi=300,
        show_plot=False,
        save_path=False,
        return_plot=False,
        engine="matplotlib",
    ):
        """Warming stripes (Ed Hawkins style).

        A single horizontal band, one cell per year (resolution='year') or per
        month (resolution='month'), coloured by the anomaly from the climate
        mean: cool-blue below, warm-red above, white at zero (symmetric scale).
        temperature or precipitation.
        """
        information = information.lower()
        if information not in ("temperature", "precipitation"):
            raise ValueError("information must be 'Temperature' or 'Precipitation'")
        if resolution not in ("year", "month"):
            raise ValueError("resolution must be 'year' or 'month'")

        monthly, dmax = self._monthly_anomaly(end_date)

        if information == "temperature":
            val_col, unit, kind = "anom_t", "C", "Temperature"
        else:
            val_col, unit, kind = "anom_p", "mm", "Precipitation"

        start_ts = parse_dates(start_date)
        monthly["MDATE"] = pd.to_datetime(list(monthly["DATE_YM"]))
        window = monthly[(monthly["MDATE"] >= start_ts) & (monthly["MDATE"] <= dmax)]

        if resolution == "year":
            cells = window.groupby("Year", sort=True)[val_col].mean()
        else:
            monshort = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            window = window.sort_values(["Year", "Month"])
            cells = window[val_col]
            months_labels = [
                "{0}-{1}".format(monshort[int(m) - 1], int(y))
                for y, m in zip(window["Year"].astype(int), window["Month"].astype(int))
            ]

        values = [float(v) if v is not None else None for v in
                  (cells.values.tolist() if resolution == "year" else list(cells))]
        labels = [str(int(y)) for y in cells.index] if resolution == "year" else months_labels

        unit_label = "\N{DEGREE SIGN}C" if unit == "C" else "mm"
        title = title or "{0} warming stripes ({1}) vs climate".format(
            kind, "per year" if resolution == "year" else "per month"
        )

        # ----- plotly engine -----
        if engine == "plotly":
            from noaaplotter.figures import make_stripes_figure

            fig_pl = make_stripes_figure(
                values, labels, title,
                height=(int(figsize[1] * 100) if figsize else 230),
                unit=unit_label,
            )
            if save_path:
                fig_pl.write_html(
                    save_path if str(save_path).endswith(".html")
                    else str(save_path) + ".html"
                )
            return fig_pl

        # ----- matplotlib engine -----
        import numpy as np
        import matplotlib.cm as cm
        import matplotlib.patches as mpatches
        from matplotlib.colors import TwoSlopeNorm

        arr = np.asarray([None if v is None else v for v in values], dtype=float)
        missing = ~np.isfinite(arr)
        finite = arr[~missing]
        half = float(np.max(np.abs(finite))) if finite.size else 1.0
        norm = TwoSlopeNorm(vmin=-half, vcenter=0.0, vmax=half)
        cmap = self._diverging_cmap()

        ncell = len(arr)
        height = figsize[1] if figsize else 2.2
        fig = plt.figure(figsize=(max(ncell * 0.12, 3.0), height), dpi=dpi)
        ax = fig.add_subplot(111)
        for i in range(ncell):
            fc = "lightgrey" if missing[i] else cmap(norm(arr[i]))
            ax.add_patch(
                mpatches.Rectangle((i, 0), 1, 1, facecolor=fc, edgecolor="white", linewidth=0.4)
            )
        ax.set_xlim(-0.5, ncell - 0.5)
        ax.set_ylim(0, 1)
        step = max(1, ncell // 25)
        ticks = list(range(0, ncell, step))
        ax.set_xticks([t + 0.5 for t in ticks])
        ax.set_xticklabels(
            [labels[t] for t in ticks], rotation=90, fontsize=6, ha="left",
            rotation_mode="anchor",
        )
        ax.set_yticks([])
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
        ax.set_title(title, fontsize=11, loc="left", pad=12)

        sm = cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        cbar = fig.colorbar(sm, ax=ax, anchor=(1, 0.5), shrink=0.55, aspect=28, pad=0.06)
        cbar.set_label("Anomaly ({0})".format(unit_label), fontsize=8)

        fig.tight_layout()
        if save_path:
            fig.savefig(save_path)
        if show_plot:
            plt.show()
        if return_plot:
            return fig
        else:
            plt.close(fig)

    def plot_activity_heatmap(
        self,
        start_date,
        end_date,
        information="Temperature",
        title=None,
        figsize=(9, None),
        dpi=300,
        show_plot=False,
        save_path=False,
        return_plot=False,
        engine="matplotlib",
    ):
        """GitHub-activity-style heatmap.

        Months on x, years on y (most recent on top); each cell is a monthly
        anomaly from the climate mean (cool-blue below / warm-red above, white
        at zero). temperature or precipitation.
        """
        information = information.lower()
        if information not in ("temperature", "precipitation"):
            raise ValueError("information must be 'Temperature' or 'Precipitation'")

        monthly, dmax = self._monthly_anomaly(end_date)

        if information == "temperature":
            val_col, unit, kind = "anom_t", "C", "Temperature"
        else:
            val_col, unit, kind = "anom_p", "mm", "Precipitation"

        start_ts = parse_dates(start_date)
        monthly["MDATE"] = pd.to_datetime(list(monthly["DATE_YM"]))
        window = monthly[(monthly["MDATE"] >= start_ts) & (monthly["MDATE"] <= dmax)]

        years = sorted(int(y) for y in window["Year"].unique())
        matrix = []
        for y in years:
            sub = window[(window["Year"] == y)]
            m2v = dict(
                zip(
                    sub["Month"].astype(int),
                    [None if pd.isna(v) else float(v) for v in sub[val_col]],
                )
            )
            matrix.append([m2v.get(m) for m in range(1, 13)])
        # most recent year on top
        matrix = list(reversed(matrix))
        years_top = list(reversed(years))

        unit_label = "\N{DEGREE SIGN}C" if unit == "C" else "mm"
        title = title or "{0} anomaly by month and year (vs climate)".format(kind)

        # ----- plotly engine -----
        if engine == "plotly":
            from noaaplotter.figures import make_heatmap_figure

            fig_pl = make_heatmap_figure(
                matrix, years_top, title,
                height=(int(figsize[1] * 100) if figsize and figsize[1] else None),
                unit=unit_label,
            )
            if save_path:
                fig_pl.write_html(
                    save_path if str(save_path).endswith(".html")
                    else str(save_path) + ".html"
                )
            return fig_pl

        # ----- matplotlib engine -----
        import numpy as np
        import matplotlib.cm as cm
        from matplotlib.colors import TwoSlopeNorm

        n_years = len(matrix)
        arr = np.full((n_years, 12), np.nan, dtype=float)
        for r in range(n_years):
            for c in range(12):
                v = matrix[r][c]
                if v is not None and np.isfinite(v):
                    arr[r, c] = v
        finite = arr[np.isfinite(arr)]
        half = float(np.max(np.abs(finite))) if finite.size else 1.0
        norm = TwoSlopeNorm(vmin=-half, vcenter=0.0, vmax=half)
        cmap = self._diverging_cmap()
        masked = np.ma.array(arr, mask=~np.isfinite(arr))

        months_short = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]
        width = figsize[0] if figsize and figsize[0] else 9
        height = figsize[1] if figsize and figsize[1] else max(1.6, 0.28 * n_years + 1.6)
        fig, ax = plt.subplots(figsize=(width, height), dpi=dpi)
        ax.imshow(
            masked, aspect="auto", origin="upper", cmap=cmap, norm=norm,
            interpolation="nearest",
        )
        ax.set_xlim(-0.5, 11.5)
        ax.set_ylim(n_years - 0.5, -0.5)
        ax.set_xticks(range(12))
        ax.set_xticklabels(months_short)
        ax.set_yticks(range(n_years))
        ax.set_yticklabels([str(y) for y in years_top])
        for tick in ax.get_xticklabels():
            tick.set_fontsize(9)
        for tick in ax.get_yticklabels():
            tick.set_fontsize(8)
        ax.set_title(title, loc="left", fontsize=11, pad=12)
        ax.set_xlabel("Month", fontsize=9)
        # cell grid
        ax.set_xticks(np.arange(-0.5, 12, 1), minor=True)
        ax.set_yticks(np.arange(-0.5, n_years, 1), minor=True)
        ax.grid(which="minor", color="white", linewidth=0.9)
        ax.tick_params(which="minor", bottom=False, left=False)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)

        sm = cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        cbar = fig.colorbar(sm, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label("Anomaly ({0})".format(unit_label), fontsize=8)

        fig.tight_layout()
        if save_path:
            fig.savefig(save_path)
        if show_plot:
            plt.show()
        if return_plot:
            return fig
        else:
            plt.close(fig)
