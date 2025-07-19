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

import asyncio
import json
import tempfile
import sys
import os
from pathlib import Path

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tests_base import F1TelemetryUnitTestsBase
from lib.save_to_disk import save_json_to_file


class TestSaveRaceInfo(F1TelemetryUnitTestsBase):

    def test_save_race_info_creates_file_with_correct_content(self):
        test_data = {"driver": "Hamilton", "position": 2}
        test_filename = "race-info.json"

        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            # Call the async function using the temp dir as base_dir
            file_path = asyncio.run(save_json_to_file(test_data, test_filename, base_path))

            # Verify file exists
            self.assertTrue(file_path.exists(), "Expected JSON file was not created.")

            # Verify file contents
            with file_path.open("r", encoding="utf-8") as f:
                content = json.load(f)
            self.assertEqual(content, test_data, "File contents do not match input data.")
