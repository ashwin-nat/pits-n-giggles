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

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pydantic import ValidationError

from lib.config import McpSettings
from lib.config.schema.hud.mfd import DEFAULT_PAGES

from .tests_config_base import TestF1ConfigBase

# ----------------------------------------------------------------------------------------------------------------------

class TestMcpSettings(TestF1ConfigBase):
    """Test LoggingSettings model"""

    def test_default_values(self):
        """Test default values"""
        settings = McpSettings()
        self.assertEqual(settings.mcp_http_server_enable, False)
        self.assertEqual(settings.mcp_http_port, 4770)
        # MFD pages has its own test case because the structure is a bit more complex

    def test_enabled_validation(self):
        """Test valid and invalid mcp_http_server_enable values"""
        # Valid value
        enabled = True
        mcp_settings = McpSettings(mcp_http_server_enable=enabled)
        self.assertEqual(mcp_settings.mcp_http_server_enable, enabled)

        with self.assertRaises(ValidationError):
            McpSettings(mcp_http_server_enable=None)  # type: ignore

        with self.assertRaises(ValidationError):
            McpSettings(mcp_http_server_enable="invalid")

        with self.assertRaises(ValidationError):
            McpSettings(mcp_http_server_enable=420)

    def test_mcp_port_validation(self):
        """Test valid and invalid mcp_http_port values"""
        # Valid value
        port = 5000
        mcp_settings = McpSettings(mcp_http_port=port)
        self.assertEqual(mcp_settings.mcp_http_port, port)

        with self.assertRaises(ValidationError):
            McpSettings(mcp_http_port=0)  # type: ignore

        with self.assertRaises(ValidationError):
            McpSettings(mcp_http_port=70000)  # type: ignore

        with self.assertRaises(ValidationError):
            McpSettings(mcp_http_port=-1)  # type: ignore

        with self.assertRaises(ValidationError):
            McpSettings(mcp_http_port="invalid")  # type: ignore
