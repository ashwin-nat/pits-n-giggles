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

from typing import TYPE_CHECKING
from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout,
    QLabel, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

if TYPE_CHECKING:
    from .main_window import PngAppMgrBase

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class SubsystemCard(QFrame):
    """Modern card-style widget for a subsystem"""

    def __init__(self, manager: "PngAppMgrBase"):
        super().__init__()
        self.manager = manager
        self.setup_ui()

        # Connect manager signals to UI updates
        manager.status_changed.connect(self.update_status)

    def setup_ui(self):
        """Setup the subsystem card UI"""
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border: 1px solid #3e3e3e;
                border-radius: 8px;
            }
            QFrame:hover {
                border: 1px solid #0e639c;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # Header with name and status
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        # Name
        name_label = QLabel(self.manager.display_name.upper())
        name_label.setFont(QFont("Formula1", 11, QFont.Weight.Bold))
        name_label.setStyleSheet("color: #d4d4d4; background: transparent; border: none;")
        header_layout.addWidget(name_label)

        header_layout.addStretch()

        # Status badge
        self.status_label = QLabel(self.manager.status)
        self.status_label.setFont(QFont("Formula1", 9))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFixedHeight(22)
        self.status_label.setStyleSheet("""
            padding: 2px 12px;
            border-radius: 11px;
            background: transparent;
            border: none;
        """)
        self.update_status(self.manager.status)
        header_layout.addWidget(self.status_label)

        layout.addLayout(header_layout)

        # Buttons row
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(6)

        for button in self.manager.get_buttons():
            button.setFixedSize(32, 32)
            buttons_layout.addWidget(button)

            # Disable buttons at start. post_start should enable them
            self.manager.set_button_state(button, False)

        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

        self.setLayout(layout)

    def update_status(self, status: str):
        """Update the status badge"""
        status_styles = {
            'Stopped': {
                'bg': '#3e3e3e',
                'color': '#808080'
            },
            'Starting': {
                'bg': '#3d3d2a',
                'color': '#d7ba7d'
            },
            'Running': {
                'bg': '#1e3a32',
                'color': '#4ec9b0'
            },
            'Stopping': {
                'bg': '#3d3d2a',
                'color': '#d7ba7d'
            },
            'Crashed': {
                'bg': '#3d2a2a',
                'color': '#f48771'
            },
            'HTTP Port Conflict': {
                'bg': '#3d2a2a',
                'color': '#f48771'
            },
            'UDP Port Conflict': {
                'bg': '#3d2a2a',
                'color': '#f48771'
            },
            'Timed out': {
                'bg': '#3d2a2a',
                'color': '#f48771'
            },
            'Unsupported': {
                'bg': '#2a2a3d',
                'color': '#9cdcfe'
            }
        }

        style = status_styles.get(status, {'bg': '#3e3e3e', 'color': '#d4d4d4'})

        self.status_label.setText(status)
        self.status_label.setStyleSheet(f"""
            padding: 2px 12px;
            border-radius: 11px;
            background-color: {style['bg']};
            color: {style['color']};
            font-weight: bold;
            border: none;
        """)
