"""
Copyright (c) 2025 Piotr Gawron (dev@gawron.biz)
This file is licensed under the MIT License.
For details, see the LICENSE file in the project root.

Edge cases tests for MeteoForecast class.
"""

# pylint: disable=protected-access

from unittest.mock import patch

import pytest

from meteo_forecast.meteo_forecast import MeteoForecast
from tests.base_test import BaseTest


class TestMeteoForecastEdgeCases(BaseTest):
    """Test edge cases and boundary conditions."""

    def test_extreme_coordinates(self):
        """Test with extreme latitude/longitude values."""
        with patch.object(MeteoForecast, '_set_xy'):
            # Test extreme valid coordinates
            forecast_north = MeteoForecast(self.api_key, 89.9, 179.9)
            assert forecast_north.lat == 89.9
            assert forecast_north.lon == 179.9

            forecast_south = MeteoForecast(self.api_key, -89.9, -179.9)
            assert forecast_south.lat == -89.9
            assert forecast_south.lon == -179.9

    def test_empty_config_fields(self):
        """Test with empty fields configuration."""
        config = {
            'model': 'wrf',
            'grid': 'd02_XLONG_XLAT',
            'fields': []
        }

        with patch.object(MeteoForecast, '_set_xy'):
            with pytest.raises(ValueError, match="Fields cannot be empty"):
                MeteoForecast(self.api_key, 52.0, 21.0, config)

    def test_invalid_config(self):
        """Test with invalid configuration."""
        # Missing required keys
        with patch.object(MeteoForecast, '_set_xy'):
            with pytest.raises(ValueError, match='Configuration must have "model" key'):
                MeteoForecast(self.api_key, 52.0, 21.0, {'grid': 'test', 'fields': [('T2', 0)]})

            with pytest.raises(ValueError, match='Configuration must have "grid" key'):
                MeteoForecast(self.api_key, 52.0, 21.0, {'model': 'test', 'fields': [('T2', 0)]})

            # Wrong types
            with pytest.raises(ValueError, match='Configuration "model" must be of type str'):
                MeteoForecast(self.api_key, 52.0, 21.0, {'model': 123, 'grid': 'test', 'fields': [('T2', 0)]})

            with pytest.raises(ValueError, match='Each field in "fields" must be a tuple'):
                MeteoForecast(self.api_key, 52.0, 21.0, {'model': 'wrf', 'grid': 'test', 'fields': ['invalid']})

            with pytest.raises(ValueError, match='Each field in "fields" must be a tuple'):
                MeteoForecast(self.api_key, 52.0, 21.0, {'model': 'wrf', 'grid': 'test', 'fields': [('T2', 'invalid')]})

    def test_date_parsing_edge_cases(self):
        """Test date parsing with various formats."""
        # Test with different date formats
        date_dict_1 = {
            'starting-date': '2024-12-31T23',
            'interval': 1,
            'count': 2
        }

        result = MeteoForecast._get_forecast_dates(date_dict_1)
        assert result == ['2024-12-31T23', '2025-01-01T00']

        # Test with leap year
        date_dict_2 = {
            'starting-date': '2024-02-28T12',
            'interval': 24,
            'count': 2
        }

        result = MeteoForecast._get_forecast_dates(date_dict_2)
        assert result == ['2024-02-28T12', '2024-02-29T12']
