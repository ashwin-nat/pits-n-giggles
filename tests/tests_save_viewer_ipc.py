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

import apps.save_viewer.save_viewer_state as SaveViewerState
from apps.save_viewer.save_viewer_ipc import SaveViewerIpc
from tests_base import F1TelemetryUnitTestsBase

# ----------------------------------------------------------------------------------------------------------------------

class TestSaveViewerIpcBase(F1TelemetryUnitTestsBase):
    """Base class for SaveViewerIpc tests."""

class TestOpenFileHelperValidation(TestSaveViewerIpcBase):
    """Test path validation in open_file_helper."""

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

        self.logger = logging.getLogger("test_save_viewer_ipc")
        SaveViewerState.init_state(self.logger)

    def tearDown(self):
        self.tmp_dir.cleanup()

    async def test_path_traversal_blocked(self):
        """Path traversal via ../../ must be rejected."""
        traversal_path = str(self.data_dir / ".." / "secret.txt")
        result = await SaveViewerState.open_file_helper(traversal_path)

        self.assertEqual(result["status"], "error")
        self.assertIn("disallowed traversal", result["message"])

    async def test_path_traversal_etc_passwd_blocked(self):
        """Classic /etc/passwd traversal must be rejected."""
        result = await SaveViewerState.open_file_helper("../../etc/passwd")

        self.assertEqual(result["status"], "error")
        self.assertIn("disallowed traversal", result["message"])

    async def test_missing_file_path_rejected(self):
        """Missing file-path argument must be rejected."""
        result = await SaveViewerState.open_file_helper(None)
        self.assertEqual(result["status"], "error")
        self.assertIn("Missing", result["message"])

        result = await SaveViewerState.open_file_helper("")
        self.assertEqual(result["status"], "error")
        self.assertIn("Missing", result["message"])

    async def test_wrong_extension_rejected(self):
        """Files with non-.json extension must be rejected."""
        txt_file = Path(self.tmp_dir.name) / "notes.txt"
        txt_file.write_text("not json", encoding="utf-8")

        result = await SaveViewerState.open_file_helper(str(txt_file))

        self.assertEqual(result["status"], "error")
        self.assertIn("File type not allowed", result["message"])

    async def test_directory_path_rejected(self):
        """A directory path must be rejected."""
        result = await SaveViewerState.open_file_helper(str(self.data_dir))

        self.assertEqual(result["status"], "error")
        self.assertIn("not point to an existing file", result["message"])

    async def test_nonexistent_file_rejected(self):
        """A path to a non-existent file (without ..) must be rejected."""
        fake_path = Path(self.tmp_dir.name) / "does_not_exist.json"
        result = await SaveViewerState.open_file_helper(str(fake_path))

        self.assertEqual(result["status"], "error")
        self.assertIn("not point to an existing file", result["message"])

    async def test_path_resolve_oserror_rejected(self):
        """If Path.resolve() raises OSError, the handler must return an error."""
        with patch('apps.save_viewer.save_viewer_state.save_viewer_state.Path.resolve',
                   side_effect=OSError("bad path")):
            result = await SaveViewerState.open_file_helper("/some/valid-looking/path.json")

        self.assertEqual(result["status"], "error")
        self.assertIn("Invalid file path", result["message"])

    async def test_valid_json_file_accepted(self):
        """A valid .json file must be accepted and loaded."""
        with patch('apps.save_viewer.save_viewer_state.save_viewer_state._check_recompute_json'):
            result = await SaveViewerState.open_file_helper(str(self.valid_file))

        self.assertEqual(result["status"], "success")

    async def test_valid_json_outside_data_accepted(self):
        """A valid .json file outside data/ must be accepted (no whitelist)."""
        external_dir = Path(self.tmp_dir.name) / "external_backup"
        external_dir.mkdir()
        external_json = external_dir / "race_backup.json"
        external_json.write_text('{"test": true}', encoding="utf-8")

        with patch('apps.save_viewer.save_viewer_state.save_viewer_state._check_recompute_json'):
            result = await SaveViewerState.open_file_helper(str(external_json))

        self.assertEqual(result["status"], "success")


class TestSaveViewerIpcFlow(TestSaveViewerIpcBase):
    """Test IPC handler flow (open-file -> browser -> broadcast)."""

    def setUp(self):
        self.mock_server = MagicMock()
        self.mock_server.send_to_clients_of_type = AsyncMock()
        self.mock_server.m_port = 8080
        self.logger = logging.getLogger("test_save_viewer_ipc")

    def _create_ipc(self):
        """Create a SaveViewerIpc instance with mocked dependencies."""
        with patch.object(SaveViewerIpc, '__init__', lambda self_, *a, **kw: None):
            ipc = SaveViewerIpc.__new__(SaveViewerIpc)
            ipc.m_logger = self.logger
            ipc.m_server = self.mock_server
            ipc.m_should_open_ui = False
            ipc.m_ipc_server = MagicMock()
            return ipc

    async def test_ipc_success_broadcasts_to_clients(self):
        """On successful open, IPC handler must broadcast to clients."""
        ipc = self._create_ipc()
        # Register routes to get the handler
        ipc._register_routes()

        # Find the registered open-file handler
        handler = None
        for call in ipc.m_ipc_server.on.call_args_list:
            if call[0][0] == "open-file":
                handler = call[1].get('handler') or ipc.m_ipc_server.on.return_value.call_args[0][0]
                break

        # Since the decorator pattern captures the function, get it differently
        # We test through _register_routes which registers handlers via decorators
        # The simplest approach: call the method through the mock's decorator capture
        with patch('apps.save_viewer.save_viewer_state.open_file_helper', new_callable=AsyncMock) as mock_open, \
             patch('apps.save_viewer.save_viewer_state.getTelemetryInfo') as mock_telemetry:
            mock_open.return_value = {"status": "success"}
            mock_telemetry.return_value = {"data": "test"}

            # Get the handler that was passed to the decorator
            # m_ipc_server.on("open-file") returns a decorator, which is called with the function
            decorator_calls = ipc.m_ipc_server.on.return_value.call_args_list
            open_file_handler = decorator_calls[0][0][0]  # first decorator call, first positional arg

            result = await open_file_handler({"file-path": "/tmp/test.json"})

        self.assertEqual(result["status"], "success")
        mock_open.assert_called_once_with("/tmp/test.json")
        self.mock_server.send_to_clients_of_type.assert_called_once()

    async def test_ipc_error_does_not_broadcast(self):
        """On validation error, IPC handler must NOT broadcast."""
        ipc = self._create_ipc()
        ipc._register_routes()

        with patch('apps.save_viewer.save_viewer_state.open_file_helper', new_callable=AsyncMock) as mock_open:
            mock_open.return_value = {"status": "error", "message": "some error"}

            decorator_calls = ipc.m_ipc_server.on.return_value.call_args_list
            open_file_handler = decorator_calls[0][0][0]

            result = await open_file_handler({"file-path": "/tmp/bad.json"})

        self.assertEqual(result["status"], "error")
        self.mock_server.send_to_clients_of_type.assert_not_called()

    async def test_ipc_opens_browser_once(self):
        """Browser should only open on the first successful open."""
        ipc = self._create_ipc()
        ipc.m_should_open_ui = True
        ipc._register_routes()

        with patch('apps.save_viewer.save_viewer_state.open_file_helper', new_callable=AsyncMock) as mock_open, \
             patch('apps.save_viewer.save_viewer_state.getTelemetryInfo') as mock_telemetry, \
             patch('apps.save_viewer.save_viewer_ipc.webbrowser.open') as mock_browser:
            mock_open.return_value = {"status": "success"}
            mock_telemetry.return_value = {"data": "test"}

            decorator_calls = ipc.m_ipc_server.on.return_value.call_args_list
            open_file_handler = decorator_calls[0][0][0]

            await open_file_handler({"file-path": "/tmp/test1.json"})
            await open_file_handler({"file-path": "/tmp/test2.json"})

        # Browser should have been opened exactly once
        mock_browser.assert_called_once()
