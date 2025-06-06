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

import os
import sys

from pydantic import ValidationError

from lib.config import LoggingSettings

from .tests_config_base import TestF1ConfigBase

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



# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.config import ForwardingSettings

from .tests_config_base import TestF1ConfigBase

# ----------------------------------------------------------------------------------------------------------------------

class TestForwardingSettings(TestF1ConfigBase):
    """Test ForwardingSettings model and host:port validation"""

    def test_default_values(self):
        """Test default values"""
        settings = ForwardingSettings()
        self.assertEqual(settings.target_1, "")
        self.assertEqual(settings.target_2, "")
        self.assertEqual(settings.target_3, "")

    def test_valid_hostport_formats(self):
        """Test valid host:port formats"""
        valid_targets = [
            "localhost:8080",
            "127.0.0.1:3000",
            "example.com:80",
            "my-server.domain:65535",
            "192.168.1.1:443"
        ]

        for target in valid_targets:
            settings = ForwardingSettings(target_1=target)
            self.assertEqual(settings.target_1, target)

    def test_empty_targets_allowed(self):
        """Test that empty strings are allowed"""
        settings = ForwardingSettings(
            target_1="",
            target_2=" ",  # Should be stripped to empty
            target_3=None
        )
        self.assertEqual(settings.target_1, "")
        self.assertEqual(settings.target_2, "")
        self.assertEqual(settings.target_3, "")

    def test_invalid_hostport_formats(self):
        """Test invalid host:port formats raise ValidationError"""
        invalid_targets = [
            "localhost",  # No port
            ":8080",      # No host
            "localhost:",  # No port number
            "localhost:abc",  # Non-numeric port
            "localhost:0",    # Port out of range
            "localhost:65536", # Port out of range
            "localhost:8080:extra", # Extra components
            "local host:8080",  # Space in hostname
        ]

        for target in invalid_targets:
            with self.assertRaises(ValidationError):
                ForwardingSettings(target_1=target)

    def test_port_range_validation(self):
        """Test port number range validation"""
        with self.assertRaises(ValidationError):
            ForwardingSettings(target_1="localhost:0")

        with self.assertRaises(ValidationError):
            ForwardingSettings(target_1="localhost:65536")

        # Valid boundaries
        settings1 = ForwardingSettings(target_1="localhost:1")
        settings2 = ForwardingSettings(target_1="localhost:65535")
        self.assertEqual(settings1.target_1, "localhost:1")
        self.assertEqual(settings2.target_1, "localhost:65535")

    def test_empty_targets(self):
        f = ForwardingSettings(target_1="", target_2="", target_3="")
        self.assertEqual(f.forwarding_targets, [])

    def test_none_targets(self):
        f = ForwardingSettings(target_1=None, target_2=None, target_3=None)
        self.assertEqual(f.forwarding_targets, [])

    def test_single_valid_target(self):
        f = ForwardingSettings(target_1="localhost:8080")
        self.assertEqual(f.forwarding_targets, [("localhost", 8080)])

    def test_multiple_valid_targets(self):
        f = ForwardingSettings(
            target_1="host1.example.com:1234",
            target_2="192.168.1.10:65535",
            target_3="myhost:1"
        )
        expected = [
            ("host1.example.com", 1234),
            ("192.168.1.10", 65535),
            ("myhost", 1),
        ]
        self.assertEqual(f.forwarding_targets, expected)

    def test_invalid_hostport_format(self):
        with self.assertRaises(ValidationError):
            ForwardingSettings(target_1="noport")
        with self.assertRaises(ValidationError):
            ForwardingSettings(target_1="host:port:extra")
        with self.assertRaises(ValidationError):
            ForwardingSettings(target_1=":8080")
        with self.assertRaises(ValidationError):
            ForwardingSettings(target_1="host:")

    def test_port_out_of_range(self):
        with self.assertRaises(ValidationError):
            ForwardingSettings(target_1="host:0")
        with self.assertRaises(ValidationError):
            ForwardingSettings(target_1="host:70000")

    def test_port_non_numeric(self):
        with self.assertRaises(ValidationError):
            ForwardingSettings(target_1="host:notanumber")

    def test_whitespace_trimmed(self):
        settings = ForwardingSettings(target_1="  myhost.com:1234  ")
        self.assertEqual(settings.target_1, "myhost.com:1234")
