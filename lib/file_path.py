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

def resolve_user_file(filename: str) -> str:
    """
    Resolves the given filename to a user-writable path.

    - On Windows, uses the path as-is (relative to current working directory)
    - On macOS, uses ~/Library/Application Support/pits_n_giggles/
    - On Linux and other Unix-like platforms, uses $XDG_CONFIG_HOME/pits_n_giggles/
      (default: ~/.config/pits_n_giggles/)

    Args:
        filename (str): The name of the file to resolve.

    Returns:
        str: Full path to the resolved file location.
    """
    if sys.platform == "win32":
        return filename
    if sys.platform == "darwin":
        base_dir = Path.home() / "Library" / "Application Support" / APP_NAME_SNAKE
    else:
        xdg_config = os.environ.get("XDG_CONFIG_HOME", "")
        if xdg_config:
            base_dir = Path(xdg_config) / APP_NAME_SNAKE
        else:
            base_dir = Path.home() / ".config" / APP_NAME_SNAKE
    base_dir.mkdir(parents=True, exist_ok=True)
    return str(base_dir / filename)
