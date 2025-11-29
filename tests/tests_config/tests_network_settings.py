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

from lib.config import NetworkSettings

from .tests_config_base import TestF1ConfigBase

# ----------------------------------------------------------------------------------------------------------------------

class TestNetworkSettings(TestF1ConfigBase):
    """Test NetworkSettings model validation and defaults"""

    def test_default_values(self):
        """Test that default values are set correctly"""
        settings = NetworkSettings()
        self.assertEqual(settings.telemetry_port, 20777)
        self.assertEqual(settings.server_port, 4768)
        self.assertEqual(settings.save_viewer_port, 4769)
        self.assertEqual(settings.udp_tyre_delta_action_code, None)
        self.assertEqual(settings.udp_custom_action_code, None)
        self.assertEqual(settings.wdt_interval_sec, 30)

    def test_invalid_port_ranges(self):
        """Test that invalid port numbers raise ValidationError"""
        with self.assertRaises(ValidationError):
            NetworkSettings(telemetry_port=-1)

        with self.assertRaises(ValidationError):
            NetworkSettings(server_port=65536)

    def test_action_code_validation(self):
        """Test UDP action code validation"""
        # Valid range
        settings = NetworkSettings(
            udp_tyre_delta_action_code=1,
            udp_custom_action_code=12
        )
        self.assertEqual(settings.udp_tyre_delta_action_code, 1)
        self.assertEqual(settings.udp_custom_action_code, 12)

        # Invalid range
        with self.assertRaises(ValidationError):
            NetworkSettings(udp_tyre_delta_action_code=0)

        with self.assertRaises(ValidationError):
            NetworkSettings(udp_custom_action_code=13)

    def test_valid_port_ranges(self):
        net = NetworkSettings(
            telemetry_port=0,
            server_port=65535,
            save_viewer_port=12345,
            udp_tyre_delta_action_code=1,
            udp_custom_action_code=12,
            wdt_interval_sec=45
        )
        self.assertEqual(net.telemetry_port, 0)
        self.assertEqual(net.server_port, 65535)
        self.assertEqual(net.save_viewer_port, 12345)
        self.assertEqual(net.udp_tyre_delta_action_code, 1)
        self.assertEqual(net.udp_custom_action_code, 12)
        self.assertEqual(net.wdt_interval_sec, 45)

    def test_invalid_telemetry_port(self):
        with self.assertRaises(ValidationError):
            NetworkSettings(telemetry_port=-1)
        with self.assertRaises(ValidationError):
            NetworkSettings(telemetry_port=70000)

    def test_invalid_server_port(self):
        with self.assertRaises(ValidationError):
            NetworkSettings(server_port=-1)
        with self.assertRaises(ValidationError):
            NetworkSettings(server_port=70000)

    def test_invalid_save_viewer_port(self):
        with self.assertRaises(ValidationError):
            NetworkSettings(save_viewer_port=-5)
        with self.assertRaises(ValidationError):
            NetworkSettings(save_viewer_port=70000)

    def test_invalid_udp_tyre_delta_action_code(self):
        with self.assertRaises(ValidationError):
            NetworkSettings(udp_tyre_delta_action_code=0)
        with self.assertRaises(ValidationError):
            NetworkSettings(udp_tyre_delta_action_code=13)

    def test_invalid_udp_custom_action_code(self):
        with self.assertRaises(ValidationError):
            NetworkSettings(udp_custom_action_code=0)
        with self.assertRaises(ValidationError):
            NetworkSettings(udp_custom_action_code=13)

    def test_server_and_save_viewer_ports_must_differ(self):
        """Test that server_port and save_viewer_port cannot be the same"""
        with self.assertRaises(ValidationError) as ctx:
            NetworkSettings(server_port=5000, save_viewer_port=5000)
        self.assertIn("must not be the same", str(ctx.exception))

    def test_udp_action_codes_must_differ(self):
        """Test that tyre and custom UDP action codes cannot be the same"""
        with self.assertRaises(ValidationError) as ctx:
            NetworkSettings(udp_tyre_delta_action_code=5, udp_custom_action_code=5)
        self.assertIn("must not be the same", str(ctx.exception))

    def test_wdt_interval_sec_invalid_type(self):
        with self.assertRaises(ValidationError):
            NetworkSettings(wdt_interval_sec="cat")

    def test_wdt_interval_sec_invalid_range(self):
        with self.assertRaises(ValidationError):
            NetworkSettings(wdt_interval_sec=0)
        with self.assertRaises(ValidationError):
            NetworkSettings(wdt_interval_sec=121)
