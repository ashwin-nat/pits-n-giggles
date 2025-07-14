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

import cProfile
import os
import random
import sys
import unittest

from colorama import init

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# from f1_types import (TestPacketCarDamageData, TestPacketCarMotionData,
#                       TestPacketCarSetupData, TestPacketCarStatusData,
#                       TestPacketCarTelemetryData, TestPacketEventData,
#                       TestPacketFinalClassificationData, TestPacketLapData,
#                       TestPacketLapPositionsData, TestPacketLobbyInfoData,
#                       TestPacketMotionExData, TestPacketParticipantsData,
#                       TestPacketSessionData, TestPacketSessionHistoryData,
#                       TestPacketTimeTrialData, TestPacketTyreSetsData,
#                       TestSessionType23, TestSessionType24)
# pylint: disable=unused-import wrong-import-position
# sourcery skip: dont-import-test-modules
from tests_base import CustomTestResult, F1TelemetryUnitTestsBase
from tests_version import TestIsUpdateAvailable
# from tests_collision_analyzer import (TestCollisionAnalyzer,
#                                       TestCollisionPairKey,
#                                       TestCollisionRecord)
# from tests_config import (TestCaptureSettings, TestConfigIO,
#                           TestDisplaySettings, TestEdgeCases, TestFilePathStr,
#                           TestForwardingSettings, TestHttpsSettings,
#                           TestLoadConfigFromIni, TestLoggingSettings,
#                           TestMissingSectionsAndKeys, TestNetworkSettings,
#                           TestPngSettings, TestPrivacySettings,
#                           TestSampleSettingsFixture)

# from tests_custom_markers import (TestCustomMarkerEntry,
#                                   TestCustomMarkersHistory)
# from tests_data_per_driver import (TestTyreSetHistoryEntry,
#                                    TestTyreSetHistoryManager, TestTyreSetInfo)
# from tests_debouncer import TestMultiButtonDebouncer
# from tests_fuel_recommender import (TestFuelRateRecommenderMisc,
#                                     TestFuelRateRecommenderRemove,
#                                     TestFuelRemainingPerLap)
# from tests_itc import TestAsyncInterTaskCommunicator
# from tests_overtake_analyzer import (TestOvertakeAnalyzerEmptyInput,
#                                      TestOvertakeAnalyzerFileCsv,
#                                      TestOvertakeAnalyzerInvalidData,
#                                      TestOvertakeAnalyzerListCsv,
#                                      TestOvertakeAnalyzerListObj)
# from tests_pcap import (FullPCapTests, TestF1PacketCaptureCompression,
#                         TestF1PacketCaptureHeader)
# from tests_pid_report import TestPidReport
# from tests_race_analyzer import TestGetFastestTimesJson
# from tests_tyre_wear_extrapolator import (
#     TestSimpleLinearRegression, TestTyreWearExtrapolator,
#     TestTyreWearExtrapolatorWithMissingLaps,
#     TestTyreWearExtrapolatorWithNonRacingLaps)
# from tests_udp_forwarder import TestAsyncUDPForwarder, TestUDPForwarder

# Initialize colorama
init(autoreset=True)

# ----------------------------------------------------------------------------------------------------------------------

def runTests():
    """
    Run all unit tests
    """
    random.seed()
    unittest.main(testRunner=unittest.TextTestRunner(resultclass=CustomTestResult))

if __name__ == '__main__':
    if '--profile' in sys.argv:
        cProfile.run('runTests()', sort='cumulative')
    else:
        runTests()
