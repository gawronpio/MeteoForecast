"""
Copyright (c) 2025 Piotr Gawron (dev@gawron.biz)
This file is licensed under the MIT License.
For details, see the LICENSE file in the project root.

Unit tests for MeteoForecast class.
"""

from unittest.mock import Mock, patch

import pytest

from meteo_forecast.meteo_forecast import MeteoForecast


class TestMeteoForecastUnit:
    """Unit tests for MeteoForecast class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.api_key = "test_api_key"
        self.latitude = 52.2297
        self.longitude = 21.0122
        self.test_config = {
            'model': 'wrf',
            'grid': 'd01_XLONG_XLAT',
            'fields': [('T2', 0), ('RAINNC', 0)]
        }

    def test_init_with_default_config(self):
        """Test MeteoForecast initialization with default configuration."""
        with patch.object(MeteoForecast, '_set_xy'):
            forecast = MeteoForecast(self.api_key, self.latitude, self.longitude)

            assert forecast.lat == self.latitude
            assert forecast.lon == self.longitude
            assert forecast.api_key == self.api_key
            assert forecast.config == MeteoForecast._default_config
            assert forecast.main_url == f'{MeteoForecast._base_url}wrf/grid/d02_XLONG_XLAT/'

    def test_init_with_custom_config(self):
        """Test MeteoForecast initialization with custom configuration."""
        with patch.object(MeteoForecast, '_set_xy'):
            forecast = MeteoForecast(self.api_key, self.latitude, self.longitude, self.test_config)

            assert forecast.config == self.test_config

    @patch('meteo_forecast.meteo_forecast.requests.get')
    def test_connect_meteo_api_static_get_success(self, mock_get):
        """Test static API connection method with GET request - success case."""
        api_key = 'test_key'
        expected_result = {'data': 'test'}
        url = 'http://test.url'
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_result
        mock_get.return_value = mock_response

        result = MeteoForecast._connect_meteo_api_(api_key, url)

        assert result == expected_result
        mock_get.assert_called_once_with(url, headers={'Authorization': f'Token {api_key}'})

    @patch('meteo_forecast.meteo_forecast.requests.post')
    def test_connect_meteo_api_static_post_success(self, mock_post):
        """Test static API connection method with POST request - success case."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': 'test'}
        mock_post.return_value = mock_response

        result = MeteoForecast._connect_meteo_api_('test_key', 'http://test.url', post=True)

        assert result == {'data': 'test'}
        mock_post.assert_called_once_with('http://test.url', headers={'Authorization': 'Token test_key'})

    @patch('meteo_forecast.meteo_forecast.requests.get')
    def test_connect_meteo_api_static_failure(self, mock_get):
        """Test static API connection method - failure case."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = 'Unauthorized'
        mock_get.return_value = mock_response

        with pytest.raises(ValueError, match="Failed to connect to Meteo API: 401 - Unauthorized"):
            MeteoForecast._connect_meteo_api_('invalid_key', 'http://test.url')

    def test_connect_meteo_api_instance_method(self):
        """Test instance API connection method."""
        with patch.object(MeteoForecast, '_set_xy'), \
                patch.object(MeteoForecast, '_connect_meteo_api_') as mock_static:
            mock_static.return_value = {'data': 'test'}
            forecast = MeteoForecast(self.api_key, self.latitude, self.longitude)

            result = forecast._connect_meteo_api('http://test.url', post=True)

            assert result == {'data': 'test'}
            mock_static.assert_called_once_with(api_key=self.api_key, url='http://test.url', post=True)

    @patch.object(MeteoForecast, '_connect_meteo_api_')
    def test_get_xy_static(self, mock_connect):
        """Test static get_xy method."""
        mock_connect.return_value = {'points': [{'col': 100, 'row': 200}]}

        x, y = MeteoForecast.get_xy('test_key', 52.0, 21.0, 'wrf', 'd02_XLONG_XLAT')

        assert x == 100
        assert y == 200
        expected_url = f'{MeteoForecast._base_url}wrf/grid/d02_XLONG_XLAT/latlon2rowcol/52.0%2C21.0/'
        mock_connect.assert_called_once_with(api_key='test_key', url=expected_url)

    def test_set_xy_instance_method(self):
        """Test instance _set_xy method."""
        with patch.object(MeteoForecast, 'get_xy') as mock_get_xy:
            mock_get_xy.return_value = (150, 250)

            forecast = MeteoForecast(self.api_key, self.latitude, self.longitude)

            assert forecast.x == 150
            assert forecast.y == 250
            mock_get_xy.assert_called_once_with(
                self.api_key, self.latitude, self.longitude,
                model='wrf', grid='d02_XLONG_XLAT'
            )

    def test_get_forecast_dates_static(self):
        """Test static _get_forecast_dates method."""
        date_dict = {
            'starting-date': '2024-01-01T00',
            'interval': 6,
            'count': 3
        }

        result = MeteoForecast._get_forecast_dates(date_dict)

        expected = ['2024-01-01T00', '2024-01-01T06', '2024-01-01T12']
        assert result == expected

    @patch.object(MeteoForecast, '_connect_meteo_api_')
    def test_available_models_static(self, mock_connect):
        """Test static available_models method."""
        mock_connect.return_value = {'models': ['wrf', 'gfs']}

        result = MeteoForecast.available_models('test_key')

        assert result == ['wrf', 'gfs']
        mock_connect.assert_called_once_with('test_key', MeteoForecast._base_url)

    @patch.object(MeteoForecast, '_connect_meteo_api_')
    def test_available_grids_static(self, mock_connect):
        """Test static available_grids method."""
        mock_connect.return_value = {'grids': ['d01', 'd02_XLONG_XLAT']}

        result = MeteoForecast.available_grids('test_key', 'wrf')

        assert result == ['d01', 'd02_XLONG_XLAT']
        expected_url = f'{MeteoForecast._base_url}wrf/grid/'
        mock_connect.assert_called_once_with('test_key', expected_url)

    @patch.object(MeteoForecast, 'get_xy')
    @patch.object(MeteoForecast, '_connect_meteo_api_')
    def test_available_fields_static(self, mock_connect, mock_get_xy):
        """Test static available_fields method."""
        mock_get_xy.return_value = (100, 200)
        mock_connect.return_value = {'fields': ['T2', 'RAINNC', 'U10']}

        result = MeteoForecast.available_fields('test_key', 'wrf', 'd02_XLONG_XLAT', 52.0, 21.0)

        assert result == ['T2', 'RAINNC', 'U10']
        mock_get_xy.assert_called_once_with('test_key', 52.0, 21.0, 'wrf', 'd02_XLONG_XLAT')
        expected_url = f'{MeteoForecast._base_url}wrf/grid/d02_XLONG_XLAT/coordinates/200%2C100/field/'
        mock_connect.assert_called_once_with('test_key', expected_url)

    @patch.object(MeteoForecast, 'get_xy')
    @patch.object(MeteoForecast, '_connect_meteo_api_')
    def test_available_levels_static(self, mock_connect, mock_get_xy):
        """Test static available_levels method."""
        mock_get_xy.return_value = (100, 200)
        mock_connect.return_value = {'levels': [0, 850, 500]}

        result = MeteoForecast.available_levels('test_key', 'wrf', 'd02_XLONG_XLAT', 'T2', 52.0, 21.0)

        assert result == [0, 850, 500]
        mock_get_xy.assert_called_once_with('test_key', 52.0, 21.0, 'wrf', 'd02_XLONG_XLAT')
        expected_url = f'{MeteoForecast._base_url}wrf/grid/d02_XLONG_XLAT/coordinates/200%2C100/field/T2/level/'
        mock_connect.assert_called_once_with('test_key', expected_url)
