import asyncio
import json
import tempfile
import sys
import os
from pathlib import Path
from unittest.mock import patch

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tests_base import F1TelemetryUnitTestsBase
import lib.save_to_disk
from lib.save_to_disk import save_race_info


class TestSaveRaceInfo(F1TelemetryUnitTestsBase):

    def test_save_race_info_creates_file_with_correct_content(self):
        test_data = {"driver": "Hamilton", "position": 2}
        test_filename = "race-info.json"
        test_date = "2025-07-17"

        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            target_dir = base_path / "data" / test_date / "race-info"
            expected_file_path = target_dir / test_filename

            # Patch Path inside save_race_info to redirect to the temp dir
            # We use a simple monkeypatch-style override
            original_path = Path

            try:
                # Patch Path() constructor used in save_race_info
                def patched_path(*args):
                    return base_path.joinpath(*args)

                lib.save_to_disk.Path = patched_path

                # Call the async function using a fresh event loop
                asyncio.run(save_race_info(test_data, test_filename, test_date))

                # Verify file exists
                self.assertTrue(expected_file_path.exists(), "Expected JSON file was not created.")

                # Verify file contents
                with expected_file_path.open("r", encoding="utf-8") as f:
                    content = json.load(f)
                self.assertEqual(content, test_data, "File contents do not match input data.")
            finally:
                # Restore original Path to avoid side effects
                lib.save_to_disk.Path = original_path
