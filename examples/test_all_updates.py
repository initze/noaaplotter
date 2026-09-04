#!/usr/bin/env python
"""
noaaplotter update — try-it examples
====================================
Runs each new feature and writes the results under examples/out/:

  1. NOAA station data        — needs NOAA_API_TOKEN in .env (skipped if absent)
  2. Open-Meteo reanalysis    — by coordinates, NO key needed
  3. CDS/ERA5 reanalysis      — needs CDS_API_TOKEN in .env (skipped if absent)
  4. For every dataset: daily + monthly figures, BOTH engines
     (matplotlib PNG + interactive plotly HTML — open the .html in a browser)

Run it:
    python examples/test_all_updates.py            # reuse cached data where present
    python examples/test_all_updates.py --live     # also fetch open_meteo/cds fresh

Requires:
    pip install -e .
    pip install cdsapi xarray netCDF4   # only for the CDS source
"""
import argparse
import datetime
import os
import sys
import warnings

warnings.filterwarnings("ignore")
import matplotlib

matplotlib.use("Agg")  # static rendering, no display needed

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPT_DIR)
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(SCRIPT_DIR, "out")
os.makedirs(OUT, exist_ok=True)

KOTZEBUE_LAT, KOTZEBUE_LON = 70.02, -142.56
KOTZEBUE_STATION_ID = "USC00022706"  # KOTZEBUE, AK — adjust to your station


def hr(title):
    print("\n" + "=" * 62)
    print(" " + title)
    print("=" * 62)


def token_set(name):
    try:
        from dotenv import load_dotenv

        load_dotenv(os.path.join(ROOT, ".env"))
    except ImportError:
        pass
    return bool(os.environ.get(name))


def load(path, location):
    """Build a NOAAPlotter from a parquet file (classic 1981-2010 normals)."""
    from noaaplotter.noaaplotter import NOAAPlotter

    return NOAAPlotter(
        path,
        location=location,
        climate_start=datetime.datetime(1981, 1, 1),
        climate_end=datetime.datetime(2010, 12, 31),
        climate_filtersize=7,
    )


def plot_all(n, label):
    """Render daily + monthly, both engines, for one NOAAPlotter instance."""
    # daily weather series -------------------------------------------------
    n.plot_weather_series(
        "2009-01-01", "2010-12-31",
        show_plot=False,
        show_snow_accumulation=False,
        plot_extrema=True,
        save_path=os.path.join(OUT, f"daily_{label}.png"),
        figsize=(10, 6),
        dpi=120,
    )
    fig = n.plot_weather_series(
        "2009-01-01", "2010-12-31",
        engine="plotly",
        show_snow_accumulation=False,
        title=f"{label} — daily weather series",
    )
    html_path = os.path.join(OUT, f"daily_{label}.html")
    fig.write_html(html_path)
    print(f"  daily   matplotlib -> {os.path.relpath(os.path.join(OUT, f'daily_{label}.png'), ROOT)}")
    print(f"  daily   plotly     -> {os.path.relpath(html_path, ROOT)}")

    # monthly temperature --------------------------------------------------
    n.plot_monthly_barchart(
        "2008-01-01", "2010-12-31",
        information="Temperature", anomaly=False,
        save_path=os.path.join(OUT, f"monthly_t_{label}.png"),
        figsize=(10, 4), dpi=120,
    )
    fig = n.plot_monthly_barchart(
        "2008-01-01", "2010-12-31",
        information="Temperature", anomaly=False,
        engine="plotly",
    )
    html_path = os.path.join(OUT, f"monthly_t_{label}.html")
    fig.write_html(html_path)
    print(f"  monthly matplotlib -> {os.path.relpath(os.path.join(OUT, f'monthly_t_{label}.png'), ROOT)}")
    print(f"  monthly plotly     -> {os.path.relpath(html_path, ROOT)}")


def namer_from(path):
    """First distinct NAME value in the file (used as the location filter)."""
    import polars as pl

    try:
        names = pl.scan_parquet(path).select("NAME").unique().collect().get_column("NAME").to_list()
        names = [x for x in names if x is not None]
        if names:
            return names[0]
    except Exception:
        pass
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--live", action="store_true",
        help="fetch open_meteo / cds data even if not cached (open_meteo ~15s, cds ~1-2min)",
    )
    parser.add_argument("--station", default=KOTZEBUE_STATION_ID,
                        help=f"NOAA station id (default {KOTZEBUE_STATION_ID})")
    parser.add_argument("--lat", type=float, default=KOTZEBUE_LAT)
    parser.add_argument("--lon", type=float, default=KOTZEBUE_LON)
    args = parser.parse_args()

    ok, failed = [], []

    # ------------------------------------------------------------------
    # 1) NOAA station data (if token available)
    # ------------------------------------------------------------------
    hr("1) NOAA station data")
    if token_set("NOAA_API_TOKEN"):
        import glob

        cands = glob.glob(os.path.join(DATA, f"NOAA_{args.station}*.parquet"))
        if cands:
            data_path = cands[0]
            print(f"  reusing {os.path.relpath(data_path, ROOT)}")
        else:
            data_path = None
        try:
            if data_path is None:
                from noaaplotter.utils.config import get_noaa_token
                from noaaplotter.utils.download_utils import download_from_noaa

                print("  downloading NOAA GHCND 1981-2010 ...")
                data_path = os.path.join(DATA, f"NOAA_{args.station}.parquet")
                os.makedirs(DATA, exist_ok=True)
                download_from_noaa(
                    output_file=data_path,
                    start_date="1981-01-01",
                    end_date="2010-12-31",
                    datatypes=["TMIN", "TMAX", "PRCP", "SNOW"],
                    loc_name="",
                    station_id=args.station,
                    noaa_api_token=get_noaa_token(),
                )
            n = load(data_path, namer_from(data_path))
            plot_all(n, "noaa")
            ok.append("noaa")
        except Exception as e:  # noqa: BLE001 — keep going for the other sources
            failed.append(("noaa", e))
            print(f"  NOAA failed: {e}")
    else:
        print("  skipped — no NOAA_API_TOKEN in .env (see .env.example). "
              "Add it and re-run.")

    # ------------------------------------------------------------------
    # 2) Open-Meteo reanalysis (no key)
    # ------------------------------------------------------------------
    hr("2) Open-Meteo reanalysis (coordinates, no key)")
    import glob

    cands = sorted(glob.glob(os.path.join(DATA, "open_meteo*.parquet")))
    # pick the file that actually spans the 1981-2010 reference period
    data_path = None
    for c in cands:
        try:
            import polars as _pl

            d = _pl.read_parquet(c)
            dmin = str(d["DATE"].min())
            dmax = str(d["DATE"].max())
            if dmin <= "1981-01-01" and dmax >= "2010-12-31":
                data_path = c
                break
        except Exception:
            continue
    if data_path:
        print(f"  reusing {os.path.relpath(data_path, ROOT)}")
    elif args.live:
        from noaaplotter.sources import fetch_open_meteo
        from noaaplotter.sources.open_meteo import save_to_parquet

        print(f"  fetching Open-Meteo ERA5 {args.lat},{args.lon} (1981-2010, ~15s) ...")
        df = fetch_open_meteo(
            args.lat, args.lon, "1981-01-01", "2010-12-31", name="Kotzebue ERA5"
        )
        os.makedirs(DATA, exist_ok=True)
        data_path = os.path.join(DATA, f"open_meteo_{args.lat}_{args.lon}.parquet")
        save_to_parquet(df, data_path)
        print(f"  saved {df.shape[0]} rows -> {os.path.relpath(data_path, ROOT)}")
    else:
        data_path = None
        print("  no cached Open-Meteo data — re-run with --live to fetch (no key needed).")
    if data_path:
        try:
            n = load(data_path, namer_from(data_path))
            plot_all(n, "open_meteo")
            ok.append("open_meteo")
        except Exception as e:  # noqa: BLE001
            failed.append(("open_meteo", e))
            print(f"  open_meteo failed: {e}")

    # ------------------------------------------------------------------
    # 3) CDS / Copernicus ERA5 (needs credentials)
    # ------------------------------------------------------------------
    hr("3) CDS / Copernicus ERA5 (credentials required)")
    if token_set("CDS_API_TOKEN") or token_set("CDS_API_KEY"):
        cands = sorted(glob.glob(os.path.join(DATA, "cds*.parquet")))
        if cands:
            data_path = cands[-1]
            print(f"  reusing {os.path.relpath(data_path, ROOT)}")
        elif args.live:
            from noaaplotter.sources import fetch_cds_era5
            from noaaplotter.sources.cds import save_to_parquet

            # CDS is rate-limited (~2 s per file) — keep the window modest
            print("  fetching CDS ERA5 2008-2010 (first fetch of a window "
                  "takes a few minutes) ...")
            df = fetch_cds_era5(args.lat, args.lon, "2008-01-01", "2010-12-31")
            os.makedirs(DATA, exist_ok=True)
            data_path = os.path.join(DATA, f"cds_{args.lat}_{args.lon}.parquet")
            save_to_parquet(df, data_path)
            print(f"  saved {df.shape[0]} rows -> {os.path.relpath(data_path, ROOT)}")
        else:
            data_path = None
            print("  no cached CDS data — re-run with --live to fetch.")
        if data_path:
            try:
                n = load(data_path, "ERA5")
                plot_all(n, "cds_era5")
                ok.append("cds")
            except Exception as e:  # noqa: BLE001
                failed.append(("cds", e))
                print(f"  cds failed: {e}")
    else:
        print("  skipped. To test CDS, set CDS_API_TOKEN in .env (see .env.example)")
        print("  token: https://cds.climate.copernicus.eu -> login -> My Data -> API")

    # ------------------------------------------------------------------
    # 4) CLI equivalents
    # ------------------------------------------------------------------
    hr("4) Same things as command line (alternative)")
    print(f"""
    # fetch Open-Meteo reanalysis for {args.lat},{args.lon}:
    python -m noaaplotter.scripts.download_data --source open_meteo \\
        -lat {args.lat} -lon {args.lon} -start 1981-01-01 -end 2010-12-31 \\
        -o data/open_meteo_kotzebue.parquet

    # fetch CDS/ERA5 for {args.lat},{args.lon} (needs CDS_API_TOKEN in .env):
    python -m noaaplotter.scripts.download_data --source cds \\
        -lat {args.lat} -lon {args.lon} -start 1981-01-01 -end 2010-12-31 \\
        -o data/cds_kotzebue.parquet
""")

    # ------------------------------------------------------------------
    hr("SUMMARY")
    print(f"  plotted:        {', '.join(ok) or '(nothing)'}")
    print(f"  failures:       {', '.join(name + ': ' + str(e) for name, e in failed) or '(none)'}")
    print(f"  outputs in:     {OUT}")
    print("  open the .html files in a browser, or use them in Streamlit:")
    print("      fig = n.plot_weather_series(..., engine='plotly')")
    print("      st.plotly_chart(fig)")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
