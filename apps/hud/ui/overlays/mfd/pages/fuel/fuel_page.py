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
from typing import Any, Dict

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from apps.hud.common import get_ref_row, load_icon
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
        """Initialise the fuel info page.

        Args:
            parent (QWidget): Parent widget
            logger (logging.Logger): Logger
        """
        super().__init__(parent, logger, "mfd.fuel_info", title="FUEL INFO")

        # Load fuel icon
        icon_base = Path("assets")
        icon_path = icon_base / "overlays" / "fuel-pump.svg"
        self.fuel_icon = load_icon(str(icon_path))
        if self.fuel_icon and not self.fuel_icon.isNull():
            self.logger.debug(f"{self.overlay_id} | Fuel icon loaded")
        else:
            self.logger.warning(f"{self.overlay_id} | Failed to load fuel icon")

        # Initialize widget references to None
        self.curr_rate_widget = None
        self.last_lap_widget = None
        self.target_avg_widget = None
        self.target_next_widget = None
        self.surplus_laps_widget = None

        self._build_ui()
        self._init_event_handlers()
        self.logger.info(f"{self.overlay_id} | Fuel info widget initialized")

    def _build_ui(self):
        """Build the fuel info UI."""
        # Use the existing page_layout from BasePage instead of creating a new one
        # Clear margins set by parent and apply our own to the content
        content_widget = QWidget()
        main_layout = QVBoxLayout(content_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        # Top row: Current consumption and last lap
        top_row = self._create_middle_row()
        main_layout.addLayout(top_row)

        # Separator
        separator1 = self._create_separator()
        main_layout.addWidget(separator1)

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
            "TARGET NEXT LAP", "0.000", "kg", compact=True
        )
        layout.addWidget(self.target_next_widget)

        # Surplus laps
        self.surplus_laps_widget = self._create_stat_widget(
            "SURPLUS", "0", "laps", compact=True
        )
        layout.addWidget(self.surplus_laps_widget)

        return layout

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

    def _init_event_handlers(self) -> None:
        @self.on_event("race_table_update")
        def update(data: Dict[str, Any]) -> None:
            """Update fuel information display."""
            ref_row = get_ref_row(data)
            if not ref_row:
                return

            telemetry_settings = ref_row["driver-info"]["telemetry-setting"]
            if telemetry_settings != "Public":
                self._show_telemetry_disabled()
                return

            fuel_info = ref_row["fuel-info"]
            self.logger.debug(f"{self.overlay_id} | Received fuel info: {fuel_info}")

            # Extract values (may be None on first lap)
            curr_fuel_rate = fuel_info.get("curr-fuel-rate")
            last_lap_used = fuel_info.get("last-lap-fuel-used")
            surplus_laps = fuel_info.get("surplus-laps-png")
            target_rate_avg = fuel_info.get("target-fuel-rate-average")
            target_rate_next_lap = fuel_info.get("target-fuel-rate-next-lap")

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

    def _update_stat(self, widget: QFrame, value: str, color: str):
        """Update a stat widget's value and color."""
        widget.value_label.setText(value)
        widget.value_label.setStyleSheet(f"color: {color}; border: none;")

    def _get_surplus_color(self, surplus: float) -> str:
        """Get color based on surplus laps."""
        if surplus < 0:
            return self.COLOR_DANGER
        if surplus < self.MIN_FUEL:
            return self.COLOR_WARNING
        return self.COLOR_PRIMARY

    def _show_telemetry_disabled(self):
        """Show message when telemetry is disabled."""
        # Update all displays to show disabled state
        disabled_text = "---"
        disabled_color = self.COLOR_TEXT_DIM

        self._update_stat(self.curr_rate_widget, disabled_text, disabled_color)
        self._update_stat(self.last_lap_widget, disabled_text, disabled_color)
        self._update_stat(self.target_avg_widget, disabled_text, disabled_color)
        self._update_stat(self.target_next_widget, disabled_text, disabled_color)
        self._update_stat(self.surplus_laps_widget, disabled_text, disabled_color)
