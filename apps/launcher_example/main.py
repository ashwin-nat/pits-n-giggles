"""
Application Launcher
Clean, compact launcher for managing subsystem processes
"""

import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import List
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QFrame, QSplitter, QMenuBar, QMenu
)
from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtGui import QFont, QTextCursor, QAction

from .subsystem_manager import SubsystemManager
from .subsystems_examples import ServerSubsystem, HUDSubsystem, DashboardSubsystem


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


class SubsystemRow(QWidget):
    """Compact single-row widget for a subsystem"""

    def __init__(self, manager: SubsystemManager):
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
        for button_def in self.manager.get_buttons():
            btn = QPushButton(button_def['text'])
            btn.setFixedHeight(28)
            btn.setMinimumWidth(80)
            btn.setFont(QFont("Arial", 9))
            btn.setStyleSheet(self._get_button_style(button_def.get('primary', False)))
            btn.clicked.connect(button_def['command'])
            layout.addWidget(btn)

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


class LauncherMainWindow(QMainWindow):
    """Main launcher window"""

    def __init__(self):
        super().__init__()
        self.subsystems = [
            ServerSubsystem(start_by_default=True, console=self),
            HUDSubsystem(start_by_default=False, console=self),
            DashboardSubsystem(start_by_default=True, console=self),
        ]
        self.log_file = Path("launcher.log")

        # Setup logging signals
        self.log_signals = LogSignals()
        self.log_signals.log_message.connect(self._write_log)

        # Setup file logging
        self.setup_file_logging()

        self.setup_ui()

        # Auto-start subsystems marked for auto-start
        QTimer.singleShot(500, self.auto_start_subsystems)

    def setup_file_logging(self):
        """Setup file logging handler"""
        logging.basicConfig(
            filename=self.log_file,
            level=logging.DEBUG,
            format='[%(asctime)s] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

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

        # Menu bar
        # self.create_menu_bar()

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Create console first
        self.console = ConsoleWidget()

        # Splitter for subsystems and console
        splitter = QSplitter(Qt.Vertical)
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
        self.info_log("Application started")

    def create_menu_bar(self):
        """Create the menu bar"""
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #2d2d2d;
                color: #d4d4d4;
                border-bottom: 1px solid #3e3e3e;
            }
            QMenuBar::item:selected {
                background-color: #3e3e3e;
            }
            QMenu {
                background-color: #2d2d2d;
                color: #d4d4d4;
                border: 1px solid #3e3e3e;
            }
            QMenu::item:selected {
                background-color: #0e639c;
            }
        """)

        # File menu
        file_menu = menubar.addMenu("File")

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Help menu
        help_menu = menubar.addMenu("Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(lambda: self.info_log("Pits n' Giggles Launcher v2.0"))
        help_menu.addAction(about_action)

    def create_subsystems_area(self) -> QWidget:
        """Create the subsystems display area"""
        container = QFrame()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # Header
        header_label = QLabel("Subsystems")
        header_label.setFont(QFont("Arial", 11, QFont.Bold))
        header_label.setStyleSheet("color: #d4d4d4; background-color: transparent; border: none;")
        layout.addWidget(header_label)

        # Add a separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
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
        console_label.setFont(QFont("Arial", 11, QFont.Bold))
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
        separator.setFrameShape(QFrame.HLine)
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
                subsystem.start()

    def info_log(self, message: str, is_child_message: bool = False):
        """Thread-safe info logging"""
        level = 'CHILD' if is_child_message else 'INFO'
        self.log_signals.log_message.emit(message, level)

    def debug_log(self, message: str):
        """Thread-safe debug logging"""
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

        # Write to file
        log_func = getattr(logging, level.lower(), logging.info)
        log_func(message)

    def closeEvent(self, event):
        """Handle window close - stop all subsystems"""
        self.info_log("Shutting down launcher...")

        for subsystem in self.subsystems:
            if subsystem.is_running:
                self.info_log(f"Stopping {subsystem.display_name}...")
                subsystem.stop()

        event.accept()


def main():
    """Main entry point"""
    app = QApplication(sys.argv)

    # Example subsystems (you'll replace these with your actual implementations)


    window = LauncherMainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
