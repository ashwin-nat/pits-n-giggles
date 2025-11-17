# MIT License
#
# Copyright (c) [2024] [Ashwin Natarajan]
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
from typing import List
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QFrame, QSplitter
)
from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtGui import QFont, QTextCursor, QCloseEvent


# -------------------------------------- CLASSES -----------------------------------------------------------------------

class LogSignals(QObject):
    """Signals for thread-safe logging"""
    log_message = Signal(str, str)  # message, level


class ConsoleWidget(QTextEdit):
    """Custom console widget"""

    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setFont(QFont("Consolas", 9))

        # Clean dark theme styling
        self.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3e3e3e;
                padding: 8px;
            }
        """)

        # Log colors
        self.colors = {
            'INFO': '#4ec9b0',      # Teal
            'DEBUG': '#808080',     # Gray
            'WARNING': '#d7ba7d',   # Yellow
            'ERROR': '#f48771',     # Red
            'CHILD': '#569cd6'      # Blue
        }

    def append_log(self, message: str, level: str = 'INFO'):
        """Append a log message with color coding"""

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        color = self.colors.get(level, '#d4d4d4')

        formatted = f'<span style="color: #666;">[{timestamp}]</span> '
        formatted += f'<span style="color: {color}; font-weight: bold;">[{level}]</span> '
        formatted += f'<span style="color: #d4d4d4;">{message}</span>'

        self.append(formatted)
        self.moveCursor(QTextCursor.End)
