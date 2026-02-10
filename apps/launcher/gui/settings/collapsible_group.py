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

from typing import Dict, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class CollapsibleGroup(QWidget):
    def __init__(self, title: str, icon_map: Dict[str, QIcon], parent: Optional[QWidget] = None):
        """A collapsible group widget for organizing settings in the launcher.

        Args:
            title: The title of the group.
            icon_map: A dictionary mapping icon names to icons.
            parent: The parent widget.
        """
        super().__init__(parent)
        self._icon_map = icon_map
        self._is_collapsed = False

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 4, 0, 4)
        outer_layout.setSpacing(0)

        header = QFrame()
        header.setFrameShape(QFrame.Shape.StyledPanel)
        header.setCursor(Qt.CursorShape.PointingHandCursor)
        header.setStyleSheet("""
            QFrame {
                background-color: #2d2d30;
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                padding: 2px;
            }
            QFrame:hover {
                background-color: #37373d;
                border-color: #0e639c;
            }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 6, 10, 6)
        header_layout.setSpacing(8)

        self._toggle_label = QLabel()
        self._toggle_label.setFixedSize(20, 20)
        header_layout.addWidget(self._toggle_label)

        title_label = QLabel(title)
        title_label.setFont(QFont("Roboto", 10, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #cccccc; background: transparent; border: none;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        header.mousePressEvent = self._on_header_clicked  # local, but now encapsulated

        outer_layout.addWidget(header)

        self._content_wrapper = QWidget()
        self._content_wrapper.setStyleSheet("background-color: #1e1e1e;")
        self._content_layout = QVBoxLayout(self._content_wrapper)
        self._content_layout.setContentsMargins(12, 8, 8, 8)
        self._content_layout.setSpacing(8)
        outer_layout.addWidget(self._content_wrapper)

        self._update_icon()

    @property
    def content_layout(self) -> QVBoxLayout:
        return self._content_layout

    def set_collapsed(self, collapsed: bool) -> None:
        self._is_collapsed = collapsed
        self._content_wrapper.setVisible(not collapsed)
        self._update_icon()

    def is_collapsed(self) -> bool:
        return self._is_collapsed

    def expand_if_has_visible_children(self) -> None:
        for i in range(self._content_layout.count()):
            w = self._content_layout.itemAt(i).widget()
            if w is not None and w.isVisible():
                if self._is_collapsed:
                    self.set_collapsed(False)
                return

    def _update_icon(self) -> None:
        key = 'caret-right' if self._is_collapsed else 'caret-down'
        self._toggle_label.setPixmap(self._icon_map[key].pixmap(16, 16))

    def _on_header_clicked(self, _event) -> None:
        self.set_collapsed(not self._is_collapsed)
