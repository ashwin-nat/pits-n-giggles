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

import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QFrame, QSplitter
)
from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtGui import QFont, QTextCursor, QCloseEvent

if TYPE_CHECKING:
    from .main_window import PngAppMgrBase

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class SubsystemRow(QWidget):
    """Compact single-row widget for a subsystem"""

    def __init__(self, manager: "PngAppMgrBase"):
        super().__init__()
        self.manager = manager
        self.setup_ui()

        # Connect manager signals to UI updates
        manager.status_changed.connect(self.update_status)

    def setup_ui(self):
        """Setup the subsystem row UI"""
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)

        # Name label (fixed width)
        name_label = QLabel(f"{self.manager.display_name}:")
        name_label.setFont(QFont("Arial", 10))
        name_label.setFixedWidth(100)
        name_label.setStyleSheet("color: #d4d4d4;")
        layout.addWidget(name_label)

        # Status indicator (fixed width)
        self.status_label = QLabel(self.manager.status)
        self.status_label.setFont(QFont("Arial", 9))
        self.status_label.setFixedWidth(100)
        self.update_status(self.manager.status)
        layout.addWidget(self.status_label)

        # Buttons
        for button in self.manager.get_buttons():
            layout.addWidget(button)

        layout.addStretch()
        self.setLayout(layout)

    def update_status(self, status: str):
        """Update the status indicator"""
        color_map = {
            'Stopped': '#808080',
            'Starting': '#d7ba7d',
            'Running': '#4ec9b0',
            'Stopping': '#d7ba7d',
            'Crashed': '#f48771',
            'HTTP Port Conflict': '#f48771',
            'UDP Port Conflict': '#f48771',
            'Timed out': '#f48771'
        }

        color = color_map.get(status, '#d4d4d4')
        self.status_label.setText(status)
        self.status_label.setStyleSheet(f"color: {color}; font-weight: bold;")

    def _get_button_style(self, is_primary: bool) -> str:
        if is_primary:
            return """
                QPushButton {
                    background-color: #0e639c;
                    color: white;
                    border: 1px solid #0e639c;
                    border-radius: 3px;
                    padding: 4px 12px;
                }
                QPushButton:hover {
                    background-color: #1177bb;
                }
                QPushButton:pressed {
                    background-color: #0d5689;
                }
                QPushButton:disabled {
                    background-color: #3e3e3e;
                    color: #808080;
                    border-color: #3e3e3e;
                }
            """
        else:
            return """
                QPushButton {
                    background-color: #2d2d2d;
                    color: #d4d4d4;
                    border: 1px solid #3e3e3e;
                    border-radius: 3px;
                    padding: 4px 12px;
                }
                QPushButton:hover {
                    background-color: #3e3e3e;
                    border-color: #0e639c;
                }
                QPushButton:pressed {
                    background-color: #1e1e1e;
                }
                QPushButton:disabled {
                    background-color: #1e1e1e;
                    color: #808080;
                    border-color: #2d2d2d;
                }
            """

