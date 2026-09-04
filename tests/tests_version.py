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

import pytest
from packaging import version as pkg_version

from lib.version import get_build_version, get_version, is_update_available
from meta.meta import APP_VERSION

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

    @patch("lib.version._get_git_metadata", return_value=("main", "abc1234", "clean"))
    @patch.dict(os.environ, {}, clear=True)
    def test_returns_git_derived_default_when_env_missing(self, _mock_git_metadata):
        self.assertEqual(get_version(), 'dev_main_abc1234_clean')

    @patch("lib.version._get_git_metadata", return_value=("feature/new-ui", "deadbee", "dirty"))
    @patch.dict(os.environ, {}, clear=True)
    def test_returns_dirty_git_derived_default_when_env_missing(self, _mock_git_metadata):
        self.assertEqual(get_version(), 'dev_feature/new-ui_deadbee_dirty')

    @patch.dict(os.environ, {'PNG_VERSION': ''})
    def test_returns_empty_string_if_env_is_empty(self):
        self.assertEqual(get_version(), '')

    @patch.dict(os.environ, {}, clear=True)
    def test_returns_meta_version_when_use_meta_version_true_and_env_missing(self):
        self.assertEqual(get_version(use_meta_version=True), APP_VERSION)

    @patch.dict(os.environ, {'PNG_VERSION': '3.0.0'})
    def test_env_value_takes_priority_over_use_meta_version(self):
        self.assertEqual(get_version(use_meta_version=True), '3.0.0')


# ----------------------------------------------------------------------------------------------------------------------

def test_release_build_reports_the_bare_meta_version():
    # The whole point of release mode: what the user quotes has to equal the tag.
    with patch("lib.version._get_git_metadata") as mock_git_metadata:
        assert get_build_version(release_mode=True) == APP_VERSION
    mock_git_metadata.assert_not_called()


@pytest.mark.parametrize("tree_state, expected_suffix", [
    ("clean", "abc1234"),
    ("unknown", "abc1234"),
    ("dirty", "abc1234.dirty"),
])
def test_non_release_build_appends_the_commit(tree_state, expected_suffix):
    with patch("lib.version._get_git_metadata", return_value=("main", "abc1234", tree_state)):
        assert get_build_version() == f"{APP_VERSION}+{expected_suffix}"


def test_non_release_build_survives_git_being_unavailable():
    # _get_git_metadata degrades to "unknown" rather than raising; the build must not die
    # just because it ran outside a checkout.
    with patch("lib.version._get_git_metadata", return_value=("unknown", "unknown", "unknown")):
        assert get_build_version() == f"{APP_VERSION}+unknown"


@pytest.mark.parametrize("tree_state", ["clean", "dirty"])
def test_build_version_stays_comparable(tree_state):
    # is_update_available parses the running version, so a dev build must not break the
    # update check. A PEP 440 local segment is ignored when ordering against a release.
    with patch("lib.version._get_git_metadata", return_value=("main", "abc1234", tree_state)):
        dev = pkg_version.parse(get_build_version())
    assert dev.base_version == pkg_version.parse(APP_VERSION).base_version
    assert not is_update_available(
        get_build_version(release_mode=True),
        [{"prerelease": False, "tag_name": f"v{APP_VERSION}"}],
    )
