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
import itertools
from typing import Dict, Any
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QStackedWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QHBoxLayout
)
from PySide6.QtCore import Qt

from apps.hud.ui.infra.config import OverlaysConfig
from apps.hud.ui.overlays.base import BaseOverlay
from apps.hud.ui.overlays.mfd.pages.base_page import BasePage

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class CollapsedPage(BasePage):
    """Minimal page shown when MFD is collapsed."""

    def __init__(self, parent: BasePage, logger: logging.Logger):
        self.overlay_id: str = "mfd.collapsed"
        super().__init__(parent, logger)

        icon_base = Path("assets")
        icon_path = icon_base / "logo.png"
        page_text = "Pits n' Giggles MFD"

        # Try loading icon
        self.app_icon = self.load_icon(str(icon_path))

        if self.app_icon and not self.app_icon.isNull():
            layout = QHBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Icon
            icon_label = QLabel(self)
            pixmap = self.app_icon.pixmap(24, 24)  # adjust size if needed
            icon_label.setPixmap(pixmap)
            icon_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)

            # Text
            text_label = QLabel(page_text, self)
            text_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
            # Optional styling for better visibility
            # text_label.setStyleSheet("color: #ccc; font-weight: bold; font-size: 14px;")

            # Combine
            layout.addWidget(icon_label)
            layout.addSpacing(6)
            layout.addWidget(text_label)
            self.page_layout.addLayout(layout)

        else:
            label = QLabel(page_text, self)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.page_layout.addWidget(label)
