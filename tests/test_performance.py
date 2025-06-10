"""
Copyright (c) 2025 Piotr Gawron (dev@gawron.biz)
This file is licensed under the MIT License.
For details, see the LICENSE file in the project root.

Performance tests for MeteoForecast class.
"""

import time
from unittest.mock import patch, Mock
import pytest
from meteo_forecast.meteo_forecast import MeteoForecast


class TestMeteoForecastPerformance:
    """Performance tests for MeteoForecast class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.api_key = "test_api_key"
        self.latitude = 52.2297
        self.longitude = 21.0122

    @patch('meteo_forecast.meteo_forecast.requests.get')
    @patch('meteo_forecast.meteo_forecast.requests.post')
    def test_forecast_response_time(self, mock_post, mock_get):
        """Test that forecast retrieval completes within acceptable time."""
        # Mock fast API responses
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
            from datetime import datetime
            import pytz
            mock_datetime.now.return_value = datetime(2024, 1, 15, 12, 0, 0, tzinfo=pytz.UTC)
            mock_datetime.strptime = datetime.strptime
            
            start_time = time.time()
            
            forecast = MeteoForecast(self.api_key, self.latitude, self.longitude)
            result = forecast.get_forecast()
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Should complete within 1 second (mocked responses)
            assert execution_time < 1.0
            assert len(result) > 0

    @patch('meteo_forecast.meteo_forecast.requests.get')
    def test_multiple_instances_performance(self, mock_get):
        """Test performance with multiple MeteoForecast instances."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'points': [{'col': 100, 'row': 200}]}
        mock_get.return_value = mock_response
        
        start_time = time.time()
        
        # Create multiple instances
        instances = []
        for i in range(10):
            lat = 52.0 + i * 0.1
            lon = 21.0 + i * 0.1
            instance = MeteoForecast(self.api_key, lat, lon)
            instances.append(instance)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should create 10 instances within reasonable time
        assert execution_time < 2.0
        assert len(instances) == 10
        
        # Verify all instances are properly initialized
        for i, instance in enumerate(instances):
            assert instance.lat == 52.0 + i * 0.1
            assert instance.lon == 21.0 + i * 0.1

    @patch.object(MeteoForecast, '_connect_meteo_api_')
    def test_large_field_list_performance(self, mock_connect):
        """Test performance with large number of fields."""
        mock_connect.return_value = {'points': [{'col': 100, 'row': 200}]}
        
        # Create config with many fields
        large_config = {
            'model': 'wrf',
            'grid': 'd02_XLONG_XLAT',
            'fields': [(f'FIELD_{i}', 0) for i in range(50)]
        }
        
        start_time = time.time()
        
        with patch.object(MeteoForecast, '_set_xy'):
            forecast = MeteoForecast(self.api_key, self.latitude, self.longitude, large_config)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should handle large config efficiently
        assert execution_time < 1.0
        assert len(forecast.config['fields']) == 50

    @pytest.mark.slow
    @patch('meteo_forecast.meteo_forecast.requests.get')
    @patch('meteo_forecast.meteo_forecast.requests.post')
    def test_stress_forecast_retrieval(self, mock_post, mock_get):
        """Stress test for multiple forecast retrievals."""
        # Mock responses
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
            return response
        
        def mock_post_response(url, headers=None):
            response = Mock()
            response.status_code = 200
            response.json.return_value = {
                'times': ['2024-01-15T00'],
                'data': [15.5]
            }
            return response
        
        mock_get.side_effect = mock_get_response
        mock_post.side_effect = mock_post_response
        
        with patch('meteo_forecast.meteo_forecast.datetime') as mock_datetime:
            from datetime import datetime
            import pytz
            mock_datetime.now.return_value = datetime(2024, 1, 15, 12, 0, 0, tzinfo=pytz.UTC)
            mock_datetime.strptime = datetime.strptime
            
            forecast = MeteoForecast(self.api_key, self.latitude, self.longitude)
            
            start_time = time.time()
            
            # Perform multiple forecast retrievals
            results = []
            for _ in range(20):
                result = forecast.get_forecast()
                results.append(result)
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Should complete 20 retrievals within reasonable time
            assert execution_time < 10.0
            assert len(results) == 20
            
            # Verify all results are valid
            for result in results:
                assert isinstance(result, dict)
                assert len(result) > 0