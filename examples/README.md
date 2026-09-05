# noaaplotter Examples

This directory contains examples demonstrating the fixes implemented in noaaplotter.

## Files

- `demo_data.parquet`: Sample weather data for testing
- `cache_fix_explanation.txt`: Details on cache corruption fix
- `fixes_summary.txt`: Summary of all fixes implemented

## Fixes Implemented

1. **Cache Corruption Fix**: Fixed incremental downloads that were corrupting cache files
2. **Widget Auto-run Fix**: Made processing dependent only on explicit Start Process button  
3. **Future Date Handling**: Fixed interactive plots with future end dates

These fixes resolve issues where:
- Fairbanks/Kotzebue plots showed "No Data" fields
- Widget changes would trigger unwanted re-processing
- Future date ranges in interactive plots would crash
