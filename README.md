# noaaplotter
A python package to create fancy plots with NOAA weather data.

## Install
#### Recommended conda install

I recommend to use a fresh conda environment
`conda create -n noaaplotter python pip`

activate conda environment
`conda activate noaaplotter`

pip install noaaplotter and dependencies
`pip install git+https://github.com/initze/noaaplotter.git`

#### Requirements
  - matplotlib
  - numpy
  - pandas
  - python
  - requests
  - joblib
  - tqdm
  - geemap

## Command Line Interface (CLI)
The package now provides a unified command line interface:

### Download Data
#### NOAA Stations
Download daily summaries (temperature + precipitation) from Kotzebue (or other station) from 1970-01-01 until 2021-12-31
* NOAA API Token is required: https://www.ncdc.noaa.gov/cdo-web/token

`noaaplotter download-data -o ./data/kotzebue.parquet -sid USW00026616 -start 1970-01-01 -end 2021-12-31 -t <NOAA API Token>`

#### ERA5 Reanalysis (Coordinate-based)
Download daily summaries (temperature + precipitation) from Potsdam (13.05°E, 52.4°N) from 1980-01-01 until 2021-12-31
* No API token required for open_meteo data

`noaaplotter download-data -o ./data/potsdam_ERA5.parquet -start 1980-01-01 -end 2021-12-31 -lat 52.4 -lon 13.05 --source open_meteo`

### Daily Plots
#### Entire year 1 January until 31 December (e.g. 1992)

`noaaplotter plot-daily -infile data/kotzebue.parquet -start 1992-01-01 -end 1992-12-31 -t-range -45 25 -p-range 50`

![alt text](https://user-images.githubusercontent.com/4864803/132648353-d1792234-dc68-4baf-a608-5aa5fe6899a8.png "Mean monthly temperatures with 12 months trailing mean")

### Monthly Plots
#### Absolute values

Temperature:
`noaaplotter plot-monthly -infile data/kotzebue.parquet -start 1980-01-01 -end 2021-08-31 -type Temperature -trail 12 -save-plot figures/kotzebue_monthly_temperature_anomaly.png`

![Kotzebue_monthly_t_abs](https://user-images.githubusercontent.com/4864803/133925329-540933c1-b30a-4d31-a66f-0ba624223abf.png)

Precipitation:
`noaaplotter plot-monthly -infile data/kotzebue.parquet -start 1980-01-01 -end 2021-08-31 -type Precipitation -trail 12 -save-plot figures/kotzebue_monthly_precipitation.png -anomaly`

![Kotzebue_monthly_p_abs](https://user-images.githubusercontent.com/4864803/133925351-5d7513df-2794-472a-b00d-780538f68ce6.png)

#### Anomalies/Departures from Climate (1981-2010)

Temperature:
`noaaplotter plot-monthly -infile data/kotzebue.parquet -start 1980-01-01 -end 2021-08-31 -type Temperature -trail 12 -save-plot figures/kotzebue_monthly_temperature_anomaly.png -anomaly`

![Mean monthly temperatures with 12 months trailing mean](https://user-images.githubusercontent.com/4864803/133923928-9ca78105-3718-48d9-80c5-efaf0bfa3217.png)

Precipitation:
`noaaplotter plot-monthly -infile data/kotzebue.parquet -start 1980-01-01 -end 2021-08-31 -type Precipitation -trail 12 -save-plot figures/kotzebue_monthly_precipitation_anomaly.png -anomaly`

![Mean monthly temperatures with 12 months trailing mean](https://user-images.githubusercontent.com/4864803/133923987-faabba54-e2d7-4340-be05-078bce0648cf.png)

## Examples
### Download data
#### Option 1 NOAA Daily Summaries: Download via CLI
Download daily summaries (temperature + precipitation) from Kotzebue (or other station) from 1970-01-01 until 2021-12-31
* NOAA API Token is required: https://www.ncdc.noaa.gov/cdo-web/token

`noaaplotter download-data -o ./data/kotzebue.parquet -sid USW00026616 -start 1970-01-01 -end 2021-12-31 -t <NOAA API Token>`

#### Option 2 NOAA Daily Summaries: Download via browser
CSV files of "daily summaries"
("https://www.ncdc.noaa.gov/cdo-web/search")
* Values: metric
* File types: csv

#### Option 3 ERA5 Daily: Download via CLI
Download daily summaries (temperature + precipitation) from Potsdam (13.05°E, 52.4°N) from 1980-01-01 until 2021-12-31
* Google Earthengine account is required
* Caution: full dataset may take a few minutes

`noaaplotter download-data -o ./data/potsdam_ERA5.parquet -start 1980-01-01 -end 2021-12-31 -lat 52.4 -lon 13.05 --source open_meteo`

### Daily Mean Temperature and Precipitation values vs. Climate
#### Entire year 1 January until 31 December (e.g. 1992)

`noaaplotter plot-daily -infile data/kotzebue.parquet -start 1992-01-01 -end 1992-12-31 -t-range -45 25 -p-range 50 -plot`

![alt text](https://user-images.githubusercontent.com/4864803/132648353-d1792234-dc68-4baf-a608-5aa5fe6899a8.png "Mean monthly temperatures with 12 months trailing mean")

## Advanced Usage
### Get help for any command
`noaaplotter download-data --help`
`noaaplotter plot-daily --help`
`noaaplotter plot-monthly --help`

### Interactive Plots (plotly)
Use the `--engine plotly` flag to create interactive HTML plots:
`noaaplotter plot-daily -infile data/kotzebue.parquet -start 2020-01-01 -end 2024-06-30 --engine plotly -save-plot figures/kotzebue_interactive.html`