"""
Copyright (c) 2025 Piotr Gawron (dev@gawron.biz)
This file is licensed under the MIT License.
For details, see the LICENSE file in the project root.

Integration tests for MeteoForecast class.
"""

import warnings
from datetime import datetime
from unittest.mock import patch

import pytz
import requests

from meteo_forecast.meteo_forecast import MeteoForecast


class TestMeteoForecastIntegration:
    """Integration tests for MeteoForecast class - testing method interactions."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.api_key = "test_api_key"
        self.latitude = 52.2297
        self.longitude = 21.0122

    @patch('meteo_forecast.meteo_forecast.datetime')
    @patch.object(MeteoForecast, '_connect_meteo_api')
    def test_get_forecast_integration(self, mock_connect, mock_datetime):
        """Test get_forecast method integration with multiple API calls."""
        # Mock current time
        mock_now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=pytz.UTC)
        mock_datetime.now.return_value = mock_now
        mock_datetime.strptime = datetime.strptime

        # Mock API responses
        def mock_api_response(url, post=False):
            if 'date/' in url and not post:
                return {
                    'dates': [{
                        'starting-date': '2024-01-14T00',
                        'interval': 6,
                        'count': 8
                    }]
                }
            elif 'forecast/' in url and post:
                return {
                    'times': ['2024-01-15T00', '2024-01-15T06'],
                    'data': [15.5, 16.2]
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

            result = forecast.get_forecast()

            # Verify structure of returned data
            assert isinstance(result, dict)
            assert '2024-01-15T00' in result
            assert '2024-01-15T06' in result
            assert 'T2' in result['2024-01-15T00']
            assert result['2024-01-15T00']['T2'][0] == 15.5
            assert result['2024-01-15T06']['T2'][0] == 16.2

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
                assert result == {}
