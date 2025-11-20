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
                        NetworkSettings, PngSettings, HttpsSettings, HudSettings,
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
            Privacy=PrivacySettings(),
            Forwarding=ForwardingSettings(),
            StreamOverlay=StreamOverlaySettings(),
            HTTPS=HttpsSettings(),
            HUD=HudSettings(),
        )

        self.assertIsInstance(settings.Network, NetworkSettings)
        self.assertIsInstance(settings.Capture, CaptureSettings)
        self.assertIsInstance(settings.Display, DisplaySettings)
        self.assertIsInstance(settings.Privacy, PrivacySettings)
        self.assertIsInstance(settings.Forwarding, ForwardingSettings)

    def test_nested_validation(self):
        """Test that nested model validation works"""
        with self.assertRaises(ValidationError):
            PngSettings(
                Network=NetworkSettings(telemetry_port=-1),  # Invalid
                Capture=CaptureSettings(),
                Display=DisplaySettings(),
                Privacy=PrivacySettings(),
                Forwarding=ForwardingSettings()
            )

    def test_udp_action_code(self):
        """Test UDP action code validation across areas of the model"""

        with self.assertRaises(ValidationError):
            PngSettings(
                Network=NetworkSettings(udp_tyre_delta_action_code=0),
                HUD=HudSettings(toggle_overlays_udp_action_code=0)
            )

        with self.assertRaises(ValidationError):
            PngSettings(
                Network=NetworkSettings(udp_custom_action_code=0),
                HUD=HudSettings(toggle_overlays_udp_action_code=0)
            )
    def test_diff_top_level(self):
        """Test the diff method"""
        settings1 = PngSettings(
            Network=NetworkSettings(),
            Capture=CaptureSettings(),
            Display=DisplaySettings(),
            Privacy=PrivacySettings(),
            Forwarding=ForwardingSettings(),
            StreamOverlay=StreamOverlaySettings(),
        )

        settings2 = PngSettings(
            Network=NetworkSettings(),
            Capture=CaptureSettings(),
            Display=DisplaySettings(),
            Privacy=PrivacySettings(),
            Forwarding=ForwardingSettings(),
            StreamOverlay=StreamOverlaySettings(),
        )

        settings3 = PngSettings(
            Network=NetworkSettings(server_port=12345),
            Capture=CaptureSettings(),
            Display=DisplaySettings(refresh_interval=1000),
            Privacy=PrivacySettings(),
            Forwarding=ForwardingSettings(),
            StreamOverlay=StreamOverlaySettings(),
        )

        self.assertFalse(settings1.has_changed(settings2))
        self.assertEqual(settings1.diff(settings2), {})
        self.assertTrue(settings1.has_changed(settings3))
        self.assertEqual(settings1.diff(settings3),
            {
                "Network" : {
                    "server_port" : {
                        "old_value" : 4768,
                        "new_value" : 12345
                    }
                },
                "Display" : {
                    "refresh_interval" : {
                        "old_value" : 200,
                        "new_value" : 1000
                    }
                }
            })

        # Interested in a full container diff
        self.assertEqual(settings1.diff(settings3, {"Network": [], "Display": []}),
            {
                "Network" : {
                    "server_port" : {
                        "old_value" : 4768,
                        "new_value" : 12345
                    }
                },
                "Display" : {
                    "refresh_interval" : {
                        "old_value" : 200,
                        "new_value" : 1000
                    }
                }
            })

    def test_diff_container_level(self):
        """Test the diff method"""
        settings1 = CaptureSettings()
        settings2 = CaptureSettings()
        settings3 = CaptureSettings(save_race_ctrl_msg=True)

        self.assertFalse(settings1.has_changed(settings2))
        self.assertEqual(settings1.diff(settings2), {})
        self.assertTrue(settings1.has_changed(settings3))
        self.assertEqual(settings1.diff(settings3), {"save_race_ctrl_msg" : {"old_value" : False, "new_value" : True}})
