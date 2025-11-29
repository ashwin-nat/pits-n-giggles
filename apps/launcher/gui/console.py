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

from PySide6.QtWidgets import QTextEdit
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QFont, QTextCursor


# -------------------------------------- CLASSES -----------------------------------------------------------------------

class LogSignals(QObject):
    """Signals for thread-safe logging"""
    log_message = Signal(str, str, str)  # message, level, src


class ConsoleWidget(QTextEdit):
    """Custom console widget with copy support and scroll lock"""

    # Maximum number of lines to keep in the console
    MAX_LINES = 1000

    # Signal emitted when scroll lock state changes
    scroll_lock_changed = Signal(bool)  # True = locked, False = auto-scroll

    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setFont(QFont("Consolas", 9))

        # Enable text interaction for copying
        self.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse |
            Qt.TextInteractionFlag.TextSelectableByKeyboard
        )

        # Clean dark theme styling
        self.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3e3e3e;
                padding: 8px;
            }
        """)

        # Scroll lock state
        self._auto_scroll = True
        self._user_scrolled = False

        # Connect to scrollbar to detect user scrolling
        scrollbar = self.verticalScrollBar()
        scrollbar.valueChanged.connect(self._on_scroll_changed)

    def _on_scroll_changed(self, value):
        """Detect when user scrolls up"""
        scrollbar = self.verticalScrollBar()

        # If user scrolls away from bottom, enable scroll lock
        if value < scrollbar.maximum() and not self._user_scrolled:
            self._user_scrolled = True
            self._auto_scroll = False
            self.scroll_lock_changed.emit(True)

        # If user scrolls back to bottom, re-enable auto-scroll
        elif value == scrollbar.maximum() and self._user_scrolled:
            self._user_scrolled = False
            self._auto_scroll = True
            self.scroll_lock_changed.emit(False)

    def append_log(self, message: str):
        """Append a log message with color coding"""

        self.append(message)

        # Enforce line limit
        doc = self.document()
        if doc.blockCount() > self.MAX_LINES:
            # Remove excess lines from the top
            cursor = QTextCursor(doc)
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            for _ in range(doc.blockCount() - self.MAX_LINES):
                cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
                cursor.movePosition(QTextCursor.MoveOperation.NextBlock,
                                  QTextCursor.MoveMode.KeepAnchor)
                cursor.removeSelectedText()

        # Only auto-scroll if enabled
        if self._auto_scroll:
            self.moveCursor(QTextCursor.MoveOperation.End)
            self.ensureCursorVisible()

    def enable_auto_scroll(self):
        """Manually enable auto-scroll and scroll to bottom"""
        self._auto_scroll = True
        self._user_scrolled = False
        self.moveCursor(QTextCursor.MoveOperation.End)
        self.ensureCursorVisible()
        self.scroll_lock_changed.emit(False)

    def is_auto_scroll_enabled(self) -> bool:
        """Check if auto-scroll is currently enabled"""
        return self._auto_scroll
