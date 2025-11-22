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

# ------------------------- IMPORTS ------------------------------------------------------------------------------------

import sys
from pathlib import Path
from typing import Callable, List, Optional

from PySide6.QtGui import QFontDatabase

# ------------------------- DEFAULTS -----------------------------------------------------------------------------------

_DEFAULT_BASE = Path("assets") / "fonts"
_DEFAULT_FONTS = [
    "f1-regular.ttf",
    "f1-bold.ttf",
    "Roboto-Regular.ttf",
    "Roboto-Bold.ttf",
    "JetBrainsMono-Bold.ttf",
    "JetBrainsMono-Regular.ttf",
    "Exo2-Bold.ttf",
    "Exo2-Regular.ttf",
]

# ------------------------- FUNCTIONS ----------------------------------------------------------------------------------

def _load_font(
        relative_path: Path,
        debug_log_printer: Optional[Callable[[str], None]] = None,
        error_log_printer: Optional[Callable[[str], None]] = None) -> bool:
    """
    Load fonts that work in both dev and PyInstaller builds.

    Args:
        relative_path: Path to the font file, relative to the project root or build bundle.
        debug_log_printer: Optional function to print debug messages.
        error_log_printer: Optional function to print error messages.

    Returns:
        bool: True if the font was loaded successfully, False otherwise.
    """
    try:
        if hasattr(sys, "_MEIPASS"):
            # Running inside a PyInstaller bundle
            base_path = Path(sys._MEIPASS)
        else:
            # Running from source
            base_path = Path.cwd()

        full_path = base_path / relative_path

        # Convert to str only for Qt API call
        font_id = QFontDatabase.addApplicationFont(str(full_path))

        if font_id == -1:
            if debug_log_printer:
                debug_log_printer(f"Failed to load font from {full_path}")
            return False

        if debug_log_printer:
            debug_log_printer(f"Loaded font from {full_path}. name={QFontDatabase.applicationFontFamilies(font_id)}")
        return True

    except Exception as e:  # pylint: disable=broad-except
        if error_log_printer:
            error_log_printer(f"Failed to load font from {relative_path}: {e}")
        return False


def load_fonts(
        base_path: Path = _DEFAULT_BASE,
        fonts_list: List[str] = None,
        debug_log_printer: Optional[Callable[[str], None]] = None,
        error_log_printer: Optional[Callable[[str], None]] = None) -> None:
    """
    Load and register fonts with the QT font database.

    Args:
        base_path: Base path to the font files. Defaults to _DEFAULT_BASE.
        fonts_list: List of font files to load. Defaults to _DEFAULT_FONTS.
        debug_log_printer: Optional function to print debug messages.
        error_log_printer: Optional function to print error messages.
    """
    if not fonts_list:
        fonts_list = _DEFAULT_FONTS
    for font in fonts_list:
        font_path = base_path / font
        _load_font(font_path, debug_log_printer, error_log_printer)
