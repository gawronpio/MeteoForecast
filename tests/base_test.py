"""
Copyright (c) 2025 Piotr Gawron (dev@gawron.biz)
This file is licensed under the MIT License.
For details, see the LICENSE file in the project root.

BaseTest class for MeteoForecast class.
"""


# pylint: disable=too-few-public-methods

class BaseTest:
    """Base test class to support common code"""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # pylint: disable=attribute-defined-outside-init
        self.api_key = "test_api_key"
        self.latitude = 52.2297
        self.longitude = 21.0122
        self.test_config = {
            'model': 'wrf',
            'grid': 'd01_XLONG_XLAT',
            'fields': [('T2', 0), ('RAINNC', 0)]
        }
