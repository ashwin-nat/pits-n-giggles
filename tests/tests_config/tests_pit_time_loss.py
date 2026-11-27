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

"""PitTimeLoss field names. Each track's value range is in tests_config_properties.py."""

import allure
import pytest

from lib.config import PitTimeLossF1, PitTimeLossF2
from lib.f1_types import TrackID

pytestmark = allure.feature("Pit time loss settings")


@allure.story("Track names")
@allure.title("Every {model.__name__} field names a known track")
@pytest.mark.parametrize("model", [PitTimeLossF1, PitTimeLossF2], ids=lambda m: m.__name__)
def test_field_names_are_tracks(model):
    """
    Maps each field name to a track name (underscores to spaces, except "_Reverse" layouts, which keep the
    underscore) and looks it up among the TrackID names.

    Expected: every field names a track, so the per-track lookup finds a value for it.
    """
    track_names = {str(track) for track in TrackID}
    for field in model.model_fields:
        name = field if field.endswith("_Reverse") else field.replace("_", " ")
        assert name in track_names, f"{model.__name__}.{field}"
