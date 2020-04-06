# noaaplotter
python module to make fancy plots for weather data provided by NOAA

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
### Monthly aggregates
#### Absolute values

Temperature:

`plot_monthly.py -infile ./data/kotzebue.csv -loc Kotzebue -start 1990-01-01 -end 2019-12-31 -type Temperature -trail 12 -plot`

![alt text](https://raw.githubusercontent.com/initze/noaaplotter/master/figures/monthly_series_temperature_12mthsTrMn_Kotzebue.png "Mean monthly temperatures with 12 months trailing mean")

Precipitation:


`plot_monthly.py -infile ./data/kotzebue.csv -loc Kotzebue -start 1990-01-01 -end 2019-12-31 -type Precipitation -trail 12 -plot`

![alt text](https://raw.githubusercontent.com/initze/noaaplotter/master/figures/monthly_series_precipitation_12mthsTrMn_Kotzebue.png "Mean monthly temperatures with 12 months trailing mean")

#### Anomalies from Climate (1981-2010)

Temperature:

`plot_monthly.py -infile ./data/kotzebue.csv -loc Kotzebue -start 1990-01-01 -end 2019-12-31 -type Temperature -trail 12 -plot -anomaly`

![alt text](https://raw.githubusercontent.com/initze/noaaplotter/master/figures/monthly_series_temperature_12mthsTrMn_Kotzebue_anomaly.png "Mean monthly temperatures with 12 months trailing mean")

Precipitation:


`plot_monthly.py -infile ./data/kotzebue.csv -loc Kotzebue -start 1990-01-01 -end 2019-12-31 -type Precipitation -trail 12 -plot -anomaly`

![alt text](https://raw.githubusercontent.com/initze/noaaplotter/master/figures/monthly_series_precipitation_12mthsTrMn_Kotzebue_anomaly.png "Mean monthly temperatures with 12 months trailing mean")
