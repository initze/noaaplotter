# noaaplotter
A python package to create fancy plots with NOAA weather data.

## Input Data

CSV files of "daily summaries"
("https://www.ncdc.noaa.gov/cdo-web/search")
* Values: metric
* File types: csv

## Requirements
pandas
matplotlib
numpy

## Examples

### Download daily summaries (temperature + precipitation) from Kotzebue (or other station) from 1970-01-01 until 2021-12-31 

`python download_data.py -o ./data/kotzebue.csv -sid GHCND:USW00026616 -start 1970-01-01 -end 2021-12-31 -t <NOAA API Token>`
  
### Daily Temperature and Precipitation values vs. Climate
#### Entire year 1 January until 31 December

`python plot_daily.py -infile ./data/kotzebue.csv -loc Kotzebue -start 1992-01-01 -end 1992-12-31 -t_range -45 25 -p_range 50 -plot`


![alt text](https://user-images.githubusercontent.com/4864803/132648353-d1792234-dc68-4baf-a608-5aa5fe6899a8.png "Mean monthly temperatures with 12 months trailing mean")


#### Winter configuration with cumulative snowfall: July 1 until June 30

`python plot_daily.py -infile ./data/kotzebue.csv -loc Kotzebue -start 2017-07-01 -end 2018-06-30 -t_range -45 25 -p_range 50 -snow_acc -s_range 300 -plot`

![alt text](https://raw.githubusercontent.com/initze/noaaplotter/master/figures/daily_series_Kotzebue_2017-2018_winter.png "Mean monthly temperatures with 12 months trailing mean")


### Monthly aggregates
#### Absolute values

Temperature:

`python plot_monthly.py -infile ./data/kotzebue.csv -loc Kotzebue -start 1990-01-01 -end 2019-12-31 -type Temperature -trail 12 -plot`

![alt text](https://raw.githubusercontent.com/initze/noaaplotter/master/figures/monthly_series_temperature_12mthsTrMn_Kotzebue.png "Mean monthly temperatures with 12 months trailing mean")

Precipitation:


`python plot_monthly.py -infile ./data/kotzebue.csv -loc Kotzebue -start 1990-01-01 -end 2019-12-31 -type Precipitation -trail 12 -plot`

![alt text](https://raw.githubusercontent.com/initze/noaaplotter/master/figures/monthly_series_precipitation_12mthsTrMn_Kotzebue.png "Mean monthly temperatures with 12 months trailing mean")

#### Anomalies from Climate (1981-2010)

Temperature:

`python plot_monthly.py -infile ./data/kotzebue.csv -loc Kotzebue -start 1990-01-01 -end 2019-12-31 -type Temperature -trail 12 -plot -anomaly`

![alt text](https://raw.githubusercontent.com/initze/noaaplotter/master/figures/monthly_series_temperature_12mthsTrMn_Kotzebue_anomaly.png "Mean monthly temperatures with 12 months trailing mean")

Precipitation:


`python plot_monthly.py -infile ./data/kotzebue.csv -loc Kotzebue -start 1990-01-01 -end 2019-12-31 -type Precipitation -trail 12 -plot -anomaly`

![alt text](https://raw.githubusercontent.com/initze/noaaplotter/master/figures/monthly_series_precipitation_12mthsTrMn_Kotzebue_anomaly.png "Mean monthly temperatures with 12 months trailing mean")
