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

from lib.config import PitTimeLossF1, PitTimeLossF2
from lib.f1_types import TrackID

from .tests_config_base import TestF1ConfigBase

# ----------------------------------------------------------------------------------------------------------------------

class TestPitTimeLossF1(TestF1ConfigBase):
    """Test NetworkSettings model validation and defaults"""

    def test_track_name_validity(self):
        field_names = list(PitTimeLossF1.model_fields.keys())
        valid_track_names = {str(track) for track in TrackID}
        for field in field_names:
            if field.endswith("_Reverse"):
                cleaned_field = field
            else:
                cleaned_field = field.replace("_", " ")
            self.assertIn(cleaned_field, valid_track_names)

class TestPitTimeLossF2(TestF1ConfigBase):
    """Test NetworkSettings model validation and defaults"""

    def test_track_name_validity(self):
        field_names = list(PitTimeLossF1.model_fields.keys())
        valid_track_names = {str(track) for track in TrackID}
        for field in field_names:
            if field.endswith("_Reverse"):
                cleaned_field = field
            else:
                cleaned_field = field.replace("_", " ")
            self.assertIn(cleaned_field, valid_track_names)
