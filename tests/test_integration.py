"""
Copyright (c) 2025 Piotr Gawron (dev@gawron.biz)
This file is licensed under the MIT License.
For details, see the LICENSE file in the project root.

Integration tests for MeteoForecast class.
"""

import warnings
from unittest.mock import patch

import pytest
import requests

from meteo_forecast.meteo_forecast import MeteoForecast
from tests.base_test import BaseTest
from tests.mocks import (
    get_mock_get_response,
    get_mock_post_response,
    get_times_nad_vals,
)


class TestMeteoForecastIntegration(BaseTest):
    """Integration tests for MeteoForecast class - testing method interactions."""

    @patch.object(MeteoForecast, '_connect_meteo_api')
    def test_get_forecast_integration(self, mock_connect):
        """Test get_forecast method integration with multiple API calls."""
        times_and_vals = get_times_nad_vals()

        def mock_api_response(url, post=False):
            if post:
                return get_mock_post_response(times_and_vals)(url).json()
            return get_mock_get_response()(url).json()

        mock_connect.side_effect = mock_api_response
        config = {
            'model': 'wrf',
            'grid': 'd02_XLONG_XLAT',
            'fields': [('T2', 0)]
        }

        with patch.object(MeteoForecast, '_set_xy'):
            forecast = MeteoForecast(self.api_key, self.latitude, self.longitude, config)
            forecast.x = 100
            forecast.y = 200

            result = forecast.get_forecast()

            # Verify structure of returned data
            assert isinstance(result, dict)
            for i, time in enumerate(times_and_vals['times']):
                assert time in result
                for field, level in config['fields']:
                    assert field in result[time]
                    assert result[time][field][level] == times_and_vals['vals'][field][i]

    @patch.object(MeteoForecast, '_connect_meteo_api')
    def test_get_forecast_with_warnings(self, mock_connect):
        """Test get_forecast method when some fields fail to fetch."""

        def mock_api_response(url, post=False):
            # All fields fail to simulate error handling
            raise requests.RequestException("Network error")

        mock_connect.side_effect = mock_api_response

        with patch.object(MeteoForecast, '_set_xy'):
            forecast = MeteoForecast(self.api_key, self.latitude, self.longitude, {
                'model': 'wrf',
                'grid': 'd02_XLONG_XLAT',
                'fields': [('T2', 0), ('RAINNC', 0)]
            })
            forecast.x = 100
            forecast.y = 200

            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                result = forecast.get_forecast()

                # Check that warnings were issued for failed fields
                assert len(w) >= 2  # At least one warning per field
                # Check that result is empty when all fields fail
                assert isinstance(result, dict)
                assert not result

    def test_get_forecast_with_missing_coordinates(self):
        """Test get_forecast with missing coordinates."""
        with patch.object(MeteoForecast, '_set_xy'):
            meteo = MeteoForecast(self.api_key)
            with pytest.raises(ValueError, match="Coordinates must be set before fetching the forecast"):
                meteo.get_forecast()

    @pytest.mark.filterwarnings("ignore:Failed to fetch data for field")
    @patch.object(MeteoForecast, 'get_xy')
    def test_get_forecast_with_coordinates(self, mock_get_xy):
        """Test get_forecast with valid coordinates."""
        latitude = 52.2297
        longitude = 21.0122
        x_expected = 100
        y_expected = 200
        model = 'abc'
        grid = 'a1b2'
        field = 'T2'
        level = 0
        expected_url = (f'{MeteoForecast.base_url}'
                        f'{model}'
                        f'/grid/{grid}'
                        f'/coordinates/{y_expected}%2C{x_expected}'
                        f'/field/{field}'
                        f'/level/{level}'
                        f'/date/')
        mock_get_xy.return_value = (x_expected, y_expected)

        with patch.object(MeteoForecast, '_set_xy'):
            meteo = MeteoForecast(self.api_key, config={
                'model': model,
                'grid': grid,
                'fields': [(field, level)]
            })

            with patch.object(meteo, '_connect_meteo_api') as mock_meteo_api:
                meteo.get_forecast(latitude, longitude)
                mock_meteo_api.assert_called_with(expected_url)
