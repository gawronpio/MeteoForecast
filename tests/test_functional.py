"""
Copyright (c) 2025 Piotr Gawron (dev@gawron.biz)
This file is licensed under the MIT License.
For details, see the LICENSE file in the project root.

Functional tests for MeteoForecast class.
"""

from unittest.mock import patch

from meteo_forecast.meteo_forecast import MeteoForecast
from tests.base_test import BaseTest
from tests.mocks import get_mock_get_response, get_mock_post_response


class TestMeteoForecastFunctional(BaseTest):
    """Functional tests for MeteoForecast class - testing complete workflows."""

    @patch('requests.get')
    @patch('requests.post')
    def test_complete_forecast_workflow(self, mock_post, mock_get):
        """Test complete workflow from initialization to forecast retrieval."""
        mock_get.side_effect = get_mock_get_response()
        mock_post.side_effect = get_mock_post_response()

        # Initialize forecast object
        forecast = MeteoForecast(self.api_key, self.latitude, self.longitude, {
            'model': 'wrf',
            'grid': 'd02_XLONG_XLAT',
            'fields': [('T2', 0)]
        })

        # Verify initialization
        assert forecast.x == 150
        assert forecast.y == 250

        # Get forecast
        result = forecast.get_forecast()

        # Verify forecast data structure and content
        assert isinstance(result, dict)
        assert len(result) == 3

    @patch.object(MeteoForecast, '_connect_meteo_api_')
    def test_metadata_retrieval_workflow(self, mock_connect):
        """Test workflow for retrieving available models, grids, fields, and levels."""

        # Mock different API responses
        def mock_api_response(api_key, url):  # pylint: disable=unused-argument
            if url == MeteoForecast.base_url:
                return {'models': ['wrf', 'gfs']}
            if 'latlon2rowcol' in url:
                return {'points': [{'col': 100, 'row': 200}]}
            if 'grid/' in url and 'coordinates' not in url:
                return {'grids': ['d01', 'd02_XLONG_XLAT']}
            if 'field/' in url and 'level' not in url:
                return {'fields': ['T2', 'RAINNC', 'U10']}
            if 'level/' in url:
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
