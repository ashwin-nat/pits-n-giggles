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

"""CaptureSettings rules the field spec table does not cover: defaults and session_dir. The autosave flags are in
tests_config_properties.py."""

import allure
import pytest
from pydantic import ValidationError

from lib.config import CaptureSettings

pytestmark = allure.feature("Capture settings")

# -------------------------------------- DEFAULTS ----------------------------------------------------------------------

@allure.story("Defaults")
@allure.title("Default CaptureSettings hold the shipped values")
def test_default_values():
    """
    Builds CaptureSettings with no arguments.

    Expected: every field holds its shipped default.
    """
    settings = CaptureSettings()

    assert settings.post_race_data_autosave is True
    assert settings.post_quali_data_autosave is True
    assert settings.post_fp_data_autosave is False
    assert settings.post_tt_data_autosave is False
    assert settings.save_race_ctrl_msg is False
    assert settings.just_in_case_autosave is True
    assert settings.session_dir == "data"

# -------------------------------------- SESSION DIR -------------------------------------------------------------------

@allure.story("Session dir")
@allure.title("session_dir keeps the path {path}")
@pytest.mark.parametrize("path", ["/my/sessions", "custom/relative"])
def test_session_dir_valid(path):
    """
    Sets session_dir to an absolute or a relative path.

    Expected: the model builds and keeps the path as given.
    """
    assert CaptureSettings(session_dir=path).session_dir == path


@allure.story("Session dir")
@allure.title("session_dir rejects {path!r}")
@pytest.mark.parametrize("path", ["", "   "])
def test_session_dir_blank_rejected(path):
    """
    Sets session_dir to an empty or whitespace-only string.

    Expected: a ValidationError.
    """
    with pytest.raises(ValidationError):
        CaptureSettings(session_dir=path)
