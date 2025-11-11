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


from PySide6.QtCore import QModelIndex, QRect
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (QStyledItemDelegate, QStyleOptionViewItem,
                               QTableWidget)

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class BorderDelegate(QStyledItemDelegate):
    """Custom delegate to draw borders around reference rows"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.reference_row = -1

    def set_reference_row(self, row: int):
        """Set which row should have a border"""
        self.reference_row = row

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        # First, paint the normal item
        super().paint(painter, option, index)

        # If this is the reference row, draw a white border around it
        if index.row() == self.reference_row:
            painter.save()
            painter.setPen(QPen(QColor("white"), 1))  # 2px white border

            # Get the table widget to calculate full row rect
            table = self.parent()
            if isinstance(table, QTableWidget):
                # Draw border only on the edges of the row
                rect: QRect = option.rect

                # Left edge (first column only)
                if index.column() == 0:
                    painter.drawLine(rect.left(), rect.top(), rect.left(), rect.bottom())

                # Right edge (last column only)
                if index.column() == table.columnCount() - 1:
                    painter.drawLine(rect.right(), rect.top(), rect.right(), rect.bottom())

                # Top and bottom edges (all columns)
                painter.drawLine(rect.left(), rect.top(), rect.right(), rect.top())
                painter.drawLine(rect.left(), rect.bottom(), rect.right(), rect.bottom())

            painter.restore()
