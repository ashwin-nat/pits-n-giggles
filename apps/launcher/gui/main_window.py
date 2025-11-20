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
import os
import sys
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from PySide6.QtCore import QSize, Qt, QThreadPool, QTimer, Signal
from PySide6.QtGui import QCloseEvent, QFont, QIcon
from PySide6.QtWidgets import (QApplication, QDialog, QFileDialog, QGridLayout,
                               QHBoxLayout, QLabel, QMainWindow, QMessageBox,
                               QPushButton, QSplitter, QVBoxLayout, QWidget)

from apps.launcher.logger import get_rotating_logger
from apps.launcher.subsystems import (BackendAppMgr, HudAppMgr, PngAppMgrBase,
                                      SaveViewerAppMgr)
from lib.config import PngSettings, load_config_migrated, save_config_to_json
from lib.file_path import resolve_user_file
from meta.meta import APP_NAME

from .changelog_window import ChangelogWindow
from .console import ConsoleWidget, LogSignals
from .settings import SettingsWindow
from .subsys_row import SubsystemCard
from .tasks import SettingsChangeTask, StopTask, UpdateCheckTask

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class ShutdownDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Please wait")
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint)

        layout = QVBoxLayout(self)
        label = QLabel("Shutting down ...")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        self.setFixedSize(220, 80)

class PngLauncherWindow(QMainWindow):
    """Main launcher window"""

    update_available = Signal()

    BUTTON_STYLESHEET = """
        QPushButton {
            background-color: #3e3e3e;
            border: 1px solid #4e4e4e;
            border-radius: 6px;
            padding: 0px;
        }
        QPushButton:hover {
            background-color: #0e639c;
            border: 1px solid #1177bb;
        }
        QPushButton:pressed {
            background-color: #0d5689;
        }
        QPushButton:disabled {
            background-color: #2d2d2d;
            border-color: #2d2d2d;
            opacity: 0.4;
        }
    """
    UPDATE_BLINK_STYLESHEET = """
        QPushButton#updates_btn {
            background-color: #d64a4a;
            border: 1px solid #aa0000;
            border-radius: 6px;
            padding: 0px;
        }
    """

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

        # Log colors
        self.log_colors = {
            'INFO': '#4ec9b0',      # Teal
            'DEBUG': '#808080',     # Gray
            'WARNING': '#d7ba7d',   # Yellow
            'ERROR': '#f48771',     # Red
            'CHILD': '#569cd6'      # Blue
        }

        self.ver_str = ver_str
        self.debug_mode = debug_mode

        self.console = None

        # Setup logging
        self.logger, self.log_file_path = get_rotating_logger(debug_mode=self.debug_mode)
        self.log_signals = LogSignals()
        self.log_signals.log_message.connect(self._write_log)
        self.subsystems_short_names = set()

        self.init_icons()
        self.logo_path = logo_path
        self.setWindowIcon(QIcon(self.logo_path))
        self.integration_test_mode = integration_test_mode
        self.settings_icon_path = settings_icon_path
        self.log_file = Path("launcher.log")
        self.config_file_legacy = resolve_user_file("png_config.ini")
        self.config_file_new = resolve_user_file("png_config.json")
        self.settings: PngSettings = load_config_migrated(self.config_file_legacy, self.config_file_new,
                                                          logger=self.logger)

        # Update button blink timer
        self.update_blink_timer = QTimer(self)
        self.update_blink_timer.setInterval(2000)
        self.update_blink_timer.timeout.connect(self._toggle_update_button_blink)
        self._update_blink_state = False
        self.update_available.connect(self.mark_update_button_available)
        self.newer_versions: List[Dict[str, Any]] = []

        # Common args
        args = ["--config-file", self.config_file_new]
        self.subsystems: List[PngAppMgrBase] = [
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
        for subsystem in self.subsystems:
            assert subsystem.short_name
            assert subsystem.short_name not in self.subsystems_short_names
            self.subsystems_short_names.add(subsystem.short_name)

        self.setup_ui()

    def _load_icon(self, relative_path: str) -> QIcon:
        """
        Load an icon that works in both dev and PyInstaller builds.

        Args:
            relative_path: Path to the icon file, relative to the project root or build bundle.

        Returns:
            QIcon: The loaded icon, or an empty QIcon if loading fails.
        """
        try:
            if hasattr(sys, "_MEIPASS"):
                # Running inside a PyInstaller bundle
                base_path = sys._MEIPASS
            else:
                # Running from source
                base_path = os.path.abspath(".")

            full_path = os.path.join(base_path, relative_path)
            icon = QIcon(full_path)
            self.debug_log(f"Loaded icon from {full_path}")
            return icon

        except Exception as e:  # pylint: disable=broad-except
            self.error_log(f"Failed to load icon from {relative_path}: {e}")
            return QIcon()

    def init_icons(self):
        """Init the dict of icons"""
        icons_path_base = Path("assets") / "launcher-icons"
        self.icons: Dict[str, QIcon] = {
            "arrow-down" : self._load_icon(icons_path_base / "arrow-down.svg"),
            "arrow-up" : self._load_icon(icons_path_base / "arrow-up.svg"),
            "dashboard" : self._load_icon(icons_path_base / "dashboard.svg"),
            "download" : self._load_icon(icons_path_base / "download.svg"),
            "discord" : self._load_icon(icons_path_base / "discord.svg"),
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
            "updates" : self._load_icon(icons_path_base / "updates.svg"),
            "website" : self._load_icon(icons_path_base / "website.svg"),
        }

    def get_icon(self, key: str) -> Optional[QIcon]:
        """Get icon by key"""
        return self.icons.get(key)


    def setup_ui(self):
        """Setup the main UI"""
        self.setWindowTitle(APP_NAME)
        self.thread_pool = QThreadPool.globalInstance()
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
        """)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Top bar with app info and global buttons
        top_bar_layout = QHBoxLayout()

        # Left side - App icon, name, and version
        app_info_layout = QHBoxLayout()
        app_info_layout.setSpacing(8)

        # App icon
        app_icon_label = QLabel()
        app_icon_label.setPixmap(QIcon(self.logo_path).pixmap(32, 32))
        app_icon_label.setFixedSize(32, 32)
        app_info_layout.addWidget(app_icon_label)

        # App name and version
        app_title_label = QLabel(f"{APP_NAME} - {self.ver_str}")
        app_title_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        app_title_label.setStyleSheet("color: #d4d4d4; background-color: transparent;")
        app_info_layout.addWidget(app_title_label)

        top_bar_layout.addLayout(app_info_layout)
        top_bar_layout.addStretch()

        # Right side - Global buttons
        global_buttons_layout = QHBoxLayout()
        global_buttons_layout.setSpacing(6)

        # Settings button
        self.settings_btn = self.build_button(self.get_icon("settings"), self.on_settings_clicked, "Settings")
        global_buttons_layout.addWidget(self.settings_btn)

        # Discord button
        self.discord_btn = self.build_button(self.get_icon("discord"), self.on_discord_clicked, "Join Discord")
        global_buttons_layout.addWidget(self.discord_btn)

        # Website button
        self.website_btn = self.build_button(self.get_icon("website"), self.on_website_clicked, "Tips n' Tricks")
        global_buttons_layout.addWidget(self.website_btn)

        # Updates button
        self.updates_btn = self.build_button(self.get_icon("updates"), self.on_updates_clicked,
                                             "What's New")
        self.updates_btn.setObjectName("updates_btn")
        global_buttons_layout.addWidget(self.updates_btn)

        # Download button
        self.download_btn = self.build_button(self.get_icon("download"), self.on_download_clicked,
                                              "Download Latest Releases")
        global_buttons_layout.addWidget(self.download_btn)

        top_bar_layout.addLayout(global_buttons_layout)
        main_layout.addLayout(top_bar_layout)

        # Create console first
        self.console = ConsoleWidget()

        # Splitter for subsystems and console
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #3e3e3e;
                height: 2px;
            }
        """)

        # Subsystems area
        subsystems_widget = self.create_subsystems_area()
        splitter.addWidget(subsystems_widget)

        # Console area
        console_widget = self.create_console_area()
        splitter.addWidget(console_widget)

        # Set initial sizes (25% subsystems, 75% console)
        splitter.setSizes([200, 600])

        main_layout.addWidget(splitter)
        central_widget.setLayout(main_layout)

        # Initial log
        self.info_log(f"{APP_NAME} {self.ver_str} started")

        # Check for updates in parallel (no-op in dev/beta mode)
        if self.ver_str != "dev" and "beta" not in self.ver_str:
            self.thread_pool.start(UpdateCheckTask(self, self.ver_str))

    def create_subsystems_area(self) -> QWidget:
        """Create the subsystems display area with grid layout"""
        container = QWidget()
        container.setStyleSheet("background-color: #252526;")

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Header
        header_label = QLabel("Subsystems")
        header_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header_label.setStyleSheet("color: #d4d4d4; background-color: transparent;")
        layout.addWidget(header_label)

        # Grid layout for cards
        grid_layout = QGridLayout()
        grid_layout.setSpacing(12)
        grid_layout.setContentsMargins(0, 0, 0, 0)

        # Number of subsystems per row
        NUM_SUBSYS_PER_ROW = 3

        # Add subsystem cards in a grid
        for idx, subsystem in enumerate(self.subsystems):
            row = idx // NUM_SUBSYS_PER_ROW
            col = idx % NUM_SUBSYS_PER_ROW
            card = SubsystemCard(subsystem)
            grid_layout.addWidget(card, row, col)

        layout.addLayout(grid_layout)
        layout.addStretch()

        container.setLayout(layout)
        return container

    def create_console_area(self) -> QWidget:
        """Create the console area"""
        container = QWidget()
        container.setStyleSheet("background-color: #252526;")

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Header with clear button
        header_layout = QHBoxLayout()

        console_label = QLabel("Console Log")
        console_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        console_label.setStyleSheet("color: #d4d4d4; background-color: transparent;")
        header_layout.addWidget(console_label)

        header_layout.addStretch()

        clear_btn = QPushButton("Clear")
        clear_btn.setFixedHeight(28)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                color: #d4d4d4;
                border: 1px solid #3e3e3e;
                border-radius: 4px;
                padding: 4px 16px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #3e3e3e;
                border: 1px solid #0e639c;
            }
            QPushButton:pressed {
                background-color: #1e1e1e;
            }
        """)
        clear_btn.clicked.connect(self.console.clear)
        header_layout.addWidget(clear_btn)

        layout.addLayout(header_layout)

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

    def format_log_message_colored_self(self, timestamp: str, message: str, level: str) -> str:
        """Format log message with color coding"""
        color = self.log_colors[level]
        formatted = f'<span style="color: #666;">[{timestamp}]</span> '
        formatted += f'<span style="color: {color}; font-weight: bold;">[{level}]</span> '
        formatted += f'<span style="color: #d4d4d4;">{message}</span>'
        return formatted

    def format_log_message_plain_self(self, timestamp: str, message: str, level: str) -> str:
        """Format log message"""
        return f'[{timestamp}] [{level}] {message}'

    def format_log_unknown_message_colored_child(self, timestamp: str, message: str, src: str) -> str:
        """Format unknown log message with color coding"""
        src_color = '#4ec9b0'
        level_color = self.log_colors['INFO']

        formatted = (
            f'<span style="color: #666;">[{timestamp}]</span> '
            f'<span style="color: {src_color}; font-weight: bold;">[{src}]</span> '
            f'<span style="color: {level_color};">[UNKNOWN]</span> '
            f'<span style="color: #d4d4d4;">{message.replace}</span>'
        )

        return formatted

    def format_log_message_colored_child(self,
                                        timestamp: str,
                                        message: str,
                                        level: str,
                                        src: str) -> str:
        """Format log message with color coding"""
        src_color = '#4ec9b0'
        level_color = self.log_colors[level]

        # Convert \n --> <br>
        safe_message = message.replace("\n", "<br>")
        # Wrap message to preserve indentation, spaces, tabs
        safe_message = f'<span style="white-space: pre;">{safe_message}</span>'

        formatted = (
            f'<span style="color: #666;">[{timestamp}]</span> '
            f'<span style="color: {src_color}; font-weight: bold;">[{src}]</span> '
            f'<span style="color: {level_color};">[{level}]</span>'
            f'<span style="color: #d4d4d4;">{safe_message}</span>'
        )

        return formatted

    def format_log_message_plain_child(self,
                                        timestamp: str,
                                        message: str,
                                        level: str,
                                        filename: str,
                                        lineno: int,
                                        src: str) -> str:
        """Format log message"""
        return f'[{timestamp}] [{src}] [{level}] [{filename}:{lineno}] {message}'

    def format_log_unknown_message_plain_child(self,
                                        timestamp: str,
                                        message: str,
                                        src: str) -> str:
        """Format log message"""
        return f'[{timestamp}] [{src}] [UNKNOWN] {message}'

    def info_log(self, message: str, src: str = ''):
        """Thread-safe info logging"""
        self.log_signals.log_message.emit(message, 'INFO', src)

    def debug_log(self, message: str):
        """Thread-safe debug logging"""
        if not self.debug_mode:
            return
        self.log_signals.log_message.emit(message, 'DEBUG', '')

    def warning_log(self, message: str):
        """Thread-safe warning logging"""
        self.log_signals.log_message.emit(message, 'WARNING', '')

    def error_log(self, message: str):
        """Thread-safe error logging"""
        self.log_signals.log_message.emit(message, 'ERROR', '')

    def _write_log(self, message: str, level: str, src: str):
        """Write log to console and file"""

        if src:
            self._write_log_child(message, src)
        else:
            self._write_log_self(message, level)

    def _write_log_child(self, message: str, src: str):
        """Write log to console and file. These log messages are from child processes"""

        # Unless its from some 3rd party lib, this will definitely be jsonl
        try:
            obj = json.loads(message)
            timestamp = obj['time']
            level = obj['level']
            filename = obj['filename']
            lineno = obj['lineno']
            text = obj['message']

            console_msg = self.format_log_message_colored_child(timestamp, text, level, src)
            log_msg = self.format_log_message_plain_child(timestamp, text, level, filename, lineno, src)

        except json.JSONDecodeError:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            console_msg = self.format_log_unknown_message_colored_child(timestamp, message, src)
            log_msg = self.format_log_unknown_message_plain_child(timestamp, message, src)

        # Write to console widget
        if self.console:
            self.console.append_log(console_msg)

        # Write to rotating file logger
        self.logger.info(log_msg)

    def _write_log_self(self, message: str, level: str):
        """Write log to console and file. These log messages are from the launcher process"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        console_msg = self.format_log_message_colored_self(timestamp, message, level)
        log_msg = self.format_log_message_plain_self(timestamp, message, level)

        # Write to console widget
        if self.console:
            self.console.append_log(console_msg)

        # Map levels to logger methods
        log_map = {
            "DEBUG": self.logger.debug,
            "INFO": self.logger.info,
            "WARNING": self.logger.warning,
            "ERROR": self.logger.error,
        }

        # Get the appropriate log function (fallback = info)
        log_func = log_map[level]

        # Write to rotating file logger
        log_func(log_msg)

    def closeEvent(self, event: QCloseEvent):
        self.info_log("Shutting down launcher...")

        # show the small modal window
        self.shutdown_dialog = ShutdownDialog(self)
        self.shutdown_dialog.show()
        self.process_events()

        pool = QThreadPool.globalInstance()
        tasks = []

        for subsystem in self.subsystems:
            self.info_log(f"Stopping {subsystem.display_name}...")
            task = StopTask(subsystem, "Launcher shutting down")
            tasks.append(task)
            pool.start(task)
            self.process_events()

        self.process_events()
        pool.waitForDone()
        event.accept()

    def run(self):
        """Run the application"""
        self.auto_start_subsystems()
        self.show()
        sys.exit(self.app.exec())

    def process_events(self):
        """Process pending events in the application's event loop"""
        self.app.processEvents()

    def build_button(self, icon: QIcon, callback: Callable[[], None], tooltip: str) -> QPushButton:
        """Build a button with an icon and callback"""
        assert icon and not icon.isNull(), f"Failed to load icon: {icon}"

        btn = QPushButton()
        btn.setIcon(icon)
        btn.setIconSize(QSize(20, 20))

        btn.setFixedSize(32, 32)
        btn.setStyleSheet(self.BUTTON_STYLESHEET)

        btn.clicked.connect(callback)
        self.set_button_tooltip(btn, tooltip)
        return btn

    def set_button_tooltip(self, button: QPushButton, tooltip: str):
        """Set tooltip for a QPushButton and store it for later use."""
        button.setProperty("button_tooltip", tooltip)
        button.setToolTip(tooltip)

    def set_button_state(self, button: QPushButton, enabled: bool):
        """Enable/disable a QPushButton and restore tooltip if previously set."""
        button.setEnabled(enabled)

        # Restore tooltip if it was previously configured
        tooltip = button.property("button_tooltip")
        if tooltip is not None:
            button.setToolTip(tooltip)

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

    def select_file(self, title="Select File", file_filter="All Files (*.*)"):
        """Open a file dialog and return path or None."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            title,
            "",
            file_filter
        )
        return file_path or None

    def on_settings_clicked(self):
        """Handle settings button click"""

        dialog = SettingsWindow(self, self.settings, self.icons, self.on_settings_changed)
        dialog.exec()

    def on_discord_clicked(self):
        """Handle Discord button click"""
        webbrowser.open("https://discord.gg/qQsSEHhW2V")

    def on_website_clicked(self):
        """Handle website button click"""
        webbrowser.open("https://pitsngiggles.com/blog")

    def on_updates_clicked(self):
        """Handle updates button click"""
        if self.newer_versions:
            dialog = ChangelogWindow(self, self.newer_versions, self.icons)
            dialog.exec()
        else:
            self.show_success("No Updates", "You are running the latest version!")

    def on_download_clicked(self):
        """Handle download button click"""
        webbrowser.open("https://pitsngiggles.com/releases")

    def on_settings_changed(self, new_settings: PngSettings):
        """Handle settings changed event"""
        try:
            save_config_to_json(new_settings, self.config_file_new)
        except Exception as e: # pylint: disable=broad-exception-caught
            self.error_log(f"Failed to save settings to {self.config_file_new}: {e}")

        self.info_log("Settings saved successfully")

        pool = QThreadPool.globalInstance()
        tasks = []

        for subsystem in self.subsystems:
            self.debug_log(f"On settings change for {subsystem.display_name}...")
            task = SettingsChangeTask(subsystem, new_settings)
            tasks.append(task)
            pool.start(task)

        pool.waitForDone()
        self.show_success("Settings Changed", "The settings have been saved and applied successfully.")


        self.settings = new_settings

    def mark_update_button_available(self):
        """Mark the update button as available"""
        if not self.update_blink_timer.isActive():
            self.update_blink_timer.start()

    def _toggle_update_button_blink(self):
        """Toggle the update button blink state"""
        self._update_blink_state = not self._update_blink_state
        if self._update_blink_state:
            self.updates_btn.setStyleSheet(self.UPDATE_BLINK_STYLESHEET)
        else:
            self.updates_btn.setStyleSheet(self.BUTTON_STYLESHEET)

