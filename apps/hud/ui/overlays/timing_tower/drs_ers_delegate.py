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

class DrsErsDelegate(QStyledItemDelegate):
    """Custom delegate to paint ERS cell with vertical color bar"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ers_colors = {
            "None": QColor("#888888"),
            "Medium": QColor("#ffff00"),
            "Hotlap": QColor("#00ff00"),
            "Overtake": QColor("#ff0000")
        }
        self.drs_colors = {
            True: QColor("#00ff00"),
            False: QColor("#888888")
        }
        self.default_color = QColor("#888888")
        self.reference_row = -1

    def set_reference_row(self, row: int):
        """Set which row should have a border"""
        self.reference_row = row

    def _draw_background(self, painter: QPainter, rect: QRect) -> None:
        """Fill the cell background"""
        bg_color = QColor(25, 25, 25, 180)
        painter.fillRect(rect, bg_color)

    def _draw_vertical_bar(self, painter: QPainter, bar_rect: QRect, color: QColor) -> None:
        """Draw a vertical colored bar with border"""
        painter.fillRect(bar_rect, color)
        painter.setPen(QPen(QColor("black"), 1))
        painter.drawRect(bar_rect.adjusted(0, 0, -1, -1))

    def _draw_text(self, painter: QPainter, text_rect: QRect, text: str, font: QFont = None) -> None:
        """Draw centered text with specified font"""
        painter.setPen(QColor("white"))
        if not font:
            font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, text)

    def _draw_reference_border(self, painter: QPainter, rect: QRect) -> None:
        """Draw white border for reference row"""
        painter.setPen(QPen(QColor("white"), 1))
        painter.drawLine(rect.right() - 2, rect.top(), rect.right() - 2, rect.bottom())
        painter.drawLine(rect.left(), rect.top(), rect.right(), rect.top())
        painter.drawLine(rect.left(), rect.bottom(), rect.right(), rect.bottom())

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """Paint the cell"""
        args = index.data(Qt.ItemDataRole.UserRole)
        ers_mode = args["ers-mode"]
        drs = args["drs"]

        assert ers_mode is not None
        assert drs is not None

        ers_mode_color = self.ers_colors.get(ers_mode, self.default_color)
        drs_color = self.drs_colors.get(drs, self.default_color)

        painter.save()
        rect: QRect = option.rect
        bar_width = int(rect.width() * 0.15)

        # Draw background
        self._draw_background(painter, rect)

        # Draw ERS bar on the left
        ers_bar_rect = rect.adjusted(0, 0, -rect.width() + bar_width, 0)
        self._draw_vertical_bar(painter, ers_bar_rect, ers_mode_color)

        # Draw ERS percentage text in the middle
        remaining_rect = rect.adjusted(bar_width, 0, 0, 0)
        text_rect = remaining_rect.adjusted(0, 0, -bar_width, 0)
        text = index.data(Qt.ItemDataRole.DisplayRole)
        font = index.data(Qt.ItemDataRole.FontRole)
        self._draw_text(painter, text_rect, text, font)

        # Draw DRS bar on the right
        drs_bar_rect = QRect(rect.right() - bar_width, rect.top(), bar_width, rect.height())
        self._draw_vertical_bar(painter, drs_bar_rect, drs_color)

        # Draw reference row border if applicable
        if index.row() == self.reference_row:
            self._draw_reference_border(painter, rect)

        painter.restore()
