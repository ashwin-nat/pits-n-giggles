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

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

import os
import sys
from pathlib import Path

from meta.meta import APP_NAME_SNAKE

# -------------------------------------- FUNCTIONS --------------------------------------------------------------------

def get_app_base_dir() -> Path:
    """
    Returns the base directory for user-writable app data.

    - On macOS: ~/Library/Application Support/pits_n_giggles/
    - On other platforms: current working directory
    """
    if sys.platform != "darwin":
        return Path(".")
    base_dir = Path.home() / "Library" / "Application Support" / APP_NAME_SNAKE
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


def get_app_fixed_dir() -> Path:
    """
    Returns a fixed, cwd-independent per-user directory for app data.

    Unlike :func:`get_app_base_dir`, this never resolves to the current working
    directory, so files placed here are shared across every instance of the app
    regardless of where it was launched from (needed e.g. for a single-instance
    lock file).

    - On macOS: ~/Library/Application Support/pits_n_giggles/
    - On Windows: %LOCALAPPDATA%/pits_n_giggles/
    - On other platforms: ~/.local/state/pits_n_giggles/
    """
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local")
        base_dir = Path(base) / APP_NAME_SNAKE
    elif sys.platform == "darwin":
        base_dir = Path.home() / "Library" / "Application Support" / APP_NAME_SNAKE
    else:
        base = os.environ.get("XDG_STATE_HOME") or (Path.home() / ".local" / "state")
        base_dir = Path(base) / APP_NAME_SNAKE
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


def resolve_user_file(filename: str) -> str:
    """
    Resolves the given filename to a user-writable path.

    - On macOS, uses ~/Library/Application Support/pits_n_giggles/
    - On other platforms, uses the path as-is (relative to current working directory)

    Args:
        filename (str): The name of the file to resolve.

    Returns:
        str: Full path to the resolved file location.
    """
    return str(get_app_base_dir() / filename)


def resolve_fixed_file(filename: str) -> str:
    """
    Resolves the given filename to a fixed, cwd-independent per-user path.

    Use this (instead of :func:`resolve_user_file`) for files that must be shared
    by every instance of the app regardless of launch directory, such as the
    single-instance lock file.

    Args:
        filename (str): The name of the file to resolve.

    Returns:
        str: Full path to the resolved file location.
    """
    return str(get_app_fixed_dir() / filename)
