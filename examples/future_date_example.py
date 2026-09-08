#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example Script to demonstrate the fix for future date handling in interactive plots.
This shows that plots now work correctly with future end dates without crashing.
"""

import os
import tempfile
import pandas as pd
import polars as pl
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

def create_synthetic_station_data(start_date="2000-01-01", end_date="2024-06-30", 
                                 station_id="ANCHORAGE", name="ANCHORAGE (synthetic)"):
    """Create synthetic weather data for a station with no gaps"""
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Create realistic weather data
    doy = dates.dayofyear.to_numpy()
    season = np.sin(2 * np.pi * (doy - 105) / 365.25)  # Seasonal pattern
    
    # Temperature data with realistic variations
    tavg = 5 + 12 * season + np.random.RandomState(0).normal(0, 1.5, len(dates))
    
    # Precipitation and snow data
    prcp = np.abs(np.random.RandomState(3).normal(0, 2, len(dates))).round(1)
    snow = np.clip(-season, 0, 1) * np.abs(np.random.RandomState(4).normal(0, 1, len(dates))).round(2)
    
    # Create DataFrame
    data = {
        'STATION': [station_id] * len(dates),
        'NAME': [name] * len(dates),
        'DATE': dates.strftime('%Y-%m-%d'),
        'TAVG': tavg.round(1),
        'TMAX': (tavg + 4 + np.random.RandomState(1).normal(0, 1, len(dates))).round(1),
        'TMIN': (tavg - 4 + np.random.RandomState(2).normal(0, 1, len(dates))).round(1),
        'PRCP': prcp,
        'SNOW': snow
    }
    
    df = pd.DataFrame(data)
    df = df.astype({
        'STATION': 'str',
        'NAME': 'str',
        'DATE': 'str',
        'TAVG': 'float64',
        'TMAX': 'float64',
        'TMIN': 'float64',
        'PRCP': 'float64',
        'SNOW': 'float64'
    })
    
    return df

def main():
    # Create synthetic data
    print("Creating synthetic weather data...")
    df = create_synthetic_station_data("2000-01-01", "2024-06-30")
    
    # Convert to polars and save to temporary file
    df_pl = pl.from_pandas(df)
    
    # Create temporary file
    temp_dir = tempfile.mkdtemp(prefix='noaa_example_')
    data_file = os.path.join(temp_dir, 'anchorage_synthetic.parquet')
    df_pl.write_parquet(data_file)
    
    print(f"Data saved to: {data_file}")
    print(f"Data rows: {df_pl.height}")
    print(f"Data columns: {df_pl.columns}")
    
    # Show date range
    dates = df_pl['DATE'].to_list()
    print(f"Date range: {min(dates)} to {max(dates)}")
    
    # Import noaaplotter
    try:
        from noaaplotter.noaaplotter import NOAAPlotter
        
        # Create NOAAPlotter instance
        n = NOAAPlotter(data_file, location="ANCHORAGE (synthetic)", 
                       climate_filtersize=7, climate_start=datetime(1981,1,1), 
                       climate_end=datetime(2010,12,31))
        
        # Test the fix for future date handling
        print("\n=== Testing Future Date Handling Fix ===")
        print("Plotting with future end date (2025-12-31)...")
        
        # This should work now with the fix
        figure = n.plot_weather_series(
            start_date="2023-01-01", 
            end_date="2025-12-31",  # Future date - this used to crash
            show_snow_accumulation=True, 
            plot_extrema=True, 
            show_plot=False,
            title="ANCHORAGE (synthetic) - Window 2023-01-01 to 2025-12-31",
            return_plot=True,
            engine='matplotlib'
        )
        
        # Save to examples directory
        output_path = os.path.join('examples', 'future_date_example.png')
        figure.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"✓ Future date plot saved to: {output_path}")
        
        # Test with interactive plot (plotly)
        print("\n=== Testing Interactive Plot (Plotly) ===")
        figure_plotly = n.plot_weather_series(
            start_date="2023-01-01", 
            end_date="2025-12-31", 
            show_snow_accumulation=True, 
            plot_extrema=True, 
            show_plot=False,
            title="ANCHORAGE (synthetic) - Interactive Future Date",
            return_plot=True,
            engine='plotly'
        )
        
        # Save interactive plot
        output_path_plotly = os.path.join('examples', 'future_date_example_plotly.html')
        figure_plotly.write_html(output_path_plotly, include_plotlyjs='cdn')
        print(f"✓ Interactive plot saved to: {output_path_plotly}")
        
        print("\n=== All Examples Created Successfully ===")
        print("The fix allows future end dates without crashing.")
        print("The observed data stops at the last available date (2024-06-30),")
        print("while the climatology lines and x-axis extend to the future date (2025-12-31).")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()