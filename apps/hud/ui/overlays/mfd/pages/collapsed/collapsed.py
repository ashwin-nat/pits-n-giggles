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
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QHBoxLayout, QLabel

from lib.assets_loader import load_icon
from apps.hud.ui.overlays.mfd.pages.base_page import BasePage, MfdPageBase

# -------------------------------------- CLASSES -----------------------------------------------------------------------

# class CollapsedPage(BasePage):
#     """Minimal page shown when MFD is collapsed."""

#     KEY = "collapsed"
#     FONT_FACE = "Formula1"
#     FONT_SIZE = 13

#     def __init__(self, parent: BasePage, logger: logging.Logger, scale_factor: float):
#         """Initialise the collapsed page.

#         Args:
#             parent (BasePage): Parent widget
#             logger (logging.Logger): Logger
#             scale_factor (float): Scale factor
#         """
#         super().__init__(parent, logger, "mfd.collapsed", scale_factor)

#         icon_base = Path("assets")
#         icon_path = icon_base / "logo.png"
#         page_text = "Pits n' Giggles MFD"

#         # Try loading icon
#         self.app_icon = load_icon(icon_path, self.logger.debug, self.logger.error)

#         if self.app_icon and not self.app_icon.isNull():
#             layout = QHBoxLayout()
#             layout.setContentsMargins(0, 0, 0, 0)
#             layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

#             # Icon
#             icon_label = QLabel(self)
#             pixmap = self.app_icon.pixmap(24, 24)  # adjust size if needed
#             icon_label.setPixmap(pixmap)
#             icon_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)

#             # Text
#             text_label = QLabel(page_text, self)
#             font = QFont(self.FONT_FACE, self.font_size)
#             text_label.setFont(font)
#             text_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)

#             # Combine
#             layout.addWidget(icon_label)
#             layout.addSpacing(6)
#             layout.addWidget(text_label)
#             self.page_layout.addLayout(layout)

#         else:
#             label = QLabel(page_text, self)
#             font = QFont(self.FONT_FACE, self.font_size)
#             label.setFont(font)
#             label.setAlignment(Qt.AlignmentFlag.AlignCenter)
#             self.page_layout.addWidget(label)

#     @property
#     def font_size(self) -> int:
#         """Get the font size based on the scale factor."""
#         return int(self.FONT_SIZE * self.scale_factor)

class CollapsedPage(MfdPageBase):
    KEY = "collapsed"
    QML_FILE: Path = Path(__file__).parent / "collapsed_page.qml"

    def __init__(self, root, logger):
        super().__init__(root, logger)

        # static text, set once
        self.overlay._root.setProperty("collapsedTitle", "Pits n' Giggles MFD")

