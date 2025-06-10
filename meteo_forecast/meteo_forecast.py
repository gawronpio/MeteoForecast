import warnings
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import pytz
import requests


class MeteoForecast:
    """
    Class for fetching and processing meteorological forecast data from the meteo.pl API.

    Config can be added in contructor or can be used default config.
    Config contains:
        - model: Model name (default: 'wrf')
        - grid: Grid name (default: 'd02_XLONG_XLAT')
        - fields: List of tuples with field names and levels
        (default includes ground temperature, air temperature, rain, snow, hail, wind speed, maximum wind speed,
        sun radiation, and surface pressure)
    For available models, grids, fields, and levels please see https://api.meteo.pl/reference/

    :examples:
        >>> from meteo_forecast import MeteoForecast
        meteo = MeteoForecast(api_key='your_api_key', latitude=52.2297, longitude=21.0122)  # Using default config
        forecast = meteo.get_forecast()
    """
    default_config = {
        'model': 'wrf',
        'grid': 'd02_XLONG_XLAT',
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
            # ('COSZEN', 0),  # wrf Cosine of the solar zenith angle
            # ('COSALPHA', 0),  # wrf Cosine of the azimuth angle
            ('PSFC', 0),  # wrf Surface pressure
        ]
    }
    base_url = r'https://api.meteo.pl/api/v1/model/'

    def __init__(
            self,
            api_key: str,
            latitude: Optional[float] = None,
            longitude: Optional[float] = None,
            config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize MeteoForecast instance.
        All but api_key parameters are optional. If they were not provided they have to be set in get_forecast method.

        :param api_key: API key for meteo.pl
        :type api_key: str or None
        :param latitude: Latitude for the forecast location
        :type latitude: float or None
        :param longitude: Longitude for the forecast location
        :type longitude: float or None
        :param config: Optional configuration dictionary (model: str, grid: str, fields: List[Tuple[str, int]])
        :type config: dict or None
        """
        self.api_key = api_key
        if latitude is not None and longitude is not None:
            self.lat = latitude
            self.lon = longitude
        else:
            self.lat = None
            self.lon = None
        self.config = self.default_config if config is None else config
        MeteoForecast._check_config(self.config)
        self.main_url = f'{self.base_url}{self.config["model"]}/grid/{self.config["grid"]}/'
        self.x = None
        self.y = None

        if self.lat is not None and self.lon is not None:
            self._set_xy()

    @staticmethod
    def _check_config(config: dict):
        """
        Check if configuration dictionary has propper structure.

        :param config: Configuration dictionary to check
        :type config: dict
        :raises ValueError: If the configuration is missing required keys
        """
        for key, val_type in (
                ('model', str),
                ('grid', str),
                ('fields', list),
        ):
            if key not in config:
                raise ValueError(f'Configuration must have "{key}" key')
            if not isinstance(config[key], val_type):
                raise ValueError(f'Configuration "{key}" must be of type {val_type.__name__}')
        if len(config['fields']) == 0:
            raise ValueError('Fields cannot be empty. Please provide at least one field in the configuration.')
        for field in config['fields']:
            if (not isinstance(field, tuple) or len(field) != 2
                    or not isinstance(field[0], str) or not isinstance(field[1], int)):
                raise ValueError('Each field in "fields" must be a tuple of (field_name: str, level: int)')

    @staticmethod
    def _connect_meteo_api_(api_key: str, url: str, post: bool = False) -> dict:
        """
        Connect to the meteo.pl API and return the response as a dictionary.

        :param api_key: API key for meteo.pl
        :type api_key: str
        :param url: URL to connect to
        :type url: str
        :param post: Whether to use POST (default: False, uses GET)
        :type post: bool
        :return: Response from the API as a dictionary
        :rtype: dict
        :raises ValueError: If the API response status is not 200
        :raises TypeError: If api_key is not a string
        """
        if not isinstance(api_key, str):
            raise TypeError("api_key must be a string")
        headers = {'Authorization': f'Token {api_key}'}
        if post:
            response = requests.post(url, headers=headers)
        else:
            response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise ValueError(f"Failed to connect to Meteo API: {response.status_code} - {response.text}")
        return response.json()

    def _connect_meteo_api(self, url: str, post: bool = False) -> dict:
        """
        Instance wrapper for connecting to the meteo.pl API using the stored API key.

        :param url: URL to connect to
        :type url: str
        :param post: Whether to use POST (default: False, uses GET)
        :type post: bool
        :return: Response from the API as a dictionary
        :rtype: dict
        """
        return MeteoForecast._connect_meteo_api_(api_key=self.api_key, url=url, post=post)

    @staticmethod
    def get_xy(api_key: str, latitude: float, longitude: float, model: str, grid: str) -> tuple[int, int]:
        """
        Get grid coordinates (x, y) for a given latitude and longitude.

        :param api_key: API key for meteo.pl
        :type api_key: str
        :param latitude: Latitude
        :type latitude: float
        :param longitude: Longitude
        :type longitude: float
        :param model: Model name
        :type model: str
        :param grid: Grid name
        :type grid: str
        :return: Tuple of (x, y) grid coordinates
        :rtype: tuple[int, int]
        """
        url = f'{MeteoForecast.base_url}{model}/grid/{grid}/latlon2rowcol/{latitude}%2C{longitude}/'
        data = MeteoForecast._connect_meteo_api_(api_key=api_key, url=url)['points']
        return data[0]['col'], data[0]['row']

    def _set_xy(self):
        """
        Set the grid coordinates (x, y) for the instance based on latitude and longitude.
        """
        x, y = self.get_xy(
            self.api_key,
            self.lat,
            self.lon,
            model=self.config['model'],
            grid=self.config['grid']
        )
        self.x = x
        self.y = y

    @staticmethod
    def _get_forecast_dates(date: dict) -> list:
        """
        Generate a list of forecast date strings based on the date dictionary from the API.

        :param date: Dictionary with 'starting-date', 'interval', and 'count'
        :type date: dict
        :return: List of date strings in format "%Y-%m-%dT%H"
        :rtype: list
        """
        start_date = datetime.strptime(date['starting-date'], "%Y-%m-%dT%H")
        interval_hours = date['interval']
        num_intervals = date['count']
        dates = [
            (start_date + timedelta(hours=i * interval_hours)).strftime("%Y-%m-%dT%H")
            for i in range(num_intervals)
        ]
        return dates

    def get_forecast(
            self,
            latitude: Optional[float] = None,
            longitude: Optional[float] = None,
            config: Optional[Dict[str, Any]] = None
    ) -> dict:
        """
        Fetch the weather forecast for the configured location and fields.

        Both latitude and longitude have to be passed to use them instead of already set in constructor.

        :param latitude: Latitude for the forecast location (optional, overrides instance latitude)
        :type latitude: float or None
        :param longitude: Longitude for the forecast location (optional, overrides instance longitude)
        :type longitude: float or None
        :param config: Optional configuration dictionary to override instance config
        :type config: dict or None
        :return: Nested dictionary with forecast data for each time and field
        :rtype: dict
        :raises ValueError: If no valid forecast date is found for a field
        :warns: If fetching data for a field fails
        """
        if config is None:
            config = self.config
        MeteoForecast._check_config(config)
        if latitude is not None and longitude is not None:
            x, y = self.get_xy(
                api_key=self.api_key,
                latitude=latitude,
                longitude=longitude,
                model=config['model'],
                grid=config['grid']
            )
        else:
            x, y = self.x, self.y

        if config is None:
            raise ValueError("Configuration must be provided either in constructor or as an argument to get_forecast method.")
        if x is None or y is None:
            raise ValueError("Coordinates must be set before fetching the forecast. Set latitude and longitude in constructor or in get_forecast call.")

        forecasts = {}
        url = f'{self.base_url}{config["model"]}/grid/{config["grid"]}/coordinates/{y}%2C{x}/field/'
        for field in config['fields']:
            try:
                url_field = f'{url}{field[0]}/level/{field[1]}/'
                url_date = f'{url_field}date/'
                dates = self._connect_meteo_api(url_date)['dates']
                actual_date_minus_24 = datetime.now(pytz.UTC).replace(
                    minute=0,
                    second=0,
                    microsecond=0
                ) - timedelta(hours=24)
                last_forecast_date = None
                for date in dates[::-1]:
                    forecast_dates = self._get_forecast_dates(date)
                    for forecast_date in forecast_dates[::-1]:
                        if datetime.strptime(forecast_date, "%Y-%m-%dT%H").replace(tzinfo=pytz.UTC) >= actual_date_minus_24:
                            last_forecast_date = forecast_date
                            break
                    if last_forecast_date is not None:
                        break
                if last_forecast_date is None:
                    raise ValueError(f"No valid forecast date found for field {field[0]} at level {field[1]}")

                url_forecast = f'{url_field}date/{last_forecast_date}/forecast/'
                forecast_data = self._connect_meteo_api(url_forecast, True)
                for time, data in zip(forecast_data['times'], forecast_data['data']):
                    if time not in forecasts:
                        forecasts[time] = {}
                    if field[0] not in forecasts[time]:
                        forecasts[time][field[0]] = {}
                    forecasts[time][field[0]][field[1]] = data
            except Exception as e:
                warnings.warn(f"Failed to fetch data for field {field[0]} at level {field[1]}: {e}")
        return forecasts

    @staticmethod
    def available_models(api_key: str) -> list:
        """
        Get a list of available models from the API.

        :param api_key: API key for meteo.pl
        :type api_key: str
        :return: List of available model names
        :rtype: list
        """
        return MeteoForecast._connect_meteo_api_(api_key, MeteoForecast.base_url)['models']

    @staticmethod
    def available_grids(api_key: str, model: str) -> list:
        """
        Get a list of available grids for a given model from the API.

        :param api_key: API key for meteo.pl
        :type api_key: str
        :param model: Model name
        :type model: str
        :return: List of available grid names
        :rtype: list
        """
        url = f'{MeteoForecast.base_url}{model}/grid/'
        return MeteoForecast._connect_meteo_api_(api_key, url)['grids']

    @staticmethod
    def available_fields(api_key: str, model: str, grid: str, latitude: float, longitude: float) -> list:
        """
        Get a list of available fields for a given model, grid, and location from the API.

        :param api_key: API key for meteo.pl
        :type api_key: str
        :param model: Model name
        :type model: str
        :param grid: Grid name
        :type grid: str
        :param latitude: Latitude
        :type latitude: float
        :param longitude: Longitude
        :type longitude: float
        :return: List of available field names
        :rtype: list
        """
        x, y = MeteoForecast.get_xy(api_key, latitude, longitude, model, grid)
        url = f'{MeteoForecast.base_url}{model}/grid/{grid}/coordinates/{y}%2C{x}/field/'
        return MeteoForecast._connect_meteo_api_(api_key, url)['fields']

    @staticmethod
    def available_levels(api_key: str, model: str, grid: str, field: str, latitude: float, longitude: float) -> list:
        """
        Get a list of available levels for a given field, model, grid, and location from the API.

        :param api_key: API key for meteo.pl
        :type api_key: str
        :param model: Model name
        :type model: str
        :param grid: Grid name
        :type grid: str
        :param field: Field name
        :type field: str
        :param latitude: Latitude
        :type latitude: float
        :param longitude: Longitude
        :type longitude: float
        :return: List of available levels
        :rtype: list
        """
        x, y = MeteoForecast.get_xy(api_key, latitude, longitude, model, grid)
        url = f'{MeteoForecast.base_url}{model}/grid/{grid}/coordinates/{y}%2C{x}/field/{field}/level/'
        return MeteoForecast._connect_meteo_api_(api_key, url)['levels']
