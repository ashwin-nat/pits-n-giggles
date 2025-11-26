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
from typing import Callable, Optional

from PySide6.QtGui import QIcon

# ------------------------- FUNCTIONS ----------------------------------------------------------------------------------

def load_icon(
    relative_path: Path,
    debug_log_printer: Optional[Callable[[str], None]] = None,
    error_log_printer: Optional[Callable[[str], None]] = None
) -> QIcon:
    """
    Load an icon that works in both dev and PyInstaller builds.

    Args:
        relative_path: Path to the icon file, relative to the project root or build bundle.
        debug_log_printer: Optional callable for debug logging. Defaults to no-op.
        error_log_printer: Optional callable for error logging. Defaults to no-op.

    Returns:
        QIcon: The loaded icon, or an empty QIcon if loading fails.
    """
    # Default to no-op functions if not provided
    debug_log = debug_log_printer or (lambda msg: None)
    error_log = error_log_printer or (lambda msg: None)

    try:
        if hasattr(sys, "_MEIPASS"):
            # Running inside a PyInstaller bundle
            base_path = Path(sys._MEIPASS)
        else:
            # Running from source
            base_path = Path.cwd()

        full_path = base_path / relative_path

        # Convert to string only when passing to QIcon
        icon = QIcon(str(full_path))
        debug_log(f"Loaded icon from {full_path}")
        return icon
    except Exception as e:  # pylint: disable=broad-except
        error_log(f"Failed to load icon from {relative_path}: {e}")
        return QIcon()

def load_tyre_icons_dict(
        relative_path: Optional[Path] = Path("assets") / "tyre-icons",
        debug_log_printer: Optional[Callable[[str], None]] = None,
        error_log_printer: Optional[Callable[[str], None]] = None
        ) -> dict[str, QIcon]:
    """Get a dictionary of tyre icons.

    A
    Args:
        relative_path: Path to the tyre icons directory, relative to the project root or build bundle.
        debug_log_printer: Optional callable for debug logging. Defaults to no-op.
        error_log_printer: Optional callable for error logging. Defaults to no-op.

    Returns:
        dict[str, QIcon]: A dictionary mapping visual compound names to their corresponding icons.
    """
    return {
        "Soft": load_icon(relative_path / "soft_tyre.svg", debug_log_printer, error_log_printer),
        "Super Soft": load_icon(relative_path / "super_soft_tyre.svg", debug_log_printer, error_log_printer),
        "Medium": load_icon(relative_path / "medium_tyre.svg", debug_log_printer, error_log_printer),
        "Hard": load_icon(relative_path / "hard_tyre.svg", debug_log_printer, error_log_printer),
        "Inters": load_icon(relative_path / "intermediate_tyre.svg", debug_log_printer, error_log_printer),
        "Wet": load_icon(relative_path / "wet_tyre.svg", debug_log_printer, error_log_printer),
    }
