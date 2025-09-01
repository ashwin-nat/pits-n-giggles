# ----------------------------------------------------------------------------------------------------------------------
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

import os
import sys

from pydantic import ValidationError
# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.config import (CaptureSettings, DisplaySettings, ForwardingSettings,
                        LoggingSettings, NetworkSettings, PngSettings,
                        PrivacySettings, StreamOverlaySettings)

from .tests_config_base import TestF1ConfigBase

# ----------------------------------------------------------------------------------------------------------------------

class TestPngSettings(TestF1ConfigBase):
    """Test the main PngSettings model"""

    def test_complete_model_creation(self):
        """Test creating a complete PngSettings model"""
        settings = PngSettings(
            Network=NetworkSettings(),
            Capture=CaptureSettings(),
            Display=DisplaySettings(),
            Logging=LoggingSettings(),
            Privacy=PrivacySettings(),
            Forwarding=ForwardingSettings(),
            StreamOverlay=StreamOverlaySettings(),
        )

        self.assertIsInstance(settings.Network, NetworkSettings)
        self.assertIsInstance(settings.Capture, CaptureSettings)
        self.assertIsInstance(settings.Display, DisplaySettings)
        self.assertIsInstance(settings.Logging, LoggingSettings)
        self.assertIsInstance(settings.Privacy, PrivacySettings)
        self.assertIsInstance(settings.Forwarding, ForwardingSettings)

    def test_nested_validation(self):
        """Test that nested model validation works"""
        with self.assertRaises(ValidationError):
            PngSettings(
                Network=NetworkSettings(telemetry_port=-1),  # Invalid
                Capture=CaptureSettings(),
                Display=DisplaySettings(),
                Logging=LoggingSettings(),
                Privacy=PrivacySettings(),
                Forwarding=ForwardingSettings()
            )
