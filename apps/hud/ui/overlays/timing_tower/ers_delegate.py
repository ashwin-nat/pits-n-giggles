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

from PySide6.QtCore import QModelIndex, QRect, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class ERSDelegate(QStyledItemDelegate):
    """Custom delegate to paint ERS cell with vertical color bar"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ers_colors = {
            "None": QColor("#888888"),
            "Medium": QColor("#ffff00"),
            "Hotlap": QColor("#00ff00"),
            "Overtake": QColor("#ff0000")
        }
        self.default_color = QColor("#888888")
        self.reference_row = -1

    def set_reference_row(self, row: int):
        """Set which row should have a border"""
        self.reference_row = row

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        # Get the ERS mode color from item data
        ers_mode = index.data(Qt.ItemDataRole.UserRole)
        if ers_mode is None:
            super().paint(painter, option, index)
            return

        ers_mode_color = self.ers_colors.get(ers_mode, self.default_color)
        painter.save()
        rect: QRect = option.rect

        # Fill background FIRST
        bg_color = QColor(25, 25, 25, 180)
        painter.fillRect(rect, bg_color)

        # Draw vertical bar on the left (15% width) ON TOP of background
        bar_width = int(rect.width() * 0.15)
        bar_rect = rect.adjusted(0, 0, -rect.width() + bar_width, 0)
        painter.fillRect(bar_rect, ers_mode_color)

        # Draw thin black border around the bar
        painter.setPen(QPen(QColor("black"), 1))
        painter.drawRect(bar_rect.adjusted(0, 0, -1, -1))  # Adjust to stay within bounds

        # Draw text in the remaining space (after the color bar)
        painter.setPen(QColor("white"))

        # Get font from item data or create a new one
        font = index.data(Qt.ItemDataRole.FontRole)
        if not font:
            font = QFont()
        font.setPointSize(11)  # Match the size from _create_table_item
        font.setBold(True)
        painter.setFont(font)

        text_rect = rect.adjusted(bar_width, 0, 0, 0)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, index.data(Qt.ItemDataRole.DisplayRole))

        # Draw border if this is the reference row
        if index.row() == self.reference_row:
            painter.setPen(QPen(QColor("white"), 1))
            rect = rect
            # Right edge (this is the last column)
            painter.drawLine(rect.right() - 2, rect.top(), rect.right() - 2, rect.bottom())
            # Top and bottom edges
            painter.drawLine(rect.left(), rect.top(), rect.right(), rect.top())
            painter.drawLine(rect.left(), rect.bottom(), rect.right(), rect.bottom())

        painter.restore()
