<!--
  GENERATED. Do not hand-edit the code blocks — change the CLI, then run:

      uv run python scripts/gen_cli_docs.py

  This script captures the *exact* `--help` output from the installed CLI,
  so this page always matches what a user sees.
-->

# CLI reference

`noaaplotter` is a Typer application. Every command also accepts `-h` /
`--help`, and the app supports `--install-completion` / `--show-completion`
for shell integration.

The code blocks below are verbatim from the running CLI.

!!! tip
    Run any command with `--help` for the options of that command.


## `noaaplotter --help`

```console
Usage: noaaplotter [OPTIONS] COMMAND [ARGS]...                                
                                                                               
┌─ Options ───────────────────────────────────────────────────────────────────┐
│ --install-completion          Install completion for the current shell.     │
│ --show-completion             Show completion for the current shell, to     │
│                               copy it or customize the installation.        │
│ --help                        Show this message and exit.                   │
└─────────────────────────────────────────────────────────────────────────────┘
┌─ Commands ──────────────────────────────────────────────────────────────────┐
│ download-data  Download weather data (NOAA station or reanalysis by         │
│                coordinates).                                                │
│ plot-daily     Create a daily temperature/precipitation plot vs. climate.   │
│ plot-monthly   Create a monthly temperature/precipitation bar chart.        │
└─────────────────────────────────────────────────────────────────────────────┘
```

## `noaaplotter download-data`

Download weather data to a Parquet file — NOAA station data **or** coordinate-based (Open-Meteo, CDS/ERA5).

```console
Usage: noaaplotter download-data [OPTIONS]                                    
                                                                               
 Download weather data (NOAA station or reanalysis by coordinates).            
                                                                               
 NOAA station:        noaaplotter download-data -o data/kotzebue.parquet -sid  
 USW00026616 -start 1970-01-01 -end 2021-12-31                                 
 ERA5 (open_meteo):   noaaplotter download-data -o data/potsdam.parquet        
 --source open_meteo -lat 52.4 -lon 13.05 -start 1980-01-01 -end 2021-12-31    
                                                                               
┌─ Options ───────────────────────────────────────────────────────────────────┐
│ *  --output-file    -o           <str>    Output file path (parquet)        │
│                                           [required]                        │
│    --station-id     -sid         <str>    NOAA station id, e.g.             │
│                                           "USW00026616" (Kotzebue)          │
│    --latitude       -lat         <float>  Latitude for coordinate-based     │
│                                           sources (required for             │
│                                           open_meteo/cds)                   │
│    --longitude      -lon         <float>  Longitude for coordinate-based    │
│                                           sources (required for             │
│                                           open_meteo/cds)                   │
│ *  --start-date     -start       <str>    Start date (YYYY-MM-DD)           │
│                                           [required]                        │
│ *  --end-date       -end         <str>    End date (YYYY-MM-DD) [required]  │
│    --token          -t           <str>    NOAA API token (default:          │
│                                           NOAA_API_TOKEN from environment   │
│                                           or .env)                          │
│    --source                      <str>    Data source: noaa, open_meteo, or │
│                                           cds                               │
│                                           [default: noaa]                   │
│    --datatypes                   <str>    Comma-separated datatypes (NOAA   │
│                                           only)                             │
│                                           [default: TMIN,TMAX,PRCP,SNOW]    │
│    --n-jobs         -n_jobs      <int>    Number of parallel processes      │
│                                           (NOAA only)                       │
│                                           [default: 1]                      │
│    --location-name  -loc         <str>    Location name for the output      │
│    --help                                 Show this message and exit.       │
└─────────────────────────────────────────────────────────────────────────────┘
```

## `noaaplotter plot-daily`

Create a daily temperature/precipitation plot vs. climate: static PNG (matplotlib, default) or interactive HTML (Plotly). Records are marked red/blue against the climate baseline.

```console
Usage: noaaplotter plot-daily [OPTIONS]                                       
                                                                               
 Create a daily temperature/precipitation plot vs. climate.                    
                                                                               
 Example: noaaplotter plot-daily -infile data/kotzebue.parquet -start          
 1992-01-01 -end 1992-12-31 -t_range -45 25 -p_range 50 -save_plot             
 figures/kotzebue_1992.png                                                     
                                                                               
┌─ Options ───────────────────────────────────────────────────────────────────┐
│ *  --input-file       -infile          <str>             Input file         │
│                                                          (parquet/csv) with │
│                                                          climate data       │
│                                                          [required]         │
│ *  --start-date       -start           <str>             Start date of plot │
│                                                          (YYYY-MM-DD)       │
│                                                          [required]         │
│ *  --end-date         -end             <str>             End date of plot   │
│                                                          (YYYY-MM-DD)       │
│                                                          [required]         │
│    --location         -loc             <str>             Location name,     │
│                                                          must be in data    │
│                                                          file               │
│    --save-plot        -save_plot       <str>             File path for the  │
│                                                          plot (png, or html │
│                                                          with --engine      │
│                                                          plotly)            │
│    --temperature-ra…  -t_range         <float float>...  Temperature range  │
│                                                          (min, max), e.g.   │
│                                                          -45 25             │
│    --precipitation-…  -p_range         <float>           Maximum            │
│                                                          precipitation      │
│                                                          value in the plot  │
│    --snow-range       -s_range         <float>           Maximum snow       │
│                                                          accumulation value │
│                                                          in the plot        │
│    --snow_acc,--sno…                                     Show snow          │
│                                                          accumulation       │
│                                                          (useful for the    │
│                                                          winter season,     │
│                                                          e.g. July to June) │
│                       -filtersize      <int>             Smooth the climate │
│                                                          temperature series │
│                                                          by n days (default │
│                                                          7)                 │
│                                                          [default: 7]       │
│    --dpi                               <float>           DPI for plot       │
│                                                          output             │
│                                                          [default: 100.0]   │
│    --plot,--show-pl…                                     Open the plot in a │
│                                                          browser/GUI        │
│                       -figsize         <float float>...  Figure size in     │
│                                                          inches, width      │
│                                                          height (e.g. 15 10 │
│                                                          for 2 years)       │
│                       -title           <str>             Plot title         │
│    --engine                            <str>             Rendering engine:  │
│                                                          matplotlib         │
│                                                          (static) or plotly │
│                                                          (interactive HTML) │
│                                                          [default:          │
│                                                          matplotlib]        │
│    --full-series                                         plotly only:       │
│                                                          include the ENTIRE │
│                                                          observed record in │
│                                                          the interactive    │
│                                                          plot; the initial  │
│                                                          view is still      │
│                                                          limited to the     │
│                                                          requested period   │
│                                                          (default: plot     │
│                                                          only the requested │
│                                                          period,            │
│                                                          lightweight)       │
│    --help                                                Show this message  │
│                                                          and exit.          │
└─────────────────────────────────────────────────────────────────────────────┘
```

## `noaaplotter plot-monthly`

Create a monthly temperature/precipitation bar chart. Use `-anomaly` to show anomalies against a 30-day trailing mean.

```console
Usage: noaaplotter plot-monthly [OPTIONS]                                     
                                                                               
 Create a monthly temperature/precipitation bar chart.                         
                                                                               
 Example: noaaplotter plot-monthly -infile data/kotzebue.parquet -start        
 1980-01-01 -end 2021-12-31 -type Temperature -trail 12 -anomaly -save_plot    
 figures/kotzebue_t_anomaly.png                                                
                                                                               
┌─ Options ───────────────────────────────────────────────────────────────────┐
│ *  --input-file        -infile         <str>             Input file         │
│                                                          (parquet/csv) with │
│                                                          climate data       │
│                                                          [required]         │
│ *  --start-date        -start          <str>             Start date of plot │
│                                                          (YYYY-MM-DD)       │
│                                                          [required]         │
│ *  --end-date          -end            <str>             End date of plot   │
│                                                          (YYYY-MM-DD)       │
│                                                          [required]         │
│    --location          -loc            <str>             Location name,     │
│                                                          must be in data    │
│                                                          file               │
│    --save-plot         -save_plot      <str>             File path for the  │
│                                                          plot (png, or html │
│                                                          with --engine      │
│                                                          plotly)            │
│    --information       -type           <str>             Attribute type:    │
│                                                          Temperature or     │
│                                                          Precipitation      │
│                                                          [default:          │
│                                                          Temperature]       │
│    --trailing-mean     -trail          <int>             Trailing/rolling   │
│                                                          mean in months     │
│                                                          (e.g. 12)          │
│                        -anomaly                          Show anomaly from  │
│                                                          climate baseline   │
│    --dpi                               <float>           DPI for plot       │
│                                                          output             │
│                                                          [default: 100.0]   │
│    --plot,--show-plot                                    Open the plot in a │
│                                                          browser/GUI        │
│                        -figsize        <float float>...  Figure size in     │
│                                                          inches, width      │
│                                                          height             │
│    --engine                            <str>             Rendering engine:  │
│                                                          matplotlib         │
│                                                          (static) or plotly │
│                                                          (interactive HTML) │
│                                                          [default:          │
│                                                          matplotlib]        │
│    --help                                                Show this message  │
│                                                          and exit.          │
└─────────────────────────────────────────────────────────────────────────────┘
```
