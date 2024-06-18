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
import cProfile
import sys

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.overtake_analyzer import OvertakeAnalyzer, OvertakeAnalyzerMode, OvertakeRecord, OvertakeRivalryKey
from lib.race_analyzer import getFastestTimesJson

from tests_base import F1TelemetryUnitTestsBase, CustomTestResult
from tests_pcap import FullPCapTests, TestF1PacketCaptureHeader
from tests_overtake_analyzer import \
    TestOvertakeAnalyzerListObj, \
    TestOvertakeAnalyzerFileCsv, \
    TestOvertakeAnalyzerListCsv, \
    TestOvertakeAnalyzerEmptyInput, \
    TestOvertakeAnalyzerInvalidData
from tests_race_analyzer import TestGetFastestTimesJson

# Initialize colorama
from colorama import init
init(autoreset=True)

# ----------------------------------------------------------------------------------------------------------------------

def runTests():
    unittest.main(testRunner=unittest.TextTestRunner(resultclass=CustomTestResult))

if __name__ == '__main__':
    if '--profile' in sys.argv:
        cProfile.run('runTests()', sort='cumulative')
    else:
        runTests()