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

import json
import os
import sys
from unittest.mock import patch, Mock
from requests.exceptions import RequestException

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.version import get_version, is_update_available

from tests_base import F1TelemetryUnitTestsBase

# ----------------------------------------------------------------------------------------------------------------------

class TestIsUpdateAvailable(F1TelemetryUnitTestsBase):
    @patch("lib.version.requests.get")
    def test_update_available(self, mock_get):
        fake_rsp = [
            {"tag_name": "v2.0.0", "prerelease": False}
        ]
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = fake_rsp
        self.assertTrue(is_update_available("1.2.3", fake_rsp))

    @patch("lib.version.requests.get")
    def test_no_update_available(self, mock_get):
        fake_rsp = [
            {"tag_name": "v1.2.3", "prerelease": False}
        ]
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = fake_rsp
        self.assertFalse(is_update_available("1.2.3", fake_rsp))

    @patch("lib.version.requests.get")
    def test_skips_prereleases(self, mock_get):
        fake_rsp = [
            {"tag_name": "v2.0.0-beta", "prerelease": True},
            {"tag_name": "v1.2.3", "prerelease": False}
        ]
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = fake_rsp
        self.assertFalse(is_update_available("1.2.3", fake_rsp))

    @patch("lib.version.requests.get")
    def test_handles_missing_tag_name(self, mock_get):
        fake_rsp = [
            {"tag_name": "", "prerelease": False},
            {"prerelease": False},
            {"tag_name": "v1.2.3", "prerelease": False}
        ]
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = fake_rsp
        self.assertFalse(is_update_available("1.2.3", fake_rsp))

    @patch("lib.version.requests.get")
    def test_network_error_returns_false(self, mock_get):
        mock_get.side_effect = RequestException("Network error")
        self.assertFalse(is_update_available("1.2.3", []))

    @patch("lib.version.requests.get")
    def test_older_release_uploaded_later_returns_false_due_to_order(self, mock_get):
        # Tests the caveat: even though 1.0.0 is older, it's listed first
        fake_rsp = [
            {"tag_name": "v1.0.0", "prerelease": False},
            {"tag_name": "v2.0.0", "prerelease": False}
        ]
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = fake_rsp
        self.assertFalse(is_update_available("2.0.0", fake_rsp))

    @patch("lib.version.requests.get")  # replace with your actual module path
    def test_invalid_version_string_returns_false(self, mock_get):
        fake_rsp =  [
            {"tag_name": "!!!not-a-version", "prerelease": False}
        ]
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = fake_rsp
        mock_get.return_value = mock_response

        self.assertFalse(is_update_available("1.2.3", fake_rsp))


class TestGetVersion(F1TelemetryUnitTestsBase):

    @patch.dict(os.environ, {'PNG_VERSION': '2.1.0'})
    def test_returns_env_value(self):
        self.assertEqual(get_version(), '2.1.0')

    @patch.dict(os.environ, {}, clear=True)
    def test_returns_default_when_env_missing(self):
        self.assertEqual(get_version(), 'dev')

    @patch.dict(os.environ, {'PNG_VERSION': ''})
    def test_returns_empty_string_if_env_is_empty(self):
        self.assertEqual(get_version(), '')
