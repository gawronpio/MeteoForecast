"""
Copyright (c) 2025 Piotr Gawron (dev@gawron.biz)
This file is licensed under the MIT License.
For details, see the LICENSE file in the project root.

Mocks for MeteoForecast class tests.
"""


import re
from datetime import datetime, timedelta
from typing import Callable
from unittest.mock import Mock

import pytz


def get_times_nad_vals() -> dict:
    """
    Return dictionary with times and values for testing.

    :return: Dictionary with times and values
    :type: dict
    """
    now = datetime.now(pytz.UTC).replace(hour=0, minute=0, second=0, microsecond=0)

    return {
        'times': [
            now + timedelta(hours=6),
            now + timedelta(hours=12),
            now + timedelta(hours=18),
        ],
        'vals': {
            'TSK': [25.0, 24.5, 25.2],
            'T2': [20.5, 31.2, 19.8],
            'RAINNC': [0.0, 0.5, 1.2],
            'SNOWNC': [0.0, 0.3, 0.6],
            'HAILNC': [0.0, 0.2, 0.3],
            'U10': [3.5, 4.2, 2.8],
            'V10': [2.8, 3.1, 2.6],
            'WSPD10MAX': [10.0, 11.5, 12.0],
            'SWDOWN': [1000, 1100, 1200],
            'PSFC': [101325, 101280, 101350],
        }
    }


def get_mock_get_response(old: bool = False) -> Callable:
    """
    Return response.get mock.

    :param old: True if old dates are used, False otherwise
    :type old: bool

    :return: Mock function
    :rtype: Callable
    """
    now = datetime.now(pytz.UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    if old:
        now -= timedelta(days=20)

    def mock_get_response(url, *args, **kwargs):  # pylint: disable=unused-argument
        response = Mock()
        response.status_code = 200

        if 'latlon2rowcol' in url:
            response.json.return_value = {'points': [{'col': 150, 'row': 250}]}
        elif 'date/' in url:
            date_format = '%Y-%m-%dT%H'
            interval_1 = 24
            count_1 = 141
            interval_2 = 48
            count_2 = 3
            date_1 = (now - timedelta(hours=interval_1 * count_1)).strftime(date_format)
            date_2 = now.strftime(date_format)
            response.json.return_value = {
                'dates': [
                    {
                        'starting-date': date_1,
                        'interval': interval_1,
                        'count': count_1,
                    },
                    {
                        'starting-date': date_2,
                        'interval': interval_2,
                        'count': count_2,
                    }
                ]
            }
        return response
    return mock_get_response


def get_mock_post_response(times_and_vals: dict = None) -> Callable:
    """
        Return response.post mock.

        :return: Mock function
        :rtype: Callable
        """
    if times_and_vals is None:
        times_and_vals = get_times_nad_vals()

    def mock_post_response(url, *args, **kwargs):  # pylint: disable=unused-argument
        response = Mock()
        response.status_code = 200

        match = re.search(r"/field/([^/]+)/", url)
        if not match:
            return None

        field = match.group(1)

        try:
            response.json.return_value = {
                'times': times_and_vals['times'],
                'data': times_and_vals['vals'][field],
            }
        except Exception as e:
            raise NotImplementedError(f"Unsupported field in url: {url}") from e
        return response
    return mock_post_response
