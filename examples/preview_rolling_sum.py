#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to create preview plots for Kotzebue station and reanalysis coordinates.
This demonstrates the new 7-day rolling sum precipitation feature.
"""

import os
import tempfile
import pandas as pd
import polars as pl
import numpy as np
from datetime import datetime

def create_sample_data(station_id="KOTZEBUE", name="KOTZEBUE"):
    """Create sample weather data for demonstration"""
    dates = pd.date_range(start="2020-01-01", end="2024-06-30", freq='D')
    
    # Create realistic weather data
    doy = dates.dayofyear.to_numpy()
    season = np.sin(2 * np.pi * (doy - 105) / 365.25)
    
    # Temperature data
    tavg = 5 + 12 * season + np.random.RandomState(0).normal(0, 1.5, len(dates))
    
    # Precipitation data - some variability to make rolling sum meaningful
    prcp = np.abs(np.random.RandomState(3).normal(0, 2, len(dates))).round(1)
    # Add some bursts to make precipitation patterns more interesting
    prcp = np.maximum(prcp, np.random.RandomState(4).poisson(1, len(dates)) * 5)
    
    # Snow data
    snow = np.clip(-season, 0, 1) * np.abs(np.random.RandomState(5).normal(0, 1, len(dates))).round(2)
    
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
    print("=== Creating Preview Plots for New Rolling Sum Feature ===")
    
    # Create sample data for both scenarios
    print("1. Creating Kotzebue station data...")
    kotzebue_df = create_sample_data("KOTZEBUE", "KOTZEBUE")
    
    # Create temporary files
    temp_dir = tempfile.mkdtemp(prefix='noaa_preview_')
    
    # Save Kotzebue data
    kotzebue_file = os.path.join(temp_dir, 'kotzebue_preview.parquet')
    kotzebue_pl = pl.from_pandas(kotzebue_df)
    kotzebue_pl.write_parquet(kotzebue_file)
    
    print(f"✓ Kotzebue data saved to: {kotzebue_file}")
    
    # Create reanalysis data (simulated)
    print("2. Creating reanalysis coordinate data (lat=52, lon=12)...")
    # Create a similar structure but for reanalysis
    reanalysis_df = create_sample_data("REANALYSIS_52_12", "Reanalysis (52°N, 12°E)")
    
    reanalysis_file = os.path.join(temp_dir, 'reanalysis_preview.parquet')
    reanalysis_pl = pl.from_pandas(reanalysis_df)
    reanalysis_pl.write_parquet(reanalysis_file)
    
    print(f"✓ Reanalysis data saved to: {reanalysis_file}")
    
    # Now create plots using noaaplotter
    try:
        from noaaplotter.noaaplotter import NOAAPlotter
        
        # Test Kotzebue plot
        print("\n3. Creating Kotzebue plot with rolling sum...")
        n_kotzebue = NOAAPlotter(kotzebue_file, location="KOTZEBUE", 
                                climate_filtersize=7, climate_start=datetime(1981,1,1), 
                                climate_end=datetime(2010,12,31))
        
        # Generate plot with 7-day rolling sum
        figure_kotzebue = n_kotzebue.plot_weather_series(
            start_date="2023-01-01", 
            end_date="2024-06-30", 
            show_snow_accumulation=True, 
            plot_extrema=True, 
            show_plot=False,
            title="KOTZEBUE - Daily Weather Series with 7-Day Rolling Sum",
            return_plot=True,
            engine='plotly'
        )
        
        # Save the Kotzebue plot
        kotzebue_output = os.path.join('examples', 'kotzebue_with_rolling_sum.html')
        figure_kotzebue.write_html(kotzebue_output, include_plotlyjs='cdn')
        print(f"✓ Kotzebue plot saved to: {kotzebue_output}")
        
        # Test Reanalysis plot  
        print("\n4. Creating Reanalysis plot with rolling sum...")
        n_reanalysis = NOAAPlotter(reanalysis_file, location="Reanalysis (52°N, 12°E)", 
                                  climate_filtersize=7, climate_start=datetime(1981,1,1), 
                                  climate_end=datetime(2010,12,31))
        
        figure_reanalysis = n_reanalysis.plot_weather_series(
            start_date="2023-01-01", 
            end_date="2024-06-30", 
            show_snow_accumulation=True, 
            plot_extrema=True, 
            show_plot=False,
            title="Reanalysis (52°N, 12°E) - Daily Weather Series with 7-Day Rolling Sum",
            return_plot=True,
            engine='plotly'
        )
        
        # Save the Reanalysis plot
        reanalysis_output = os.path.join('examples', 'reanalysis_with_rolling_sum.html')
        figure_reanalysis.write_html(reanalysis_output, include_plotlyjs='cdn')
        print(f"✓ Reanalysis plot saved to: {reanalysis_output}")
        
        # Summary
        print("\n=== Preview Plots Created Successfully ===")
        print("✓ Kotzebue station with 7-day rolling sum precipitation")
        print("✓ Reanalysis coordinates with 7-day rolling sum precipitation")
        print("✓ Both plots include the new rolling sum line (blue)")
        print("✓ Features work in both interactive (plotly) mode")
        print("\nFiles created:")
        print(f"- {kotzebue_output}")
        print(f"- {reanalysis_output}")
        print("\nThe rolling sum line shows accumulated precipitation over 7-day periods,")
        print("which helps identify precipitation patterns that might not be visible in")
        print("daily precipitation bars alone.")
        
    except Exception as e:
        print(f"Error during plot creation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()