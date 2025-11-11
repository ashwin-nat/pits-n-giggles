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

import logging
import sys
import os
from typing import Dict, Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QStackedWidget,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from apps.hud.ui.infra.config import OverlaysConfig
from apps.hud.ui.overlays.base import BaseOverlay


# -------------------------------------- CLASSES -----------------------------------------------------------------------

class BasePage(QWidget):
    """Minimal page shown when MFD is collapsed."""

    def __init__(self, parent: QWidget, logger: logging.Logger):
        super().__init__(parent)
        self.page_layout = QVBoxLayout(self)
        self.page_layout.setContentsMargins(0, 0, 0, 0)
        self.page_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_cache: Dict[str, QIcon] = {}
        self.logger = logger
        self.overlay_id = None  # type: ignore  # derived classes should set this

    def load_icon(self, relative_path: str) -> QIcon:
        """
        Load an icon that works in both dev and PyInstaller builds.

        Args:
            relative_path: Path to the icon file, relative to the project root or build bundle.

        Returns:
            QIcon: The loaded icon, or an empty QIcon if loading fails.
        """
        try:
            if hasattr(sys, "_MEIPASS"):
                # Running inside a PyInstaller bundle
                base_path = sys._MEIPASS
            else:
                # Running from source
                base_path = os.path.abspath(".")

            full_path = os.path.join(base_path, relative_path)
            if cached_icon := self._icon_cache.get(full_path):
                self.logger.debug(f"{self.overlay_id} | Loaded icon from cache: '{relative_path}'")
                return cached_icon

            actual_icon = QIcon(full_path)
            self._icon_cache[full_path] = actual_icon
            self.logger.debug(f"{self.overlay_id} | Icon not in cache: '{relative_path}. Loaded from disk.")
            return actual_icon

        except Exception as e:  # pylint: disable=broad-except
            self.logger.warning(f"{self.overlay_id} | Failed to load icon '{relative_path}': {e}")
            return QIcon()
