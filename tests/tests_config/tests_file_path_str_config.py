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

from lib.config import FilePathStr

from .tests_config_base import TestF1ConfigBase

# ----------------------------------------------------------------------------------------------------------------------

class TestFilePathStr(TestF1ConfigBase):

    def test_validate_accepts_valid_string(self):
        # Just a normal string input should be accepted
        input_value = "some/path/to/file.txt"
        # validate currently does not check existence, so this passes
        result = FilePathStr.validate(input_value)
        self.assertEqual(result, input_value)

    def test_validate_rejects_non_string(self):
        # Non-string input should raise TypeError
        for invalid_value in [123, 45.6, None, [], {}, True]:
            with self.assertRaises(TypeError):
                FilePathStr.validate(invalid_value)
