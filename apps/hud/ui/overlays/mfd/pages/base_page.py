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
from typing import Dict, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget, QFrame

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class BasePage(QWidget):
    """Minimal page shown when MFD is collapsed."""

    # Class variables for title customization
    TITLE_FONT_FACE = "Montserrat"
    TITLE_FONT_SIZE = 11

    def __init__(self, parent: QWidget, logger: logging.Logger, overlay_id: str, title: Optional[str] = None):
        super().__init__(parent)

        # Main layout for the entire page
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._icon_cache: Dict[str, QIcon] = {}
        self.logger = logger
        self.overlay_id = overlay_id

        # Add title bar if specified
        if title:
            title_bar = self._create_title_bar(title)
            main_layout.addWidget(title_bar)

        # Content area with centered alignment
        content_widget = QWidget(self)
        self.page_layout = QVBoxLayout(content_widget)
        self.page_layout.setContentsMargins(0, 0, 0, 0)
        self.page_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        main_layout.addWidget(content_widget)

    def _create_title_bar(self, title: str) -> QFrame:
        """
        Create a fixed-height title bar at the top of the widget.

        Args:
            title: The title text to display

        Returns:
            QFrame: A frame containing the title bar
        """
        title_frame = QFrame(self)
        title_frame.setFixedHeight(40)  # Fixed height for title bar
        title_frame.setStyleSheet("background-color: rgba(0, 0, 0, 0.3); border-bottom: 2px solid #FF0000;")

        title_layout = QVBoxLayout(title_frame)
        title_layout.setContentsMargins(10, 5, 10, 5)
        title_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_label = QLabel(title, title_frame)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont(self.TITLE_FONT_FACE, self.TITLE_FONT_SIZE))
        title_label.setStyleSheet("color: #FF0000; font-weight: bold; background: transparent; border: none;")

        title_layout.addWidget(title_label)

        return title_frame
