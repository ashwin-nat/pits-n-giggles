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
from collections import defaultdict
from pathlib import Path
from typing import Callable, Dict, Optional

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

def load_team_icons_dict(
    relative_path: Optional[Path] = Path("assets") / "team-logos",
    debug_log_printer: Optional[Callable[[str], None]] = None,
    error_log_printer: Optional[Callable[[str], None]] = None
) -> defaultdict[str, QIcon]:
    """Get a dictionary of team icons with a default logo for unknown teams.

    Args:
        relative_path: Path to the tyre icons directory, relative to the project root or build bundle.
        debug_log_printer: Optional callable for debug logging. Defaults to no-op.
        error_log_printer: Optional callable for error logging. Defaults to no-op.

    Returns:
        dict[str, QIcon]: A dictionary mapping visual compound names to their corresponding icons.
    """

    default_team_logo = load_icon(
        relative_path / "default.svg",
        debug_log_printer,
        error_log_printer
    )

    return defaultdict(lambda: default_team_logo, {
        "Alpine": load_icon(relative_path / "alpine.svg", debug_log_printer, error_log_printer),
        "Alpine '24": load_icon(relative_path / "alpine.svg", debug_log_printer, error_log_printer),
        "Aston Martin": load_icon(relative_path / "aston_martin.svg", debug_log_printer, error_log_printer),
        "Aston Martin '24": load_icon(relative_path / "aston_martin.svg", debug_log_printer, error_log_printer),
        "Ferrari": load_icon(relative_path / "ferrari.svg", debug_log_printer, error_log_printer),
        "Ferrari '24": load_icon(relative_path / "ferrari.svg", debug_log_printer, error_log_printer),
        "Haas": load_icon(relative_path / "haas.svg", debug_log_printer, error_log_printer),
        "Haas '24": load_icon(relative_path / "haas.svg", debug_log_printer, error_log_printer),
        "McLaren": load_icon(relative_path / "mclaren.svg", debug_log_printer, error_log_printer),
        "Mclaren": load_icon(relative_path / "mclaren.svg", debug_log_printer, error_log_printer),
        "Mclaren '24": load_icon(relative_path / "mclaren.svg", debug_log_printer, error_log_printer),
        "Mercedes": load_icon(relative_path / "mercedes.svg", debug_log_printer, error_log_printer),
        "Mercedes '24": load_icon(relative_path / "mercedes.svg", debug_log_printer, error_log_printer),
        "RB": load_icon(relative_path / "rb.svg", debug_log_printer, error_log_printer),
        "Rb '24": load_icon(relative_path / "rb.svg", debug_log_printer, error_log_printer),
        "VCARB": load_icon(relative_path / "rb.svg", debug_log_printer, error_log_printer),
        "Alpha Tauri": load_icon(relative_path / "rb.svg", debug_log_printer, error_log_printer),
        "Red Bull": load_icon(relative_path / "red_bull.svg", debug_log_printer, error_log_printer),
        "Red Bull Racing": load_icon(relative_path / "red_bull.svg", debug_log_printer, error_log_printer),
        "Red Bull Racing '24": load_icon(relative_path / "red_bull.svg", debug_log_printer, error_log_printer),
        "Sauber": load_icon(relative_path / "sauber.svg", debug_log_printer, error_log_printer),
        "Sauber '24": load_icon(relative_path / "sauber.svg", debug_log_printer, error_log_printer),
        "Alfa Romeo": load_icon(relative_path / "sauber.svg", debug_log_printer, error_log_printer),
        "Williams": load_icon(relative_path / "williams.svg", debug_log_printer, error_log_printer),
        "Williams '24": load_icon(relative_path / "williams.svg", debug_log_printer, error_log_printer),
    })

def load_team_logos_uri_dict(
    relative_path: Optional[Path] = Path("assets") / "team-logos",
) -> defaultdict[str, str]:
    """Get a dictionary of team icons with a default logo for unknown teams.

    Args:
        relative_path: Path to the team icons directory, relative to the project root or build bundle.

    Returns:
        dict[str, str]: A dictionary mapping team names to their corresponding icons as URIs.
    """

    base = _get_resource_base() / relative_path
    default_team_logo_uri = (base / "default.svg").as_uri()

    return defaultdict(
        lambda: default_team_logo_uri,
        {
            "Alpine": (base / "alpine.svg").as_uri(),
            "Alpine '24": (base / "alpine.svg").as_uri(),
            "Aston Martin": (base / "aston_martin.svg").as_uri(),
            "Aston Martin '24": (base / "aston_martin.svg").as_uri(),
            "Ferrari": (base / "ferrari.svg").as_uri(),
            "Ferrari '24": (base / "ferrari.svg").as_uri(),
            "Haas": (base / "haas.svg").as_uri(),
            "Haas '24": (base / "haas.svg").as_uri(),
            "McLaren": (base / "mclaren.svg").as_uri(),
            "Mclaren": (base / "mclaren.svg").as_uri(),
            "Mclaren '24": (base / "mclaren.svg").as_uri(),
            "Mercedes": (base / "mercedes.svg").as_uri(),
            "Mercedes '24": (base / "mercedes.svg").as_uri(),
            "RB": (base / "rb.svg").as_uri(),
            "Rb '24": (base / "rb.svg").as_uri(),
            "VCARB": (base / "rb.svg").as_uri(),
            "Alpha Tauri": (base / "rb.svg").as_uri(),
            "Red Bull": (base / "red_bull.svg").as_uri(),
            "Red Bull Racing": (base / "red_bull.svg").as_uri(),
            "Red Bull Racing '24": (base / "red_bull.svg").as_uri(),
            "Sauber": (base / "sauber.svg").as_uri(),
            "Sauber '24": (base / "sauber.svg").as_uri(),
            "Alfa Romeo": (base / "sauber.svg").as_uri(),
            "Williams": (base / "williams.svg").as_uri(),
            "Williams '24": (base / "williams.svg").as_uri(),
        },
    )

def load_tyre_icons_uri_dict(relative_path: Optional[Path] = Path("assets") / "tyre-icons",
) -> Dict[str, Path]:
    """Get a dictionary of tyre icons file paths.

    Args:
        relative_path: Path to the tyre icons directory, relative to the project root or build bundle.

    Returns:
        dict[str, Path]: A dictionary mapping visual compound names to their URI's
    """

    base = _get_resource_base() / relative_path

    return {
        "Soft": (base / "soft_tyre.svg").as_uri(),
        "Super Soft": (base / "super_soft_tyre.svg").as_uri(),
        "Medium": (base / "medium_tyre.svg").as_uri(),
        "Hard": (base / "hard_tyre.svg").as_uri(),
        "Inters": (base / "intermediate_tyre.svg").as_uri(),
        "Wet": (base / "wet_tyre.svg").as_uri(),
    }

def _get_resource_base() -> Path:
    """Get the base path for loading resources. Handles pyinstaller build paths"""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path.cwd()