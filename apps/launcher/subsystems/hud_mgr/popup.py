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

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QPushButton, QSlider,
                               QVBoxLayout, QWidget)

# -------------------------------------- CLASSES -----------------------------------------------------------------------

@dataclass
class SliderItem:
    key: str
    label: str
    min: int
    max: int
    value: int
    tooltip: Optional[str] = None
    visible: bool = True

@dataclass
class SliderRow:
    item: SliderItem
    slider: QSlider
    label: QLabel
    value_label: QLabel
    row_widget: QWidget

class OverlaysAdjustPopup(QWidget):
    """
    Generic floating popup for label+slider items.
    Confirm-button-based architecture.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.confirm_callback: Optional[Callable[[Dict[str, int]], None]] = None
        self._items: List[SliderItem] = []
        self._slider_rows: list[SliderRow] = []

        self.setObjectName("ScalePopup")
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # ---- Outer wrapper ----
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        # ---- Inner container ----
        self.inner = QWidget(self)
        self.inner.setObjectName("ScalePopupInner")
        outer.addWidget(self.inner)

        self.inner_layout = QVBoxLayout(self.inner)
        self.inner_layout.setContentsMargins(12, 12, 12, 12)
        self.inner_layout.setSpacing(12)

        self.setFixedWidth(300)

        # ---- Confirm button ----
        self.confirm_btn = QPushButton("Confirm")
        self.confirm_btn.clicked.connect(self.on_confirm)
        self.confirm_btn.setFixedHeight(36)
        self.confirm_btn.setFont(QFont("Formula1"))

        # ---- Styles (updated) ----
        self.setStyleSheet("""
            QWidget#ScalePopup {
                border: 2px solid rgba(180,180,180,200);
                border-radius: 8px;
            }

            QWidget#ScalePopupInner {
                background-color: rgba(32, 32, 32, 255);
                border-radius: 8px;

                /* soft inner glow */
                border: 1px solid rgba(255,255,255,40);
            }

            QLabel {
                color: white;
                font-size: 14px;
                font-family: "Formula1";
                background: transparent;
            }

            /* === SLIDER STYLING (matching settings page) === */

            QSlider::groove:horizontal {
                border: 1px solid #3e3e3e;
                height: 6px;
                background-color: #1e1e1e;
                border-radius: 3px;
            }

            QSlider::handle:horizontal {
                background-color: #0e639c;
                border: 1px solid #0e639c;
                width: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }

            QSlider::handle:horizontal:hover {
                background-color: #1177bb;
            }
        """)

    # ---------------------------------------------------------
    def set_items(self, items: list[SliderItem]):
        # ---- Remove old rows cleanly ----
        for row in self._slider_rows:
            row_widget = row.row_widget
            row_widget.setParent(None)
            row_widget.deleteLater()
        self._slider_rows.clear()

        # ---- Rebuild ----
        self._items = items
        for item in items:
            row_widget = QWidget(self.inner)
            row_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
            row_widget.setStyleSheet("background: transparent; border: none;")
            row_widget.setVisible(item.visible)
            row_layout = QVBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(4)

            # Label
            label_row = QHBoxLayout()
            label_row.setContentsMargins(0, 0, 0, 0)
            label_row.setSpacing(6)

            label = QLabel(item.label, row_widget)
            label_row.addWidget(label)

            if item.tooltip:
                info = QLabel("ⓘ", row_widget)
                info.setToolTip(item.tooltip)
                info.setCursor(Qt.CursorShape.WhatsThisCursor)
                info.setAlignment(Qt.AlignmentFlag.AlignCenter)

                info.setStyleSheet("""
                    QLabel {
                        color: rgba(255,255,255,150);
                        font-size: 13px;
                    }
                    QLabel:hover {
                        color: white;
                    }
                """)

                label_row.addWidget(info)

            label_row.addStretch(1)
            row_layout.addLayout(label_row)

            # Slider + value
            h = QHBoxLayout()
            h.setContentsMargins(0, 0, 0, 0)
            h.setSpacing(8)

            slider = QSlider(Qt.Orientation.Horizontal, row_widget)
            slider.setMinimum(item.min)
            slider.setMaximum(item.max)
            slider.setValue(item.value)

            value_label = QLabel(str(item.value), row_widget)
            value_label.setMinimumWidth(40)
            value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            value_label.setFont(QFont("Formula1"))

            slider.valueChanged.connect(lambda v, lbl=value_label: lbl.setText(str(v)))

            h.addWidget(slider, 1)
            h.addWidget(value_label)

            row_layout.addLayout(h)
            self.inner_layout.addWidget(row_widget)

            self._slider_rows.append(SliderRow(
                item=item,
                slider=slider,
                label=label,
                value_label=value_label,
                row_widget=row_widget,
            ))

        # Add confirm button at end
        self.inner_layout.addWidget(self.confirm_btn)


    # ---------------------------------------------------------
    def set_confirm_callback(self, callback):
        self.confirm_callback = callback

    # ---------------------------------------------------------
    def on_confirm(self):
        values: Dict[str, int] = {
            row.item.key: row.slider.value()
            for row in self._slider_rows
        }
        if self.confirm_callback:
            self.confirm_callback(values)
