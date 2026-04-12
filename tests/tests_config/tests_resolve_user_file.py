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
from pathlib import Path, PurePosixPath
from unittest.mock import patch, MagicMock

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.file_path import resolve_user_file

from .tests_config_base import TestF1ConfigBase

# ----------------------------------------------------------------------------------------------------------------------

class TestResolveUserFile(TestF1ConfigBase):

    def test_windows_returns_filename_unchanged(self):
        """On Windows, resolve_user_file should return the filename as-is."""
        with patch("lib.file_path.sys") as mock_sys:
            mock_sys.platform = "win32"
            result = resolve_user_file("config.json")
        self.assertEqual(result, "config.json")

    def test_windows_does_not_create_directory(self):
        """On Windows, no directory creation should happen."""
        with patch("lib.file_path.sys") as mock_sys, \
             patch.object(Path, "mkdir") as mock_mkdir:
            mock_sys.platform = "win32"
            resolve_user_file("config.json")
        mock_mkdir.assert_not_called()

    def test_macos_resolves_to_application_support(self):
        """On macOS, path should use ~/Library/Application Support/pits_n_giggles/."""
        fake_home = Path("/Users/testuser")
        with patch("lib.file_path.sys") as mock_sys, \
             patch.object(Path, "home", return_value=fake_home), \
             patch.object(Path, "mkdir"):
            mock_sys.platform = "darwin"
            result = resolve_user_file("config.json")
        expected = str(fake_home / "Library" / "Application Support" / "pits_n_giggles" / "config.json")
        self.assertEqual(result, expected)

    def test_macos_creates_directory(self):
        """On macOS, mkdir(parents=True, exist_ok=True) should be called."""
        fake_home = Path("/Users/testuser")
        with patch("lib.file_path.sys") as mock_sys, \
             patch.object(Path, "home", return_value=fake_home), \
             patch.object(Path, "mkdir") as mock_mkdir:
            mock_sys.platform = "darwin"
            resolve_user_file("config.json")
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_linux_uses_xdg_config_home(self):
        """On Linux with XDG_CONFIG_HOME set, that path should be used."""
        with patch("lib.file_path.sys") as mock_sys, \
             patch.dict(os.environ, {"XDG_CONFIG_HOME": "/custom/config"}, clear=False), \
             patch.object(Path, "mkdir"):
            mock_sys.platform = "linux"
            result = resolve_user_file("config.json")
        expected = str(Path("/custom/config") / "pits_n_giggles" / "config.json")
        self.assertEqual(result, expected)

    def test_linux_fallback_without_xdg_config_home(self):
        """On Linux without XDG_CONFIG_HOME, should fallback to ~/.config/pits_n_giggles/."""
        fake_home = Path("/home/testuser")
        with patch("lib.file_path.sys") as mock_sys, \
             patch.dict(os.environ, {}, clear=True), \
             patch.object(Path, "home", return_value=fake_home), \
             patch.object(Path, "mkdir"):
            mock_sys.platform = "linux"
            result = resolve_user_file("config.json")
        expected = str(fake_home / ".config" / "pits_n_giggles" / "config.json")
        self.assertEqual(result, expected)

    def test_linux_creates_directory_with_xdg(self):
        """On Linux with XDG_CONFIG_HOME, mkdir should be called."""
        with patch("lib.file_path.sys") as mock_sys, \
             patch.dict(os.environ, {"XDG_CONFIG_HOME": "/custom/config"}, clear=False), \
             patch.object(Path, "mkdir") as mock_mkdir:
            mock_sys.platform = "linux"
            resolve_user_file("config.json")
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_linux_creates_directory_without_xdg(self):
        """On Linux without XDG_CONFIG_HOME, mkdir should be called."""
        fake_home = Path("/home/testuser")
        with patch("lib.file_path.sys") as mock_sys, \
             patch.dict(os.environ, {}, clear=True), \
             patch.object(Path, "home", return_value=fake_home), \
             patch.object(Path, "mkdir") as mock_mkdir:
            mock_sys.platform = "linux"
            resolve_user_file("config.json")
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_filename_preserved_in_result(self):
        """The original filename should appear at the end of the resolved path."""
        fake_home = Path("/home/testuser")
        with patch("lib.file_path.sys") as mock_sys, \
             patch.dict(os.environ, {}, clear=True), \
             patch.object(Path, "home", return_value=fake_home), \
             patch.object(Path, "mkdir"):
            mock_sys.platform = "linux"
            result = resolve_user_file("my_settings.ini")
        self.assertTrue(result.endswith("my_settings.ini"))
