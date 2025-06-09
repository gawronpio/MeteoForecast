"""
Copyright (c) 2025 Piotr Gawron (dev@gawron.biz)
This file is licensed under the MIT License.
For details, see the LICENSE file in the project root.

Functional tests for MeteoForecast class.
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytz

from meteo_forecast.meteo_forecast import MeteoForecast


class TestMeteoForecastFunctional:
    """Functional tests for MeteoForecast class - testing complete workflows."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.api_key = "test_api_key"
        self.latitude = 52.2297
        self.longitude = 21.0122

    @patch('meteo_forecast.meteo_forecast.requests.get')
    @patch('meteo_forecast.meteo_forecast.requests.post')
    def test_complete_forecast_workflow(self, mock_post, mock_get):
        """Test complete workflow from initialization to forecast retrieval."""

        # Mock responses for different API calls
        def mock_get_response(url, headers=None):
            response = Mock()
            response.status_code = 200

            if 'latlon2rowcol' in url:
                response.json.return_value = {'points': [{'col': 100, 'row': 200}]}
            elif 'date/' in url:
                response.json.return_value = {
                    'dates': [{
                        'starting-date': '2024-01-14T00',
                        'interval': 6,
                        'count': 4
                    }]
                }
            else:
                response.json.return_value = {}

            return response

        def mock_post_response(url, headers=None):
            response = Mock()
            response.status_code = 200
            response.json.return_value = {
                'times': ['2024-01-15T00', '2024-01-15T06'],
                'data': [15.5, 16.2]
            }
            return response

        mock_get.side_effect = mock_get_response
        mock_post.side_effect = mock_post_response

        with patch('meteo_forecast.meteo_forecast.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 15, 12, 0, 0, tzinfo=pytz.UTC)
            mock_datetime.strptime = datetime.strptime

            # Initialize forecast object
            forecast = MeteoForecast(self.api_key, self.latitude, self.longitude, {
                'model': 'wrf',
                'grid': 'd02_XLONG_XLAT',
                'fields': [('T2', 0)]
            })

            # Verify initialization
            assert forecast.x == 100
            assert forecast.y == 200

            # Get forecast
            result = forecast.get_forecast()

            # Verify forecast data structure and content
            assert isinstance(result, dict)
            assert len(result) == 2  # Two time points
            assert '2024-01-15T00' in result
            assert '2024-01-15T06' in result
            assert result['2024-01-15T00']['T2'][0] == 15.5
            assert result['2024-01-15T06']['T2'][0] == 16.2

    @patch.object(MeteoForecast, '_connect_meteo_api_')
    def test_metadata_retrieval_workflow(self, mock_connect):
        """Test workflow for retrieving available models, grids, fields, and levels."""

        # Mock different API responses
        def mock_api_response(api_key, url):
            if url == MeteoForecast._base_url:
                return {'models': ['wrf', 'gfs']}
            if 'latlon2rowcol' in url:
                return {'points': [{'col': 100, 'row': 200}]}
            elif 'grid/' in url and not 'coordinates' in url:
                return {'grids': ['d01', 'd02_XLONG_XLAT']}
            elif 'field/' in url and not 'level' in url:
                return {'fields': ['T2', 'RAINNC', 'U10']}
            elif 'level/' in url:
                return {'levels': [0, 850, 500]}
            return {}

        mock_connect.side_effect = mock_api_response

        # Test complete metadata retrieval workflow
        models = MeteoForecast.available_models(self.api_key)
        assert models == ['wrf', 'gfs']

        grids = MeteoForecast.available_grids(self.api_key, 'wrf')
        assert grids == ['d01', 'd02_XLONG_XLAT']

        fields = MeteoForecast.available_fields(self.api_key, 'wrf', 'd02_XLONG_XLAT',
                                                self.latitude, self.longitude)
        assert fields == ['T2', 'RAINNC', 'U10']

        levels = MeteoForecast.available_levels(self.api_key, 'wrf', 'd02_XLONG_XLAT', 'T2',
                                                self.latitude, self.longitude)
        assert levels == [0, 850, 500]
