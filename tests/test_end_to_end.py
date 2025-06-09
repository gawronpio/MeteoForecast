"""
Copyright (c) 2025 Piotr Gawron (dev@gawron.biz)
This file is licensed under the MIT License.
For details, see the LICENSE file in the project root.

End-to-end tests for MeteoForecast class.
"""


import warnings
from datetime import datetime
from unittest.mock import Mock, patch

import pytest
import pytz
import requests

from meteo_forecast.meteo_forecast import MeteoForecast


class TestMeteoForecastEndToEnd:
    """End-to-end tests for MeteoForecast class - testing with realistic scenarios."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.api_key = "test_api_key"
        self.latitude = 52.2297  # Warsaw coordinates
        self.longitude = 21.0122

    @patch('meteo_forecast.meteo_forecast.requests.get')
    @patch('meteo_forecast.meteo_forecast.requests.post')
    def test_realistic_weather_forecast_scenario(self, mock_post, mock_get):
        """Test realistic weather forecast scenario with multiple fields."""

        # Mock realistic API responses
        def mock_get_response(url, headers=None):
            response = Mock()
            response.status_code = 200

            if 'latlon2rowcol' in url:
                response.json.return_value = {'points': [{'col': 150, 'row': 250}]}
            elif 'date/' in url:
                response.json.return_value = {
                    'dates': [
                        {
                            'starting-date': '2024-01-14T00',
                            'interval': 3,
                            'count': 16
                        },
                        {
                            'starting-date': '2024-01-13T12',
                            'interval': 6,
                            'count': 8
                        }
                    ]
                }
            return response

        def mock_post_response(url, headers=None):
            response = Mock()
            response.status_code = 200

            # Different realistic data for different fields
            if 'T2' in url:  # Temperature
                response.json.return_value = {
                    'times': ['2024-01-15T00', '2024-01-15T03', '2024-01-15T06'],
                    'data': [2.5, 1.8, 3.2]  # Celsius
                }
            elif 'RAINNC' in url:  # Rain
                response.json.return_value = {
                    'times': ['2024-01-15T00', '2024-01-15T03', '2024-01-15T06'],
                    'data': [0.0, 0.5, 1.2]  # mm
                }
            elif 'U10' in url:  # Wind U component
                response.json.return_value = {
                    'times': ['2024-01-15T00', '2024-01-15T03', '2024-01-15T06'],
                    'data': [3.5, 4.2, 2.8]  # m/s
                }
            elif 'PSFC' in url:  # Surface pressure
                response.json.return_value = {
                    'times': ['2024-01-15T00', '2024-01-15T03', '2024-01-15T06'],
                    'data': [101325, 101280, 101350]  # Pa
                }

            return response

        mock_get.side_effect = mock_get_response
        mock_post.side_effect = mock_post_response

        with patch('meteo_forecast.meteo_forecast.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 15, 12, 0, 0, tzinfo=pytz.UTC)
            mock_datetime.strptime = datetime.strptime

            # Create forecast with multiple realistic fields
            config = {
                'model': 'wrf',
                'grid': 'd02_XLONG_XLAT',
                'fields': [
                    ('T2', 0),  # Temperature
                    ('RAINNC', 0),  # Rain
                    ('U10', 0),  # Wind U
                    ('PSFC', 0)  # Pressure
                ]
            }

            forecast = MeteoForecast(self.api_key, self.latitude, self.longitude, config)
            result = forecast.get_forecast()

            # Verify comprehensive forecast data
            assert len(result) == 3  # Three time points

            for time_point in ['2024-01-15T00', '2024-01-15T03', '2024-01-15T06']:
                assert time_point in result
                assert 'T2' in result[time_point]
                assert 'RAINNC' in result[time_point]
                assert 'U10' in result[time_point]
                assert 'PSFC' in result[time_point]

            # Verify specific values
            assert result['2024-01-15T00']['T2'][0] == 2.5
            assert result['2024-01-15T03']['RAINNC'][0] == 0.5
            assert result['2024-01-15T06']['U10'][0] == 2.8
            assert result['2024-01-15T00']['PSFC'][0] == 101325

    @patch('meteo_forecast.meteo_forecast.requests.get')
    def test_api_error_handling_scenario(self, mock_get):
        """Test end-to-end error handling scenarios."""
        # Test invalid API key scenario
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = 'Invalid API key'
        mock_get.return_value = mock_response

        with pytest.raises(ValueError, match="Failed to connect to Meteo API: 401 - Invalid API key"):
            MeteoForecast(self.api_key, self.latitude, self.longitude)

    @patch('meteo_forecast.meteo_forecast.requests.get')
    def test_network_timeout_scenario(self, mock_get):
        """Test network timeout handling."""
        mock_get.side_effect = requests.Timeout("Request timed out")

        with pytest.raises(requests.Timeout):
            MeteoForecast(self.api_key, self.latitude, self.longitude)

    @patch('meteo_forecast.meteo_forecast.requests.get')
    @patch('meteo_forecast.meteo_forecast.requests.post')
    def test_partial_data_availability_scenario(self, mock_post, mock_get):
        """Test scenario where only some forecast data is available."""

        def mock_get_response(url, headers=None):
            response = Mock()
            response.status_code = 200

            if 'latlon2rowcol' in url:
                response.json.return_value = {'points': [{'col': 100, 'row': 200}]}
            elif 'date/' in url:
                # Simulate old data that doesn't meet the 24-hour threshold
                response.json.return_value = {
                    'dates': [{
                        'starting-date': '2024-01-10T00',  # Old date
                        'interval': 6,
                        'count': 4
                    }]
                }
            return response

        mock_get.side_effect = mock_get_response

        with patch('meteo_forecast.meteo_forecast.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 15, 12, 0, 0, tzinfo=pytz.UTC)
            mock_datetime.strptime = datetime.strptime

            forecast = MeteoForecast(self.api_key, self.latitude, self.longitude, {
                'model': 'wrf',
                'grid': 'd02_XLONG_XLAT',
                'fields': [('T2', 0)]
            })

            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                result = forecast.get_forecast()

                # Should get warning about no valid forecast date
                assert len(w) == 1
                assert "No valid forecast date found" in str(w[0].message)

                # Result should be empty dict
                assert result == {}
