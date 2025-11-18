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
from typing import Callable, Dict, Optional
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QFrame, QSplitter, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt, QTimer, Signal, QObject, QSize
from PySide6.QtGui import QFont, QTextCursor, QCloseEvent, QIcon

from apps.launcher_v2.subsystems import BackendAppMgr, SaveViewerAppMgr, HudAppMgr
from lib.file_path import resolve_user_file
from lib.config import PngSettings, load_config_from_ini
from apps.launcher_v2.logger import get_rotating_logger
from .console import LogSignals, ConsoleWidget
from .subsys_row import SubsystemRow

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class PngLauncherWindow(QMainWindow):
    """Main launcher window"""

    def __init__(self,
                 ver_str: str,
                 logo_path: str,
                 settings_icon_path: str,
                 debug_mode: bool,
                 replay_mode: bool,
                 integration_test_mode: bool,
                 coverage_enabled: bool):

        self.app = QApplication(sys.argv)
        super().__init__()

        self.ver_str = ver_str
        self.logo_path = logo_path
        self.setWindowIcon(QIcon(self.logo_path))
        self.integration_test_mode = integration_test_mode
        self.settings_icon_path = settings_icon_path
        self.debug_mode = debug_mode
        self.log_file = Path("launcher.log")
        self.logger, self.log_file_path = get_rotating_logger(debug_mode=self.debug_mode)
        self.config_file = resolve_user_file("png_config.ini")
        self.settings: PngSettings = load_config_from_ini(self.config_file, logger=self.logger)

        # Common args
        args = ["--config-file", self.config_file]
        self.subsystems = [
           BackendAppMgr(
               window=self,
               settings=self.settings,
               args=args,
               debug_mode=debug_mode,
               replay_server=replay_mode,
               coverage_enabled=coverage_enabled
           ),
           SaveViewerAppMgr(
               window=self,
               settings=self.settings,
               args=args,
               debug_mode=debug_mode,
               coverage_enabled=coverage_enabled
           ),
           HudAppMgr(
               window=self,
               settings=self.settings,
               args=args,
               debug_mode=debug_mode,
               integration_test_mode=integration_test_mode,
               coverage_enabled=coverage_enabled
           )
        ]

        # Setup logging signals
        self.log_signals = LogSignals()
        self.log_signals.log_message.connect(self._write_log)

        self.init_icons()
        self.setup_ui()

    def _load_icon(self, path: Path) -> QIcon:
        """Load an icon"""
        ret = QIcon(str(path))
        if ret.isNull():
            self.logger.warning(f"Failed to load icon: {path}")
        else:
            self.logger.debug(f"Loaded icon successfully: {path}")
        return ret

    def init_icons(self):
        """Init the dict of icons"""
        icons_path_base = Path("assets") / "launcher-icons"
        self.icons: Dict[str, QIcon] = {
            "dashboard" : self._load_icon(icons_path_base / "dashboard.svg"),
            "lock" : self._load_icon(icons_path_base / "lock.svg"),
            "next-page" : self._load_icon(icons_path_base / "next-page.svg"),
            "open-file" : self._load_icon(icons_path_base / "open-file.svg"),
            "reset" : self._load_icon(icons_path_base / "reset.svg"),
            "save" : self._load_icon(icons_path_base / "save.svg"),
            "settings" : self._load_icon(icons_path_base / "settings.svg"),
            "show-hide" : self._load_icon(icons_path_base / "show-hide.svg"),
            "start" : self._load_icon(icons_path_base / "start.svg"),
            "stop" : self._load_icon(icons_path_base / "stop.svg"),
            "twitch" : self._load_icon(icons_path_base / "twitch.svg"),
            "unlock" : self._load_icon(icons_path_base / "unlock.svg"),
        }

    def get_icon(self, key: str) -> Optional[QIcon]:
        """Get icon by key"""
        return self.icons.get(key)


    def setup_ui(self):
        """Setup the main UI"""
        self.setWindowTitle("Pits n' Giggles")
        self.setMinimumSize(1000, 700)

        # Clean dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #252526;
            }
            QWidget {
                background-color: #252526;
                color: #d4d4d4;
            }
            QLabel {
                color: #d4d4d4;
            }
            QFrame {
                background-color: #1e1e1e;
                border: 1px solid #3e3e3e;
            }
        """)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Create console first
        self.console = ConsoleWidget()

        # Splitter for subsystems and console
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #3e3e3e;
            }
        """)

        # Subsystems area
        subsystems_widget = self.create_subsystems_area()
        splitter.addWidget(subsystems_widget)

        # Console area
        console_widget = self.create_console_area()
        splitter.addWidget(console_widget)

        # Set initial sizes (30% subsystems, 70% console)
        splitter.setSizes([250, 550])

        main_layout.addWidget(splitter)
        central_widget.setLayout(main_layout)

        # Initial log
        self.info_log(f"Pits n' Giggles {self.ver_str} started")

    def create_subsystems_area(self) -> QWidget:
        """Create the subsystems display area"""
        container = QFrame()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # Header
        header_label = QLabel("Subsystems")
        header_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        header_label.setStyleSheet("color: #d4d4d4; background-color: transparent; border: none;")
        layout.addWidget(header_label)

        # Add a separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #3e3e3e; border: none;")
        separator.setFixedHeight(1)
        layout.addWidget(separator)

        # Add subsystem rows
        for subsystem in self.subsystems:
            row = SubsystemRow(subsystem)
            layout.addWidget(row)

        layout.addStretch()
        container.setLayout(layout)
        return container

    def create_console_area(self) -> QWidget:
        """Create the console area"""
        container = QFrame()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # Header with clear button
        header_layout = QHBoxLayout()

        console_label = QLabel("Console Log")
        console_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        console_label.setStyleSheet("color: #d4d4d4; background-color: transparent; border: none;")
        header_layout.addWidget(console_label)

        header_layout.addStretch()

        clear_btn = QPushButton("Clear Log")
        clear_btn.setFixedHeight(25)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                color: #d4d4d4;
                border: 1px solid #3e3e3e;
                border-radius: 3px;
                padding: 4px 12px;
            }
            QPushButton:hover {
                background-color: #3e3e3e;
            }
        """)
        clear_btn.clicked.connect(self.console.clear)
        header_layout.addWidget(clear_btn)

        layout.addLayout(header_layout)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #3e3e3e; border: none;")
        separator.setFixedHeight(1)
        layout.addWidget(separator)

        # Console widget
        layout.addWidget(self.console)

        container.setLayout(layout)
        return container

    def auto_start_subsystems(self):
        """Auto-start subsystems marked for auto-start"""
        for subsystem in self.subsystems:
            if subsystem.start_by_default:
                self.info_log(f"Auto-starting {subsystem.display_name}...")
                subsystem.start("Initial auto-start")

    def info_log(self, message: str, is_child_message: bool = False):
        """Thread-safe info logging"""
        level = 'CHILD' if is_child_message else 'INFO'
        self.log_signals.log_message.emit(message, level)

    def debug_log(self, message: str):
        """Thread-safe debug logging"""
        if not self.debug_mode:
            return
        self.log_signals.log_message.emit(message, 'DEBUG')

    def warning_log(self, message: str):
        """Thread-safe warning logging"""
        self.log_signals.log_message.emit(message, 'WARNING')

    def error_log(self, message: str):
        """Thread-safe error logging"""
        self.log_signals.log_message.emit(message, 'ERROR')

    def _write_log(self, message: str, level: str):
        """Write log to console and file"""
        # Write to console widget
        self.console.append_log(message, level)

        # Map levels to logger methods
        log_map = {
            "DEBUG": self.logger.debug,
            "INFO": self.logger.info,
            "WARNING": self.logger.warning,
            "ERROR": self.logger.error,
            "CHILD": lambda msg: self.logger.info(f"[SUBSYS] {msg}")
        }

        # Get the appropriate log function (fallback = info)
        log_func = log_map.get(level, self.logger.info)

        # Write to rotating file logger
        log_func(message)

    def closeEvent(self, event: QCloseEvent):
        """Handle window close - stop all subsystems"""
        self.info_log("Shutting down launcher...")

        for subsystem in self.subsystems:
            if subsystem.is_running:
                self.info_log(f"Stopping {subsystem.display_name}...")
                subsystem.stop("Launcher shutting down")

        event.accept()

    def run(self):
        """Run the application"""
        self.auto_start_subsystems()
        self.show()
        sys.exit(self.app.exec())

    def process_events(self):
        """Process pending events in the application's event loop"""
        self.app.processEvents()

    def build_button(self, icon: QIcon, callback: Callable[[], None]) -> QPushButton:
        """Build a button with an icon and callback"""
        assert icon and not icon.isNull()

        btn = QPushButton()
        btn.setIcon(icon)
        btn.setIconSize(QSize(18, 18))   # adjust as needed

        btn.setFixedHeight(28)
        btn.setMinimumWidth(28)  # square button if you want
        btn.setFont(QFont("Arial", 9))
        btn.setStyleSheet("""
            QPushButton {
                background-color: #0e639c;
                color: white;
                border: 1px solid #0e639c;
                border-radius: 3px;
                padding: 4px;
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
        """)

        btn.clicked.connect(callback)
        return btn

    def set_button_state(self, button: QPushButton, enabled: bool):
        """Enable/disable a QPushButton."""
        button.setEnabled(enabled)

    def set_button_icon(self, button: QPushButton, icon: QIcon):
        """Set icon on a QPushButton."""
        button.setIcon(icon)

    def show_success(self, title: str, message: str):
        """Display a success/info message box."""
        QMessageBox.information(
            self,
            title,
            message
        )

    def show_error(self, title: str, message: str):
        """Display an error message box."""
        QMessageBox.critical(
            self,
            title,
            message
        )

    def select_file(self, title="Select File", filter="All Files (*.*)"):
        """Open a file dialog and return path or None."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            title,
            "",
            filter
        )
        return file_path or None
