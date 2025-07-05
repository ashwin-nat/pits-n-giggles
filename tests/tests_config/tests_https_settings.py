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
import tempfile

from pydantic import ValidationError

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.config import HttpsSettings

from .tests_config_base import TestF1ConfigBase

# ----------------------------------------------------------------------------------------------------------------------

class TestHttpsSettings(TestF1ConfigBase):
    """Test HttpsSettings model validation and defaults"""

    def test_default_values(self):
        """Test that default values are set correctly"""
        settings = HttpsSettings()
        self.assertFalse(settings.enabled)
        self.assertEqual("", settings.key_file_path)
        self.assertEqual("", settings.cert_file_path)
        self.assertEqual("http", settings.proto)

    def test_enabled_without_key_should_fail(self):
        """HTTPS enabled without key should raise appropriate error"""
        with self.assertRaises(ValueError) as ctx:
            HttpsSettings(enabled=True, cert_file_path="some/cert.pem")
        self.assertIn("Key file is required", str(ctx.exception))

    def test_enabled_without_cert_should_fail(self):
        """HTTPS enabled without cert should raise appropriate error"""
        # Create a temp file for key to avoid key-related failure
        with tempfile.NamedTemporaryFile(delete=False) as key_file:
            key_path = key_file.name

        try:
            with self.assertRaises(ValueError) as ctx:
                HttpsSettings(enabled=True, key_file_path=key_path)
            self.assertIn("Certificate file is required", str(ctx.exception))
        finally:
            os.unlink(key_path)

    def test_files_provided_but_https_disabled(self):
        """Supplying file paths is allowed even if HTTPS is off"""
        settings = HttpsSettings(
            enabled=False,
            key_file_path="/path/to/key",
            cert_file_path="/path/to/cert"
        )
        self.assertFalse(settings.enabled)
        self.assertEqual(str(settings.key_file_path), "/path/to/key")
        self.assertEqual(str(settings.cert_file_path), "/path/to/cert")
        self.assertEqual("http", settings.proto)

    def test_valid_file_paths_when_enabled(self):
        """HTTPS enabled with valid cert/key file paths should pass"""
        with tempfile.NamedTemporaryFile(delete=False) as key_file, \
             tempfile.NamedTemporaryFile(delete=False) as cert_file:

            key_path = key_file.name
            cert_path = cert_file.name

        try:
            settings = HttpsSettings(
                enabled=True,
                key_file_path=key_path,
                cert_file_path=cert_path
            )
            self.assertTrue(settings.enabled)
            self.assertEqual(str(settings.key_file_path), key_path)
            self.assertEqual(str(settings.cert_file_path), cert_path)
            self.assertEqual("https", settings.proto)
        finally:
            os.unlink(key_path)
            os.unlink(cert_path)

    def test_nonexistent_file_paths_should_fail_validation(self):
        """Should raise if HTTPS is enabled but paths do not exist"""
        with self.assertRaises(ValueError) as ctx:
            HttpsSettings(
                enabled=True,
                key_file_path="/non/existent/key.pem",
                cert_file_path="/non/existent/cert.pem",
            )
        error_msg = str(ctx.exception)
        self.assertIn("Key file is required", error_msg)
