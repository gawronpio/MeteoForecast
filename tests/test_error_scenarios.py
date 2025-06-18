"""
Copyright (c) 2025 Piotr Gawron (dev@gawron.biz)
This file is licensed under the MIT License.
For details, see the LICENSE file in the project root.

Error scenarios tests for MeteoForecast class.
"""

import json
from unittest.mock import Mock, patch

import pytest
import requests

from meteo_forecast.meteo_forecast import MeteoForecast
from tests.base_test import BaseTest


class TestMeteoForecastErrorScenarios(BaseTest):
    """Test error scenarios and exception handling."""

    @patch('requests.get')
    def test_api_authentication_error(self, mock_get):
        """Test handling of API authentication errors."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = 'Unauthorized: Invalid API key'
        mock_get.return_value = mock_response

        with pytest.raises(ValueError, match="Failed to connect to Meteo API: 401 - Unauthorized: Invalid API key"):
            MeteoForecast(self.api_key, self.latitude, self.longitude)

    @patch('requests.get')
    def test_api_rate_limit_error(self, mock_get):
        """Test handling of API rate limit errors."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.text = 'Too Many Requests'
        mock_get.return_value = mock_response

        with pytest.raises(ValueError, match="Failed to connect to Meteo API: 429 - Too Many Requests"):
            MeteoForecast(self.api_key, self.latitude, self.longitude)

    @patch('requests.get')
    def test_api_server_error(self, mock_get):
        """Test handling of API server errors."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'
        mock_get.return_value = mock_response

        with pytest.raises(ValueError, match="Failed to connect to Meteo API: 500 - Internal Server Error"):
            MeteoForecast(self.api_key, self.latitude, self.longitude)

    @patch('requests.get')
    def test_network_connection_error(self, mock_get):
        """Test handling of network connection errors."""
        mock_get.side_effect = requests.ConnectionError("Failed to establish connection")

        with pytest.raises(requests.ConnectionError):
            MeteoForecast(self.api_key, self.latitude, self.longitude)

    @patch('requests.get')
    def test_network_timeout_error(self, mock_get):
        """Test handling of network timeout errors."""
        mock_get.side_effect = requests.Timeout("Request timed out")

        with pytest.raises(requests.Timeout):
            MeteoForecast(self.api_key, self.latitude, self.longitude)

    @patch('requests.get')
    def test_invalid_json_response(self, mock_get):
        """Test handling of invalid JSON responses."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_get.return_value = mock_response

        with pytest.raises(json.JSONDecodeError):
            MeteoForecast(self.api_key, self.latitude, self.longitude)

    @patch('requests.get')
    def test_missing_points_in_response(self, mock_get):
        """Test handling of missing 'points' key in API response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'error': 'No points found'}
        mock_get.return_value = mock_response

        with pytest.raises(KeyError):
            MeteoForecast(self.api_key, self.latitude, self.longitude)

    @patch('requests.get')
    def test_empty_points_array(self, mock_get):
        """Test handling of empty points array in API response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'points': []}
        mock_get.return_value = mock_response

        with pytest.raises(IndexError):
            MeteoForecast(self.api_key, self.latitude, self.longitude)

    @patch('requests.get')
    def test_malformed_coordinates_response(self, mock_get):
        """Test handling of malformed coordinates in API response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'points': [{'invalid': 'data'}]}
        mock_get.return_value = mock_response

        with pytest.raises(KeyError):
            MeteoForecast(self.api_key, self.latitude, self.longitude)

    def test_invalid_api_key_type(self):
        """Test handling of invalid API key types."""
        with pytest.raises(TypeError):
            # This should fail when trying to use a non-string API key
            MeteoForecast(None, self.latitude, self.longitude)

    def test_invalid_coordinate_types(self):
        """Test handling of invalid coordinate types."""
        with patch.object(MeteoForecast, '_set_xy'):
            # Should handle string coordinates
            forecast = MeteoForecast(self.api_key, "52.2297", "21.0122")
            assert forecast.lat == "52.2297"
            assert forecast.lon == "21.0122"

    @patch.object(MeteoForecast, '_connect_meteo_api')
    def test_forecast_with_no_valid_dates(self, mock_connect):
        """Test forecast retrieval when no valid dates are available."""
        def mock_api_response(url, post=False):
            if 'date/' in url and not post:
                return {'dates': []}  # Empty dates array
            return {}

        mock_connect.side_effect = mock_api_response

        with patch.object(MeteoForecast, '_set_xy'):
            forecast = MeteoForecast(self.api_key, self.latitude, self.longitude, {
                'model': 'wrf',
                'grid': 'd02_XLONG_XLAT',
                'fields': [('T2', 0)]
            })
            forecast.x = 100
            forecast.y = 200

            import warnings
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                result = forecast.get_forecast()

                # Should get warning about failed field
                assert len(w) == 1
                assert "Failed to fetch data for field T2" in str(w[0].message)
                assert isinstance(result, dict)
                assert not result

    @patch.object(MeteoForecast, '_connect_meteo_api')
    def test_forecast_with_malformed_date_data(self, mock_connect):
        """Test forecast retrieval with malformed date data."""
        def mock_api_response(url, post=False):
            if 'date/' in url and not post:
                return {
                    'dates': [{
                        'starting-date': 'invalid-date-format',
                        'interval': 6,
                        'count': 4
                    }]
                }
            return {}

        mock_connect.side_effect = mock_api_response

        with patch.object(MeteoForecast, '_set_xy'):
            forecast = MeteoForecast(self.api_key, self.latitude, self.longitude, {
                'model': 'wrf',
                'grid': 'd02_XLONG_XLAT',
                'fields': [('T2', 0)]
            })
            forecast.x = 100
            forecast.y = 200

            import warnings
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                result = forecast.get_forecast()

                # Should get warning about failed field due to date parsing error
                assert len(w) == 1
                assert "Failed to fetch data for field T2" in str(w[0].message)
                assert isinstance(result, dict)
                assert not result

    @patch('requests.post')
    def test_forecast_post_request_failure(self, mock_post):
        """Test handling of POST request failures during forecast retrieval."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = 'Not Found'
        mock_post.return_value = mock_response

        with patch.object(MeteoForecast, '_set_xy'), \
             patch.object(MeteoForecast, '_connect_meteo_api') as mock_connect:

            def mock_api_response(*args, post=False, **kwargs):  # pylint: disable=unused-argument
                if not post:
                    return {
                        'dates': [{
                            'starting-date': '2024-01-14T00',
                            'interval': 6,
                            'count': 4
                        }]
                    }
                # This will trigger the POST request which will fail
                raise ValueError("Failed to connect to Meteo API: 404 - Not Found")

            mock_connect.side_effect = mock_api_response

            forecast = MeteoForecast(self.api_key, self.latitude, self.longitude, {
                'model': 'wrf',
                'grid': 'd02_XLONG_XLAT',
                'fields': [('T2', 0)]
            })
            forecast.x = 100
            forecast.y = 200

            with patch('meteo_forecast.meteo_forecast.datetime') as mock_datetime:
                from datetime import datetime

                import pytz
                mock_datetime.now.return_value = datetime(2024, 1, 15, 12, 0, 0, tzinfo=pytz.UTC)
                mock_datetime.strptime = datetime.strptime

                import warnings
                with warnings.catch_warnings(record=True) as w:
                    warnings.simplefilter("always")
                    result = forecast.get_forecast()

                    # Should get warning about failed field
                    assert len(w) == 1
                    assert "Failed to fetch data for field T2" in str(w[0].message)
                    assert isinstance(result, dict)
                    assert not result

    def test_static_methods_with_invalid_parameters(self):
        """Test static methods with invalid parameters."""
        # Test available_models with invalid API key
        with patch.object(MeteoForecast, '_connect_meteo_api_') as mock_connect:
            mock_connect.side_effect = ValueError("Invalid API key")

            with pytest.raises(ValueError):
                MeteoForecast.available_models("invalid_key")

        # Test get_xy with invalid coordinates
        with patch.object(MeteoForecast, '_connect_meteo_api_') as mock_connect:
            mock_connect.side_effect = ValueError("Invalid coordinates")

            with pytest.raises(ValueError):
                MeteoForecast.get_xy("test_key", 999, 999, "wrf", "d02_XLONG_XLAT")

    @patch.object(MeteoForecast, '_connect_meteo_api_')
    def test_available_methods_with_empty_responses(self, mock_connect):
        """Test available_* methods with empty responses."""
        # Test with missing keys in response
        mock_connect.return_value = {}

        with pytest.raises(KeyError):
            MeteoForecast.available_models("test_key")

        with pytest.raises(KeyError):
            MeteoForecast.available_grids("test_key", "wrf")

        # Test with empty arrays
        mock_connect.return_value = {'models': []}
        result = MeteoForecast.available_models("test_key")
        assert result == []
