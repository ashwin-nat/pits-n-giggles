# MIT License
#
# Copyright (c) [2025] [Ashwin Natarajan]
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

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

from .tests_capture_settings import TestCaptureSettings
from .tests_config_edge import (TestEdgeCases, TestMissingSectionsAndKeys,
                                TestSampleSettingsFixture)
from .tests_config_io import TestConfigIO, TestLoadConfigFromIni
from .tests_display_settings import TestDisplaySettings
from .tests_forwarding_settings import TestForwardingSettings
from .tests_logging_settings import TestLoggingSettings
from .tests_network_settings import TestNetworkSettings
from .tests_png_settings import TestPngSettings
from .tests_privacy_settings import TestPrivacySettings
from .tests_https_settings import TestHttpsSettings

# -------------------------------------- EXPORTS -----------------------------------------------------------------------

__all__ = [
    "TestCaptureSettings",
    "TestEdgeCases",
    "TestMissingSectionsAndKeys",
    "TestSampleSettingsFixture",
    "TestConfigIO",
    "TestLoadConfigFromIni",
    "TestDisplaySettings",
    "TestForwardingSettings",
    "TestLoggingSettings",
    "TestNetworkSettings",
    "TestPngSettings",
    "TestPrivacySettings",
    "TestHttpsSettings",
]