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

import logging
from pathlib import Path
from typing import Any, Dict, List

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QProgressBar,
                               QVBoxLayout, QWidget)

from apps.hud.ui.overlays.mfd.pages.base_page import BasePage

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class FuelInfoPage(BasePage):
    """Modern fuel statistics display for MFD."""

    FONT_FACE = "Montserrat"
    FONT_SIZE_TITLE = 9
    FONT_SIZE_VALUE = 16
    FONT_SIZE_UNIT = 9
    FONT_SIZE_LABEL = 8

    # Color scheme
    COLOR_BG = "#1a1a1a"
    COLOR_PRIMARY = "#00ff88"
    COLOR_WARNING = "#ffaa00"
    COLOR_DANGER = "#ff4444"
    COLOR_TEXT = "#e0e0e0"
    COLOR_TEXT_DIM = "#808080"
    COLOR_BORDER = "#333333"

    # Fuel constants
    MIN_FUEL = 0.2  # Minimum fuel threshold in laps

    def __init__(self, parent: QWidget, logger: logging.Logger):
        super().__init__(parent, logger, title="FUEL INFO")
        self.overlay_id = "mfd.fuel_info"
        self._last_processed_samples: List[Dict[str, Any]] = []

        # Load fuel icon
        icon_base = Path("assets")
        icon_path = icon_base / "overlays" / "fuel-pump.svg"
        self.fuel_icon = self.load_icon(str(icon_path))
        if self.fuel_icon and not self.fuel_icon.isNull():
            self.logger.debug(f"{self.overlay_id} | Fuel icon loaded")
        else:
            self.logger.warning(f"{self.overlay_id} | Failed to load fuel icon")

        # Initialize widget references to None
        self.fuel_in_tank_widget = None
        self.fuel_progress_bar = None
        self.curr_rate_widget = None
        self.last_lap_widget = None
        self.target_avg_widget = None
        self.target_next_widget = None
        self.surplus_laps_widget = None

        self._build_ui()
        self.logger.info(f"{self.overlay_id} | Fuel info widget initialized")

    def _build_ui(self):
        """Build the fuel info UI."""
        # Use the existing page_layout from BasePage instead of creating a new one
        # Clear margins set by parent and apply our own to the content
        content_widget = QWidget()
        main_layout = QVBoxLayout(content_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        # Top row: Fuel in tank and capacity
        top_row = self._create_top_row()
        main_layout.addLayout(top_row)

        # Separator
        separator1 = self._create_separator()
        main_layout.addWidget(separator1)

        # Middle row: Current consumption and last lap
        middle_row = self._create_middle_row()
        main_layout.addLayout(middle_row)

        # Separator
        separator2 = self._create_separator()
        main_layout.addWidget(separator2)

        # Bottom row: Target rates and surplus laps
        bottom_row = self._create_bottom_row()
        main_layout.addLayout(bottom_row)

        main_layout.addStretch()

        # Add the content widget to the page layout from BasePage
        self.page_layout.addWidget(content_widget)

    def _create_separator(self) -> QFrame:
        """Create a horizontal separator line."""
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(f"background-color: {self.COLOR_BORDER};")
        line.setFixedHeight(1)
        return line

    def _create_top_row(self) -> QHBoxLayout:
        """Create top row with fuel in tank (icon, progress bar, value)."""
        layout = QHBoxLayout()
        layout.setSpacing(12)

        # Fuel in tank with icon, progress bar, and value
        self.fuel_in_tank_widget = self._create_fuel_display_widget()
        layout.addWidget(self.fuel_in_tank_widget)

        return layout

    def _create_middle_row(self) -> QHBoxLayout:
        """Create middle row with current rate and last lap usage."""
        layout = QHBoxLayout()
        layout.setSpacing(12)

        # Current fuel rate
        self.curr_rate_widget = self._create_stat_widget(
            "CURRENT RATE", "0.000", "kg/lap"
        )
        layout.addWidget(self.curr_rate_widget)

        # Last lap used
        self.last_lap_widget = self._create_stat_widget(
            "LAST LAP", "0.000", "kg"
        )
        layout.addWidget(self.last_lap_widget)

        return layout

    def _create_bottom_row(self) -> QHBoxLayout:
        """Create bottom row with target rates and surplus."""
        layout = QHBoxLayout()
        layout.setSpacing(8)

        # Target average rate
        self.target_avg_widget = self._create_stat_widget(
            "TARGET AVG", "0.000", "kg/lap", compact=True
        )
        layout.addWidget(self.target_avg_widget)

        # Target next lap
        self.target_next_widget = self._create_stat_widget(
            "TARGET NEXT", "0.000", "kg/lap", compact=True
        )
        layout.addWidget(self.target_next_widget)

        # Surplus laps
        self.surplus_laps_widget = self._create_stat_widget(
            "SURPLUS", "0", "laps", compact=True
        )
        layout.addWidget(self.surplus_laps_widget)

        return layout

    def _create_fuel_display_widget(self) -> QFrame:
        """Create the fuel display with icon, progress bar, and value."""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.COLOR_BG};
                border: 1px solid {self.COLOR_BORDER};
                border-radius: 6px;
            }}
        """)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        # Label
        label_widget = QLabel("FUEL IN TANK")
        label_font = QFont(self.FONT_FACE, self.FONT_SIZE_LABEL)
        label_font.setWeight(QFont.Medium)
        label_widget.setFont(label_font)
        label_widget.setStyleSheet(f"color: {self.COLOR_TEXT_DIM}; border: none;")
        label_widget.setAlignment(Qt.AlignLeft)
        layout.addWidget(label_widget)

        # Horizontal layout for icon, progress bar, and value
        content_layout = QHBoxLayout()
        content_layout.setSpacing(8)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # Icon or emoji fallback
        icon_label = QLabel()
        if self.fuel_icon and not self.fuel_icon.isNull():
            icon_label.setPixmap(self.fuel_icon.pixmap(24, 24))
        else:
            icon_label.setText("⛽")
            icon_label.setFont(QFont(self.FONT_FACE, 18))
            icon_label.setStyleSheet(f"color: {self.COLOR_PRIMARY}; border: none;")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setFixedSize(24, 24)
        content_layout.addWidget(icon_label)

        # Progress bar
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        progress_bar.setValue(0)
        progress_bar.setTextVisible(False)
        progress_bar.setFixedHeight(20)
        progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {self.COLOR_BORDER};
                border-radius: 4px;
                background-color: #0a0a0a;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {self.COLOR_PRIMARY};
                border-radius: 3px;
            }}
        """)
        self.fuel_progress_bar = progress_bar
        content_layout.addWidget(progress_bar, stretch=1)

        # Value and unit
        value_unit_layout = QHBoxLayout()
        value_unit_layout.setSpacing(4)
        value_unit_layout.setContentsMargins(0, 0, 0, 0)

        value_widget = QLabel("0.000")
        value_font = QFont(self.FONT_FACE, self.FONT_SIZE_VALUE)
        value_font.setWeight(QFont.Bold)
        value_widget.setFont(value_font)
        value_widget.setStyleSheet(f"color: {self.COLOR_PRIMARY}; border: none;")
        value_unit_layout.addWidget(value_widget)

        unit_widget = QLabel("kg")
        unit_font = QFont(self.FONT_FACE, self.FONT_SIZE_UNIT)
        unit_font.setWeight(QFont.Medium)
        unit_widget.setFont(unit_font)
        unit_widget.setStyleSheet(f"color: {self.COLOR_TEXT_DIM}; border: none;")
        unit_widget.setAlignment(Qt.AlignBottom)
        value_unit_layout.addWidget(unit_widget)

        content_layout.addLayout(value_unit_layout)
        layout.addLayout(content_layout)

        # Store references
        frame.value_label = value_widget
        frame.unit_label = unit_widget

        return frame

    def _create_stat_widget(self, label: str, value: str, unit: str,
                           large: bool = False, compact: bool = False) -> QFrame:
        """Create a styled stat display widget."""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.COLOR_BG};
                border: 1px solid {self.COLOR_BORDER};
                border-radius: 6px;
            }}
        """)

        layout = QVBoxLayout(frame)
        padding = 6 if compact else 10
        layout.setContentsMargins(padding, padding, padding, padding)
        layout.setSpacing(2 if compact else 4)

        # Label
        label_widget = QLabel(label)
        label_font = QFont(self.FONT_FACE, self.FONT_SIZE_LABEL)
        label_font.setWeight(QFont.Medium)
        label_widget.setFont(label_font)
        label_widget.setStyleSheet(f"color: {self.COLOR_TEXT_DIM}; border: none;")
        label_widget.setAlignment(Qt.AlignLeft)
        layout.addWidget(label_widget)

        # Value container
        value_layout = QHBoxLayout()
        value_layout.setSpacing(4)
        value_layout.setContentsMargins(0, 0, 0, 0)

        # Value
        value_widget = QLabel(value)
        value_font = QFont(self.FONT_FACE, self.FONT_SIZE_VALUE if large else 14)
        value_font.setWeight(QFont.Bold)
        value_widget.setFont(value_font)
        value_widget.setStyleSheet(f"color: {self.COLOR_PRIMARY}; border: none;")
        value_layout.addWidget(value_widget)

        # Unit
        unit_widget = QLabel(unit)
        unit_font = QFont(self.FONT_FACE, self.FONT_SIZE_UNIT)
        unit_font.setWeight(QFont.Medium)
        unit_widget.setFont(unit_font)
        unit_widget.setStyleSheet(f"color: {self.COLOR_TEXT_DIM}; border: none;")
        unit_widget.setAlignment(Qt.AlignBottom)
        value_layout.addWidget(unit_widget)

        value_layout.addStretch()
        layout.addLayout(value_layout)

        # Store references for updates
        frame.value_label = value_widget
        frame.unit_label = unit_widget

        return frame

    def update(self, data: Dict[str, Any]) -> None:
        """Update fuel information display."""
        ref_row = self._get_ref_row(data)
        if not ref_row:
            return

        telemetry_settings = ref_row["driver-info"]["telemetry-setting"]
        if telemetry_settings != "Public":
            self._show_telemetry_disabled()
            return

        fuel_info = ref_row["fuel-info"]
        self.logger.debug(f"{self.overlay_id} | Received fuel info: {fuel_info}")

        # Extract values (may be None on first lap)
        fuel_capacity = fuel_info.get("fuel-capacity", 0)
        fuel_in_tank = fuel_info.get("fuel-in-tank", 0)
        curr_fuel_rate = fuel_info.get("curr-fuel-rate")
        last_lap_used = fuel_info.get("last-lap-fuel-used")
        surplus_laps = fuel_info.get("surplus-laps-png")
        target_rate_avg = fuel_info.get("target-fuel-rate-average")
        target_rate_next_lap = fuel_info.get("target-fuel-rate-next-lap")

        # Update displays - handle None values
        self._update_fuel_display(fuel_in_tank, fuel_capacity)

        # Handle potentially None values with fallback display
        if curr_fuel_rate is not None:
            self._update_stat(self.curr_rate_widget, f"{curr_fuel_rate:.3f}",
                             self.COLOR_PRIMARY)
        else:
            self._update_stat(self.curr_rate_widget, "---", self.COLOR_TEXT_DIM)

        if last_lap_used is not None:
            self._update_stat(self.last_lap_widget, f"{last_lap_used:.3f}",
                             self.COLOR_PRIMARY)
        else:
            self._update_stat(self.last_lap_widget, "---", self.COLOR_TEXT_DIM)

        if target_rate_avg is not None:
            self._update_stat(self.target_avg_widget, f"{target_rate_avg:.3f}",
                             self.COLOR_TEXT)
        else:
            self._update_stat(self.target_avg_widget, "---", self.COLOR_TEXT_DIM)

        if target_rate_next_lap is not None:
            self._update_stat(self.target_next_widget, f"{target_rate_next_lap:.3f}",
                             self.COLOR_TEXT)
        else:
            self._update_stat(self.target_next_widget, "---", self.COLOR_TEXT_DIM)

        if surplus_laps is not None:
            self._update_stat(self.surplus_laps_widget, f"{surplus_laps:.3f}",
                             self._get_surplus_color(surplus_laps))
        else:
            self._update_stat(self.surplus_laps_widget, "---", self.COLOR_TEXT_DIM)

    def _update_fuel_display(self, fuel_in_tank: float, fuel_capacity: float):
        """Update the fuel display with icon, progress bar, and value."""
        try:
            if hasattr(self.fuel_in_tank_widget, 'value_label') and self.fuel_in_tank_widget.value_label is not None:
                # Update value (always green)
                self.fuel_in_tank_widget.value_label.setText(f"{fuel_in_tank:.3f}")
                self.fuel_in_tank_widget.value_label.setStyleSheet(f"color: {self.COLOR_PRIMARY}; border: none;")

                # Update progress bar (always green)
                if self.fuel_progress_bar is not None:
                    percentage = int((fuel_in_tank / fuel_capacity) * 100) if fuel_capacity > 0 else 0
                    self.fuel_progress_bar.setValue(percentage)
        except RuntimeError:
            # Widget was deleted, ignore
            pass

    def _update_stat(self, widget: QFrame, value: str, color: str):
        """Update a stat widget's value and color."""
        try:
            if hasattr(widget, 'value_label') and widget.value_label is not None:
                widget.value_label.setText(value)
                widget.value_label.setStyleSheet(f"color: {color}; border: none;")
        except RuntimeError:
            # Widget was deleted, ignore
            pass

    def _get_surplus_color(self, surplus: float) -> str:
        """Get color based on surplus laps."""
        if surplus < 0:
            return self.COLOR_DANGER
        elif surplus < self.MIN_FUEL:
            return self.COLOR_WARNING
        return self.COLOR_PRIMARY

    def _show_telemetry_disabled(self):
        """Show message when telemetry is disabled."""
        # Update all displays to show disabled state
        disabled_text = "---"
        disabled_color = self.COLOR_TEXT_DIM

        self._update_stat(self.fuel_in_tank_widget, disabled_text, disabled_color)
        self._update_stat(self.curr_rate_widget, disabled_text, disabled_color)
        self._update_stat(self.last_lap_widget, disabled_text, disabled_color)
        self._update_stat(self.target_avg_widget, disabled_text, disabled_color)
        self._update_stat(self.target_next_widget, disabled_text, disabled_color)
        self._update_stat(self.surplus_laps_widget, disabled_text, disabled_color)
