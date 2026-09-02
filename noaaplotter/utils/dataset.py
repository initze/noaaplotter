#!/usr/bin/python
# -*- coding: utf-8 -*-

########################
# Credits here
# author: Ingmar Nitze, Alfred Wegener Institute for Polar and Marine Research
# contact: ingmar.nitze@awi.de
# version: 2020-12-09

########################
import os

import polars as pl

from .utils import parse_dates


class NOAAPlotterDailySummariesDataset(object):
    """
    Load daily weather observations (NOAA daily summaries format) and
    prepare the columns used by the plotting functions.
    Internal data is a polars DataFrame; expose a pandas view via `data`.
    """

    def __init__(self, input_filepath=None, location=None, remove_feb29=False):
        self.input_switch = None
        self.input_filepath = input_filepath
        self.location = location
        self.noaa_token = None
        self.noaa_location = None
        self.remove_feb29 = remove_feb29
        self.data = None
        self._check_data_loading()
        if self.input_switch == "file":
            self._load_file()
        elif self.input_switch == "noaa_api":
            self._load_noaa()
        self._validate_location()
        self._update_datatypes()
        self._get_datestring()
        self._get_tmean()
        self._remove_feb29()
        self._filter_to_location()

    def print_locations(self):
        """
        Print all locations names
        """
        print(self.data["NAME"].unique())

    def _check_data_loading(self):
        """
        function check if all requirements for loading options are met
        File loading:
        * input_filepath
        """
        if os.path.exists(self.input_filepath):
            self.input_switch = "file"
        elif self.noaa_token and self.noaa_location:
            self.input_switch = "noaa_api"
        else:
            raise ImportError(
                "Please enter either correct file path or noaa station_id and API token"
            )

    def _load_file(self):
        """
        load file into a polars DataFrame
        :return:
        """
        if self.input_filepath.endswith(".parquet"):
            data = pl.read_parquet(self.input_filepath)
        else:
            data = pl.read_csv(self.input_filepath)
        if "__index_level_0__" in data.columns:
            data = data.drop("__index_level_0__")
        # Observed values can be stored as strings (e.g. CSV or legacy parquet
        # exports); coerce to float so numeric ops (TMEAN, stats) work.
        # Casting an already-numeric column to Float64 is a no-op.
        for c in ("PRCP", "SNOW", "TAVG", "TMAX", "TMIN", "SNWD"):
            if c in data.columns:
                data = data.with_columns(
                    pl.col(c).cast(pl.Float64, strict=False)
                )
        self._pl = data

    def _load_noaa(self):
        """
        load data through NOAA API
        """
        pass

    def _validate_location(self):
        """
        raise error and message if location name cannot be found
        :return:
        """
        names = self._pl["NAME"].unique().to_list()
        if not self.location and len(names) > 1:
            raise ValueError(
                "There is more than one location in the dataset. Please choose a location using the -loc option! "
                "Valid Location identifiers: {0} ".format(names)
            )
        if self.location:
            mask = self._pl["NAME"].str.to_lowercase().str.contains(
                self.location.lower(), literal=False
            )
            if mask.sum() == 0:
                raise ValueError(
                    "Location Name is not valid! Valid Location identifiers: {0}".format(names)
                )

    def _update_datatypes(self):
        """
        define 'DATE' as datetime
        :return:
        """
        if self._pl["DATE"].dtype == pl.String:
            self._pl = self._pl.with_columns(pl.col("DATE").str.to_datetime())

    def _get_datestring(self):
        """
        write specific date formats
        :return:
        """
        self._pl = self._pl.with_columns(
            pl.col("DATE").dt.strftime("%m-%d").alias("DATE_MD"),
            pl.col("DATE").dt.strftime("%Y-%m").alias("DATE_YM"),
            pl.col("DATE").dt.strftime("%m").alias("DATE_M"),
        )

    def _get_tmean(self):
        """
        calculate mean daily temperature from min and max
        :return:
        """
        # TODO: check for cases where TMIN and TMAX are empty (e.g. Schonefeld). There TAVG is the main field
        self._pl = self._pl.with_columns(
            pl.mean_horizontal(["TMIN", "TMAX"]).alias("TMEAN")
        )

    def _remove_feb29(self):
        """
        Function to remove February 29 from the data
        :return:
        """
        if self.remove_feb29:
            self._pl = self._pl.filter(pl.col("DATE_MD") != "02-29")

    def _filter_to_location(self):
        """
        Filter dataset to the defined location
        :return:
        """
        if self.location:
            filt = self._pl["NAME"].str.to_lowercase().str.contains(
                self.location.lower(), literal=False
            )
            if filt.sum() > 0:
                self._pl = self._pl.filter(filt)
            else:
                raise ValueError("Location Name is not valid")

        # pandas view for the plotting code
        self.data = self._pl.to_pandas()

    def filter_to_climate(self, climate_start, climate_end):
        """
        Function to create filtered dataset covering the defined climate normal period
        :return:
        """
        df_clim = self.data[
            (self.data["DATE"] >= climate_start) & (self.data["DATE"] <= climate_end)
        ]
        return df_clim


class NOAAPlotterDailyClimateDataset(object):
    # TODO: make main class sub subclasses for daily/monthly
    def __init__(
        self,
        daily_dataset,
        start="1981-01-01",
        end="2010-12-31",
        filtersize=7,
        impute_feb29=True,
    ):
        """
        :param start:
        :param end:
        :param filtersize:
        :param impute_feb29:
        """
        self.start = parse_dates(start)
        self.end = parse_dates(end)
        self.filtersize = filtersize
        self.impute_feb29 = impute_feb29
        self.daily_dataset = daily_dataset
        self.data_daily = None
        self.data = None
        self.date_range_valid = False

        # validate date range
        self._validate_date_range()
        # filter daily to date range
        self._filter_to_climate()
        # calculate daily statistics
        self._calculate_climate_statistics()
        # mean imputation for 29 February
        self._impute_feb29()
        # filter if desired
        self._run_filter()
        # make completeness report

    def _validate_date_range(self):
        if self.daily_dataset.data["DATE"].max() >= self.end:
            if self.daily_dataset.data["DATE"].min() <= self.end:
                self.date_range_valid = True
        else:
            raise ("Dataset is insufficient to calculate climate normals!")

    def _filter_to_climate(self):
        """
        calculate climate dataset
        :return:
        """
        df_clim = self.daily_dataset.data[
            (self.daily_dataset.data["DATE"] >= self.start)
            & (self.daily_dataset.data["DATE"] <= self.end)
        ]
        df_clim = df_clim[(df_clim["DATE_MD"] != "02-29")]
        self.data_daily = df_clim

    def _calculate_climate_statistics(self):
        """
        Function to calculate major statistics (polars).
        :param self.data_daily:
        :type self.data_daily: pandas.DataFrame (converted to polars)
        :return:
        """
        d = pl.from_pandas(self.data_daily)
        aggs = [
            pl.col("TMEAN").mean().alias("tmean_doy_mean"),
            pl.col("TMEAN").std().alias("tmean_doy_std"),
            pl.col("TMEAN").max().alias("tmean_doy_max"),
            pl.col("TMEAN").min().alias("tmean_doy_min"),
            pl.col("TMAX").max().alias("tmax_doy_max"),
            pl.col("TMAX").std().alias("tmax_doy_std"),
            pl.col("TMIN").min().alias("tmin_doy_min"),
            pl.col("TMIN").std().alias("tmin_doy_std"),
        ]
        if "SNOW" in d.columns:
            aggs.append(pl.col("SNOW").mean().alias("snow_doy_mean"))
        df_out = (
            d.group_by("DATE_MD", maintain_order=True)
            .agg(aggs)
            .sort("DATE_MD")
            .to_pandas()
            .set_index("DATE_MD")
        )
        self.data = df_out

    def _impute_feb29(self):
        """
        Function for mean imputation of February 29.
        :return:
        """
        if self.impute_feb29:
            self.data.loc["02-29"] = self.data.loc["02-28":"03-01"].mean(axis=0)
            self.data.sort_index(inplace=True)

    def _run_filter(self):
        """
        Function to run rolling mean filter on climate series to smooth out
        short fluctuations (polars).
        :return:
        """
        if self.filtersize % 2 != 0:
            f = self.filtersize
            # include_index=True: the DATE_MD index is needed for the wraparound
            # frame to be sliced back with it
            d = pl.from_pandas(self.data, include_index=True)
            # wraparound window: pandas rolling(7) with min_periods=7 gives
            # NaN for the first f-1 rows of the extended frame, which are
            # sliced away below. pandas only rolls numeric columns; DATE_MD
            # passes through unchanged.
            extended = pl.concat([d.tail(f), d, d.head(f)], how="vertical")
            rolled = extended.with_columns(
                pl.selectors.numeric().rolling_mean(window_size=f, min_samples=f)
            )
            self.data = (
                rolled.slice(f, len(d)).to_pandas().set_index("DATE_MD")
            )

    def _make_report(self):
        """
        Function to create report on climate data completeness
        :return:
        """
        # input climate series (e.g. 1981-01-01 - 2010-12-31)
        pass


class NOAAPlotterMonthlyClimateDataset(object):
    def __init__(
        self, daily_dataset, start="1981-01-01", end="2010-12-31", impute_feb29=True
    ):
        self.daily_dataset = daily_dataset
        self.monthly_aggregate = None
        self.start = parse_dates(start)
        self.end = parse_dates(end)
        self.impute_feb29 = impute_feb29
        self._validate_date_range()

    def _validate_date_range(self):
        if self.daily_dataset.data["DATE"].max() >= self.end:
            if self.daily_dataset.data["DATE"].min() <= self.end:
                self.date_range_valid = True
        else:
            raise ("Dataset is insufficient to calculate climate normals!")

    def _filter_to_climate(self):
        """
        calculate climate dataset
        :return:
        """
        df_clim = self.daily_dataset.data[
            (self.daily_dataset.data["DATE"] >= self.start)
            & (self.daily_dataset.data["DATE"] <= self.end)
        ]
        df_clim = df_clim[(df_clim["DATE_MD"] != "02-29")]
        self.data_daily = df_clim

    def filter_to_date(self):
        """
        calculate climate dataset
        :return:
        """
        df_clim = self.daily_dataset.data[
            (self.daily_dataset.data["DATE"] >= self.start)
            & (self.daily_dataset.data["DATE"] <= self.end)
        ]
        df_clim = df_clim[(df_clim["DATE_MD"] != "02-29")]
        return df_clim

    def _impute_feb29(self):
        """
        Function for mean imputation of February 29.
        :return:
        """
        pass

    def calculate_monthly_statistics(self):
        """
        Function to calculate monthly statistics (polars).
        :return:
        """
        d = pl.from_pandas(self.filter_to_date())
        aggs = [
            pl.col("TMEAN").mean().alias("tmean_doy_mean"),
            pl.col("TMEAN").std().alias("tmean_doy_std"),
            pl.col("TMAX").max().alias("tmax_doy_max"),
            pl.col("TMAX").std().alias("tmax_doy_std"),
            pl.col("TMIN").min().alias("tmin_doy_min"),
            pl.col("TMIN").std().alias("tmin_doy_std"),
        ]
        if "SNOW" in d.columns:
            aggs.append(pl.col("SNOW").mean().alias("snow_doy_mean"))
        aggs.append(pl.col("PRCP").sum().alias("prcp_sum"))
        df_out = (
            d.group_by("DATE_YM", maintain_order=True)
            .agg(aggs)
            .sort("DATE_YM")
            .to_pandas()
            .set_index("DATE_YM")
        )
        self.monthly_aggregate = df_out

    def calculate_monthly_climate(self):
        """
        Function to calculate monthly climate statistics (polars).
        :return:
        """
        d = pl.from_pandas(self.filter_to_date())
        d = d.with_columns(
            pl.col("DATE").dt.month().alias("Month"),
            pl.col("DATE").dt.year().alias("Year"),
        )
        # unique year count for the (bug-compatible) precipitation scaling
        n_years = d["Year"].n_unique()
        aggs = [
            pl.col("TMEAN").mean().alias("tmean_doy_mean"),
            pl.col("TMEAN").std().alias("tmean_doy_std"),
            pl.col("TMAX").max().alias("tmax_doy_max"),
            pl.col("TMAX").std().alias("tmax_doy_std"),
            pl.col("TMIN").min().alias("tmin_doy_min"),
            pl.col("TMIN").std().alias("tmin_doy_std"),
        ]
        if "SNOW" in d.columns:
            aggs.append(pl.col("SNOW").mean().alias("snow_doy_mean"))
        aggs.append((pl.col("PRCP").mean() * 30).alias("prcp_sum"))
        df_out = (
            d.group_by("Month", maintain_order=True)
            .agg(aggs)
            .sort("Month")
            .to_pandas()
            .set_index("Month")
        )
        self.monthly_climate = df_out

    def _make_report(self):
        """
        Function to create report on climate data completeness
        :return:
        """
        # input climate series (e.g. 1981-01-01 - 2010-12-31)

        pass
