# MIT License
#
# Copyright (c) [2024] [Ashwin Natarajan]
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# pylint: skip-file

import unittest
import os
from tempfile import NamedTemporaryFile
from colorama import Fore, Style
import cProfile
import sys
import json

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from apps.lib.race_analyzer import getFastestTimesJson
from tests_base import F1TelemetryUnitTestsBase

class RaceAnalyzerUT(F1TelemetryUnitTestsBase):
    pass

class TestGetFastestTimesJson(RaceAnalyzerUT):

    def test_getFastestTimesJson(self):
        # Mock JSON data
        json_data = {
            "classification-data": [
                {
                    "session-history": {
                        "best-lap-time-lap-num": 3,
                        "best-sector-1-lap-num": 2,
                        "best-sector-2-lap-num": 2,
                        "best-sector-3-lap-num": 3,
                        "lap-history-data": [
                            {"lap-time-in-ms": 90000, "sector-1-time-in-ms": 20000, "sector-2-time-in-ms": 30000, "sector-3-time-in-ms": 40000},
                            {"lap-time-in-ms": 88000, "sector-1-time-in-ms": 19000, "sector-2-time-in-ms": 29000, "sector-3-time-in-ms": 39000},
                            {"lap-time-in-ms": 87000, "sector-1-time-in-ms": 19500, "sector-2-time-in-ms": 30500, "sector-3-time-in-ms": 38000}
                        ]
                    },
                    "index": 0,
                    "driver-name" : "HAMILTON",
                    "participant-data" : {
                        "team-id" : "Mercedes",
                        "telemetry-setting" : "Public"
                    }
                },
                {
                    "session-history": {
                        "best-lap-time-lap-num": 3,
                        "best-sector-1-lap-num": 3,
                        "best-sector-2-lap-num": 2,
                        "best-sector-3-lap-num": 3,
                        "lap-history-data": [
                            {"lap-time-in-ms": 92000, "sector-1-time-in-ms": 21000, "sector-2-time-in-ms": 32000, "sector-3-time-in-ms": 39000},
                            {"lap-time-in-ms": 89000, "sector-1-time-in-ms": 20000, "sector-2-time-in-ms": 30000, "sector-3-time-in-ms": 39000},
                            {"lap-time-in-ms": 88000, "sector-1-time-in-ms": 19500, "sector-2-time-in-ms": 31000, "sector-3-time-in-ms": 37500}
                        ]
                    },
                    "index": 1,
                    "driver-name" : "VERSTAPPEN",
                    "participant-data" : {
                        "team-id" : "Red Bull",
                        "telemetry-setting" : "Public"
                    }
                },
                {
                    "session-history": {
                        "best-lap-time-lap-num": 3,
                        "best-sector-1-lap-num": 2,
                        "best-sector-2-lap-num": 2,
                        "best-sector-3-lap-num": 3,
                        "lap-history-data": [
                            {"lap-time-in-ms": 91000, "sector-1-time-in-ms": 19000, "sector-2-time-in-ms": 31000, "sector-3-time-in-ms": 41000},
                            {"lap-time-in-ms": 90000, "sector-1-time-in-ms": 18000, "sector-2-time-in-ms": 30000, "sector-3-time-in-ms": 42000},
                            {"lap-time-in-ms": 89000, "sector-1-time-in-ms": 19500, "sector-2-time-in-ms": 32000, "sector-3-time-in-ms": 37550}
                        ]
                    },
                    "index": 2,
                    "driver-name" : "LECLERC",
                    "participant-data" : {
                        "team-id" : "Ferrari",
                        "telemetry-setting" : "Public"
                    }
                },
                {
                    "session-history": {
                        "best-lap-time-lap-num": 3,
                        "best-sector-1-lap-num": 3,
                        "best-sector-2-lap-num": 3,
                        "best-sector-3-lap-num": 1,
                        "lap-history-data": [
                            {"lap-time-in-ms": 93000, "sector-1-time-in-ms": 20000, "sector-2-time-in-ms": 33000, "sector-3-time-in-ms": 40000},
                            {"lap-time-in-ms": 92000, "sector-1-time-in-ms": 19500, "sector-2-time-in-ms": 32000, "sector-3-time-in-ms": 40500},
                            {"lap-time-in-ms": 91000, "sector-1-time-in-ms": 19000, "sector-2-time-in-ms": 31000, "sector-3-time-in-ms": 41000}
                        ]
                    },
                    "index": 3,
                    "driver-name" : "NORRIS",
                    "participant-data" : {
                        "team-id" : "McLaren",
                        "telemetry-setting" : "Public"
                    }
                },
                {
                    "session-history": {
                        "best-lap-time-lap-num": 3,
                        "best-sector-1-lap-num": 2,
                        "best-sector-2-lap-num": 3,
                        "best-sector-3-lap-num": 1,
                        "lap-history-data": [
                            {"lap-time-in-ms": 94000, "sector-1-time-in-ms": 21000, "sector-2-time-in-ms": 33000, "sector-3-time-in-ms": 40000},
                            {"lap-time-in-ms": 93000, "sector-1-time-in-ms": 20000, "sector-2-time-in-ms": 32000, "sector-3-time-in-ms": 41000},
                            {"lap-time-in-ms": 92000, "sector-1-time-in-ms": 20500, "sector-2-time-in-ms": 31000, "sector-3-time-in-ms": 40500}
                        ]
                    },
                    "index": 4,
                    "driver-name" : "ALONSO",
                    "participant-data" : {
                        "team-id" : "Aston Martin",
                        "telemetry-setting" : "Public"
                    }
                }
            ]
        }

        expected_result = {
            'lap': {
                'driver-index': 0,
                'driver-name' : 'HAMILTON',
                'team-id' : 'Mercedes',
                'lap-number': 3,
                'time': 87000,
                'time-str': '01:27.000'
            },
            's1': {
                'driver-index': 2,
                'driver-name' : 'LECLERC',
                'team-id' : 'Ferrari',
                'lap-number': 2,
                'time': 18000,
                'time-str': '18.000'
            },
            's2': {
                'driver-index': 0,
                'driver-name' : 'HAMILTON',
                'team-id' : 'Mercedes',
                'lap-number': 2,
                'time': 29000,
                'time-str': '29.000'
            },
            's3': {
                'driver-index': 1,
                'driver-name' : 'VERSTAPPEN',
                'team-id' : 'Red Bull',
                'lap-number': 3,
                'time': 37500,
                'time-str': '37.500'
            }
        }

        result = getFastestTimesJson(json_data)
        self.assertEqual(result['s1'], expected_result['s1'])
        self.assertEqual(result['s2'], expected_result['s2'])
        self.assertEqual(result['s3'], expected_result['s3'])
        self.assertEqual(result['lap'], expected_result['lap'])
        self.assertEqual(result, expected_result)
