"""
Copyright (c) 2025 Piotr Gawron (dev@gawron.biz)
This file is licensed under the MIT License.
For details, see the LICENSE file in the project root.

End-to-end tests for MeteoForecast class.
"""


import warnings
from unittest.mock import Mock, patch

import pytest
import requests

from meteo_forecast.meteo_forecast import MeteoForecast
from tests.base_test import BaseTest
from tests.mocks import (
    get_mock_get_response,
    get_mock_post_response,
    get_times_nad_vals,
)


class TestMeteoForecastEndToEnd(BaseTest):
    """End-to-end tests for MeteoForecast class - testing with realistic scenarios."""

    @patch('requests.get')
    @patch('requests.post')
    def test_realistic_weather_forecast_scenario(self, mock_post, mock_get):
        """Test realistic weather forecast scenario with multiple fields."""
        times_and_vals = get_times_nad_vals()
        mock_get.side_effect = get_mock_get_response()
        mock_post.side_effect = get_mock_post_response(times_and_vals=times_and_vals)
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

        assert len(result) == len(times_and_vals['times'])

        for i, time_point in enumerate(times_and_vals['times']):
            assert time_point in result
            assert 'T2' in result[time_point]
            assert 'RAINNC' in result[time_point]
            assert 'U10' in result[time_point]
            assert 'PSFC' in result[time_point]
            for field, level in config['fields']:
                assert result[time_point][field][level] == times_and_vals['vals'][field][i]

    @patch('requests.get')
    def test_api_error_handling_scenario(self, mock_get):
        """Test end-to-end error handling scenarios."""
        # Test invalid API key scenario
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = 'Invalid API key'
        mock_get.return_value = mock_response

        with pytest.raises(ValueError, match="Failed to connect to Meteo API: 401 - Invalid API key"):
            MeteoForecast(self.api_key, self.latitude, self.longitude)

    @patch('requests.get')
    def test_network_timeout_scenario(self, mock_get):
        """Test network timeout handling."""
        mock_get.side_effect = requests.Timeout("Request timed out")

        with pytest.raises(requests.Timeout):
            MeteoForecast(self.api_key, self.latitude, self.longitude)

    @patch('requests.get')
    def test_partial_data_availability_scenario(self, mock_get):
        """Test scenario where only some forecast data is available."""
        mock_get.side_effect = get_mock_get_response(True)

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
            assert isinstance(result, dict)
            assert not result
