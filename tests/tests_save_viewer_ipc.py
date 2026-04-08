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
import logging
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from apps.save_viewer.save_viewer_ipc import SaveViewerIpc
from tests_base import F1TelemetryUnitTestsBase

# ----------------------------------------------------------------------------------------------------------------------

class TestSaveViewerIpcBase(F1TelemetryUnitTestsBase):
    """Base class for SaveViewerIpc tests."""

class TestSaveViewerPathTraversal(TestSaveViewerIpcBase):
    """Test path traversal protection in SaveViewerIpc._handle_open_file."""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.tmp_dir.name) / "data"
        self.data_dir.mkdir()

        # Create a valid JSON file inside data/
        self.valid_file = self.data_dir / "race.json"
        self.valid_file.write_text('{"test": true}', encoding="utf-8")

        # Create a file outside data/ to simulate traversal target
        self.outside_file = Path(self.tmp_dir.name) / "secret.txt"
        self.outside_file.write_text("secret", encoding="utf-8")

        # Mock server with m_base_dir pointing to our tmp root
        self.mock_server = MagicMock()
        self.mock_server.m_base_dir = Path(self.tmp_dir.name)

        self.logger = logging.getLogger("test_save_viewer_ipc")

    def tearDown(self):
        self.tmp_dir.cleanup()

    def _create_ipc(self):
        """Create a SaveViewerIpc instance with mocked dependencies."""
        with patch.object(SaveViewerIpc, '__init__', lambda self_, *a, **kw: None):
            ipc = SaveViewerIpc.__new__(SaveViewerIpc)
            ipc.m_logger = self.logger
            ipc.m_server = self.mock_server
            ipc.m_should_open_ui = False
            return ipc

    async def test_path_traversal_blocked(self):
        """Path traversal via ../../ must be rejected."""
        ipc = self._create_ipc()

        # Attempt traversal using relative path that escapes data/
        traversal_path = str(self.data_dir / ".." / "secret.txt")
        result = await ipc._handle_open_file({"file-path": traversal_path})

        self.assertEqual(result["status"], "error")
        self.assertIn("disallowed traversal", result["message"])

    async def test_path_traversal_etc_passwd_blocked(self):
        """Classic /etc/passwd traversal must be rejected."""
        ipc = self._create_ipc()

        result = await ipc._handle_open_file({"file-path": "../../etc/passwd"})

        self.assertEqual(result["status"], "error")
        self.assertIn("disallowed traversal", result["message"])

    async def test_valid_path_in_data_accepted(self):
        """A valid file path under data/ must be accepted."""
        ipc = self._create_ipc()

        with patch('apps.save_viewer.save_viewer_state.open_file_helper', new_callable=AsyncMock) as mock_open, \
             patch.object(ipc.m_server, 'send_to_clients_of_type', new_callable=AsyncMock):
            mock_open.return_value = {"status": "success"}
            result = await ipc._handle_open_file({"file-path": str(self.valid_file)})

        self.assertEqual(result["status"], "success")
        mock_open.assert_called_once()

    async def test_missing_file_path_rejected(self):
        """Missing file-path argument must be rejected."""
        ipc = self._create_ipc()
        result = await ipc._handle_open_file({})
        self.assertEqual(result["status"], "error")
        self.assertIn("Missing", result["message"])

    async def test_valid_json_outside_data_accepted(self):
        """A valid .json file outside data/ must be accepted (no whitelist)."""
        ipc = self._create_ipc()

        # Create a JSON file completely outside data/
        external_dir = Path(self.tmp_dir.name) / "external_backup"
        external_dir.mkdir()
        external_json = external_dir / "race_backup.json"
        external_json.write_text('{"test": true}', encoding="utf-8")

        with patch('apps.save_viewer.save_viewer_state.open_file_helper', new_callable=AsyncMock) as mock_open, \
             patch.object(ipc.m_server, 'send_to_clients_of_type', new_callable=AsyncMock):
            mock_open.return_value = {"status": "success"}
            result = await ipc._handle_open_file({"file-path": str(external_json)})

        self.assertEqual(result["status"], "success")
        mock_open.assert_called_once()

    async def test_wrong_extension_rejected(self):
        """Files with non-.json extension must be rejected."""
        ipc = self._create_ipc()

        txt_file = Path(self.tmp_dir.name) / "notes.txt"
        txt_file.write_text("not json", encoding="utf-8")

        result = await ipc._handle_open_file({"file-path": str(txt_file)})

        self.assertEqual(result["status"], "error")
        self.assertIn("File type not allowed", result["message"])

    async def test_directory_path_rejected(self):
        """A directory path must be rejected."""
        ipc = self._create_ipc()

        result = await ipc._handle_open_file({"file-path": str(self.data_dir)})

        self.assertEqual(result["status"], "error")
        self.assertIn("not point to an existing file", result["message"])

    async def test_nonexistent_file_rejected(self):
        """A path to a non-existent file (without ..) must be rejected."""
        ipc = self._create_ipc()

        fake_path = Path(self.tmp_dir.name) / "does_not_exist.json"
        result = await ipc._handle_open_file({"file-path": str(fake_path)})

        self.assertEqual(result["status"], "error")
        self.assertIn("not point to an existing file", result["message"])
