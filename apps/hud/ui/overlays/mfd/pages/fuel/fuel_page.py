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
from PySide6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel,
                               QVBoxLayout, QWidget)

from apps.hud.common import get_ref_row, load_icon
from apps.hud.ui.overlays.mfd.pages.base_page import BasePage

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class FuelInfoPage(BasePage):
    """Modern fuel statistics display for MFD."""

    KEY = "fuel_info"

    FONT_FACE = "Montserrat"
    FONT_SIZE_TITLE = 16
    FONT_SIZE_VALUE = 13
    FONT_SIZE_UNIT = 13
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
        super().__init__(parent, logger, f"{super().KEY}.{self.KEY}", title="FUEL INFO")

        # Load fuel icon
        icon_base = Path("assets")
        icon_path = icon_base / "overlays" / "fuel-pump.svg"
        self.fuel_icon = load_icon(str(icon_path))
        if self.fuel_icon and not self.fuel_icon.isNull():
            self.logger.debug(f"{self.overlay_id} | Fuel icon loaded")
        else:
            self.logger.warning(f"{self.overlay_id} | Failed to load fuel icon")

        # Widget references
        self.curr_rate_widget = None
        self.last_lap_widget = None
        self.target_avg_widget = None
        self.target_next_widget = None
        self.surplus_label = None

        self._build_ui()
        self._init_event_handlers()
        self.logger.debug(f"{self.overlay_id} | Fuel info widget initialized")

    # ---------------------------------------------------------
    # UI BUILD
    # ---------------------------------------------------------

    def _build_ui(self):
        """Build the compact fuel info UI using a 2x2 grid + surplus text."""
        content_widget = QWidget()
        main_layout = QVBoxLayout(content_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        # --- 2×2 GRID ---------------------------------------------------
        grid = QGridLayout()
        grid.setSpacing(10)

        self.curr_rate_widget = self._create_stat_widget("CURRENT RATE", "0.000", "kg/lap")
        self.last_lap_widget = self._create_stat_widget("LAST LAP", "0.000", "kg")

        self.target_avg_widget = self._create_stat_widget("TARGET AVG", "0.000", "kg/lap")
        self.target_next_widget = self._create_stat_widget("TARGET NEXT", "0.000", "kg")

        grid.addWidget(self.curr_rate_widget, 0, 0)
        grid.addWidget(self.last_lap_widget,  0, 1)
        grid.addWidget(self.target_avg_widget, 1, 0)
        grid.addWidget(self.target_next_widget, 1, 1)

        main_layout.addLayout(grid)

        # --- SURPLUS LABEL -----------------------------------------------
        self.surplus_label = QLabel("Surplus: 0 laps")
        s_font = QFont(self.FONT_FACE, 11)
        s_font.setWeight(QFont.Medium)
        self.surplus_label.setFont(s_font)
        self.surplus_label.setStyleSheet(f"color: {self.COLOR_TEXT};")
        main_layout.addWidget(self.surplus_label, alignment=Qt.AlignCenter)

        main_layout.addStretch()
        self.page_layout.addWidget(content_widget)

    def _create_stat_widget(self, label: str, value: str, unit: str) -> QFrame:
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
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(4)

        # Label
        label_widget = QLabel(label)
        label_font = QFont(self.FONT_FACE, self.FONT_SIZE_LABEL)
        label_font.setWeight(QFont.Medium)
        label_widget.setFont(label_font)
        label_widget.setStyleSheet(f"color: {self.COLOR_TEXT_DIM}; border: none;")
        label_widget.setAlignment(Qt.AlignLeft)
        layout.addWidget(label_widget)

        # VALUE ROW
        value_layout = QHBoxLayout()
        value_layout.setSpacing(4)
        value_layout.setContentsMargins(0, 0, 0, 0)

        value_widget = QLabel(value)
        v_font = QFont(self.FONT_FACE, 14)
        v_font.setWeight(QFont.Bold)
        value_widget.setFont(v_font)
        value_widget.setStyleSheet(f"color: {self.COLOR_PRIMARY}; border: none;")
        value_layout.addWidget(value_widget)

        unit_widget = QLabel(unit)
        u_font = QFont(self.FONT_FACE, self.FONT_SIZE_UNIT)
        u_font.setWeight(QFont.Medium)
        unit_widget.setFont(u_font)
        unit_widget.setStyleSheet(f"color: {self.COLOR_TEXT_DIM}; border: none;")
        unit_widget.setAlignment(Qt.AlignBottom)
        value_layout.addWidget(unit_widget)

        value_layout.addStretch()
        layout.addLayout(value_layout)

        frame.value_label = value_widget
        frame.unit_label = unit_widget

        return frame

    # ---------------------------------------------------------
    # UPDATE HANDLING
    # ---------------------------------------------------------

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

            # Extract values (may be None on first lap)
            curr = fuel_info.get("curr-fuel-rate")
            last = fuel_info.get("last-lap-fuel-used")
            surplus = fuel_info.get("surplus-laps-png")
            tgt_avg = fuel_info.get("target-fuel-rate-average")
            tgt_next = fuel_info.get("target-fuel-rate-next-lap")

            # Update compact grid
            self._update_or_dim(self.curr_rate_widget, curr)
            self._update_or_dim(self.last_lap_widget, last)
            self._update_or_dim(self.target_avg_widget, tgt_avg, use_primary=False)
            self._update_or_dim(self.target_next_widget, tgt_next, use_primary=False)

            # Surplus label
            if surplus is not None:
                color = self._get_surplus_color(surplus)
                self.surplus_label.setText(f"Surplus: {surplus:.3f} laps")
                self.surplus_label.setStyleSheet(f"color: {color};")
            else:
                self.surplus_label.setText("Surplus: ---")
                self.surplus_label.setStyleSheet(f"color: {self.COLOR_TEXT_DIM};")

    def _update_or_dim(self, widget: QFrame, value: float, use_primary: bool = True):
        if value is not None:
            widget.value_label.setText(f"{value:.3f}")
            color = self.COLOR_PRIMARY if use_primary else self.COLOR_TEXT
            widget.value_label.setStyleSheet(f"color: {color}; border: none;")
        else:
            widget.value_label.setText("---")
            widget.value_label.setStyleSheet(f"color: {self.COLOR_TEXT_DIM}; border: none;")

    def _get_surplus_color(self, surplus: float) -> str:
        if surplus < 0:
            return self.COLOR_DANGER
        if surplus < self.MIN_FUEL:
            return self.COLOR_WARNING
        return self.COLOR_PRIMARY

    def _show_telemetry_disabled(self):
        disabled = ("---", self.COLOR_TEXT_DIM)

        for widget in (
            self.curr_rate_widget,
            self.last_lap_widget,
            self.target_avg_widget,
            self.target_next_widget,
        ):
            widget.value_label.setText(disabled[0])
            widget.value_label.setStyleSheet(f"color: {disabled[1]}; border: none;")

        self.surplus_label.setText("Surplus: ---")
        self.surplus_label.setStyleSheet(f"color: {self.COLOR_TEXT_DIM};")
