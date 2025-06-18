# MeteoForecast

MeteoForecast is a tool written in Python to get weather forecast data from Polish service meteo.pl.

## Requirements

- Python 3.11 or newer

## Installation

```bash
pip install git+https://github.com/gawronpio/MeteoForecast.git
```

## Usage

To use this library you have to firstly get an API key from meteo.pl. You can do this by registering on 
[api.meteo.pl](https://api.meteo.pl/) website and following the instructions.

Library can be configured by passing a dictionary with configuration parameters to the constructor of the 
`MeteoForecast` class and or by setting the configuration in the `get_forecast` method. See examples bellow.

### Config dictionary

Description of all models, grids and fields cen be found on [api.meteo.pl](https://api.meteo.pl/docs/) website.

```python
config = {
    'model': 'wrf',  # forecast model (comaps or wrf)
    'grid': 'd02_XLONG_XLAT',  # coordinate grid
    'fields': [
        # (field, level)
        ('TSK', 0),  # wrf ground temperature
        ('T2', 0),  # wrf air temperature at 2m above ground level
        ('RAINNC', 0),  # wrf accumulated rain in mm
        ('SNOWNC', 0),  # wrf accumulated snow in mm
        ('HAILNC', 0),  # wrf accumulated hail in mm (grad)
        ('U10', 0),  # wrf Wind speed in U direction at 10 meters above ground
        ('V10', 0),  # wrf Wind speed in V direction at 10 meters above ground
        ('WSPD10MAX', 0),  # wrf Maximum wind speed at 10 meters above ground (porywy wiatru)
        ('SWDOWN', 0),  # wrf Downward shortwave radiation flux (nasłonecznienie)
        ('PSFC', 0),  # wrf Surface pressure
    ]
}
```

### Usage examples

```python
from meteo_forecast import MeteoForecast

api_key = 'YOU_API_KEY'
meteo = MeteoForecast(api_key, latitude=52.2297, longitude=21.0122)  # Default config will be used
forecast = meteo.get_forecast()
```

```python
from meteo_forecast import MeteoForecast

api_key = 'YOU_API_KEY'
config = {
    'model': 'comaps',
    'grid': '2a',
    'fields': [
        ('airtmp_zht_fcstfld', 0),
        ('slpres_msl_fcstfld', 0),
    ]
}
meteo = MeteoForecast(api_key=api_key, config=config)
forecast = meteo.get_forecast(latitude=52.2297, longitude=21.0122)
```

```python
from meteo_forecast import MeteoForecast

api_key = 'YOU_API_KEY'
meteo = MeteoForecast(api_key=api_key)
forecast = meteo.get_forecast(latitude=52.2297, longitude=21.0122)  # Default config will be used
```

## License

The project is made available under the MIT license.
