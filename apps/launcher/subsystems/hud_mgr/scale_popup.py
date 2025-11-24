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

import json
import sys
import threading
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Dict, List

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QLabel, QPushButton, QSlider, QVBoxLayout,
                               QWidget)

from lib.button_debouncer import ButtonDebouncer
from lib.config import PngSettings
from lib.ipc import IpcParent

from ..base_mgr import PngAppMgrBase

if TYPE_CHECKING:
    from apps.launcher.gui import PngLauncherWindow

# -------------------------------------- CLASSES -----------------------------------------------------------------------

@dataclass
class SliderItem:
    label: str
    min: int
    max: int
    value: int
    callback: Callable[[int], None]

class ScalePopup(QWidget):
    """
    Generic floating popup for label+slider items.
    Items are provided via set_items(), using SliderItem dataclass.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("ScalePopup")
        self.setWindowFlags(
            Qt.Tool |
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._items: list[SliderItem] = []
        self._slider_rows = []

        # ---- Outer border ----
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        # ---- Inner container ----
        self.inner = QWidget(self)
        self.inner.setObjectName("ScalePopupInner")
        outer.addWidget(self.inner)

        self.inner_layout = QVBoxLayout(self.inner)
        self.inner_layout.setContentsMargins(12, 12, 12, 12)
        self.inner_layout.setSpacing(10)

        self.setFixedWidth(250)

        # ---- Styles ----
        self.setStyleSheet("""
            QWidget#ScalePopup {
                border: 2px solid rgba(180,180,180,200);
                border-radius: 8px;
            }

            QWidget#ScalePopupInner {
                background-color: rgba(32, 32, 32, 230);
                border-radius: 8px;
            }

            QLabel {
                color: white;
                font-size: 12px;
                background: transparent;
            }

            QSlider {
                background: transparent;
            }

            QSlider::groove:horizontal {
                height: 4px;
                background: rgba(255,255,255,50);
                border-radius: 2px;
            }

            QSlider::handle:horizontal {
                width: 12px;
                background: lightgray;
                border-radius: 6px;
            }
        """)

    # ------------------------------------------------------------------
    def set_items(self, items: list[SliderItem]):
        """Rebuild sliders from a strongly typed list."""

        # Remove old rows
        for row in self._slider_rows:
            row["label"].deleteLater()
            row["slider"].deleteLater()
        self._slider_rows.clear()

        self._items = items

        # Recreate rows
        for item in items:
            # Label
            lbl = QLabel(item.label)
            self.inner_layout.addWidget(lbl)

            # Slider
            slider = QSlider(Qt.Horizontal)
            slider.setMinimum(item.min)
            slider.setMaximum(item.max)
            slider.setValue(item.value)
            slider.valueChanged.connect(item.callback)

            self.inner_layout.addWidget(slider)

            self._slider_rows.append({
                "label": lbl,
                "slider": slider,
                "item": item
            })
