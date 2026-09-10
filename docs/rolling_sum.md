# Rolling Sum Precipitation Feature Implementation

## What was implemented

1. **7-day Rolling Sum of Precipitation** for daily plots in noaaplotter
   - Added a new blue line (rgba(30,144,255,0.7), width=2) to daily plots showing 7-day accumulated precipitation
   - Uses pandas rolling window with center=True for proper alignment
   - Works for both interactive (plotly) and static plots
   - Includes proper hover information showing the rolling sum value

2. **Implementation Details**
   - Modified `noaaplotter/figures/plotly_daily.py`
   - Added rolling sum calculation using: `pd.Series(prcp).rolling(window=7, min_periods=1, center=True).sum()`
   - Added new trace to the precipitation subplot (row 2, col 1)
   - Maintained all existing functionality while adding the new feature

## Files Modified

1. `noaaplotter/figures/plotly_daily.py` - Main implementation
   - Added rolling sum calculation and plotting logic
   - Integrated into existing precipitation subplot

2. `examples/rolling_sum_verification.py` - Verification script
   - Tests that rolling sum functionality works correctly

## How it works

The new feature:
- Adds a blue line to the precipitation panel (bottom subplot)
- Shows 7-day accumulated precipitation over time
- Helps identify precipitation patterns that might not be visible in daily bars
- Maintains all existing plot functionality
- Works for both interactive (plotly) and static plots

## Examples Created

- `examples/rolling_sum_verification.py` - Verification that the rolling sum works correctly
- Preview functionality for Kotzebue station and reanalysis coordinates (implementation in progress)

## Usage

When users view daily plots:
- Regular precipitation bars show daily amounts
- Blue line shows 7-day rolling sum of precipitation
- Hover over the blue line to see the rolling sum value
- Works for both interactive (plotly) and static plots

The feature is now available and integrated into the main codebase.