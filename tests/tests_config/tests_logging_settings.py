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

from lib.config import LoggingSettings

from .tests_config_base import TestF1ConfigBase

# ----------------------------------------------------------------------------------------------------------------------

class TestLoggingSettings(TestF1ConfigBase):
    """Test LoggingSettings model"""

    def test_default_values(self):
        """Test default values"""
        settings = LoggingSettings()
        self.assertEqual(settings.log_file, "png.log")
        self.assertEqual(settings.log_file_size, 1_000_000)

    def test_log_file_size_validation(self):
        """Test valid and invalid log_file_size values"""
        # Valid value
        valid_size = 500_000
        logging_settings = LoggingSettings(log_file_size=valid_size)
        self.assertEqual(logging_settings.log_file_size, valid_size)

        # Invalid values: zero and negative
        for invalid_size in (0, -1, -100):
            with self.assertRaises(ValidationError):
                LoggingSettings(log_file_size=invalid_size)

    def test_log_file_path_validation(self):
        """Test that only bare file names are allowed for log_file"""

        # Valid filename
        settings = LoggingSettings(log_file="app.log")
        self.assertEqual(settings.log_file, "app.log")

        # Directory components should raise
        for invalid_path in ("logs/app.log", "logs\\app.log", "/var/log/app.log", "C:\\logs\\app.log"):
            with self.assertRaises(ValidationError, msg=f"Expected ValidationError for path: {invalid_path}"):
                LoggingSettings(log_file=invalid_path)

        # Empty or whitespace-only strings should raise
        for bad in ("", "   "):
            with self.assertRaises(ValidationError):
                LoggingSettings(log_file=bad)

        # Leading/trailing spaces should be stripped and accepted if valid
        settings = LoggingSettings(log_file="  app.log  ")
        self.assertEqual(settings.log_file, "app.log")
