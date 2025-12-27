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
from typing import Any, Dict

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QFontMetrics
from PySide6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel,
                               QVBoxLayout, QWidget)

from apps.hud.common import get_ref_row, is_race_type_session
from apps.hud.ui.overlays.mfd.pages.base_page import BasePage, MfdPageBase
from lib.f1_types import F1Utils

# -------------------------------------- CLASSES -----------------------------------------------------------------------

# class FuelInfoPage(BasePage):
#     """Modern fuel statistics display for MFD."""

#     KEY = "fuel_info"

#     FONT_FACE = "Formula1"
#     SURPLUS_FONT_FACE = "B612 Mono"
#     FONT_SIZE_VALUE = 16
#     FONT_SIZE_UNIT = 11
#     FONT_SIZE_LABEL = 9
#     FONT_SIZE_SURPLUS = 14

#     # Spacing and padding
#     CARD_PADDING = 12
#     CARD_SPACING = 12
#     GRID_SPACING = 12
#     BORDER_RADIUS = 8
#     BORDER_WIDTH = 1
#     SURPLUS_MARGIN_TOP = 16
#     LABEL_VALUE_SPACING = 6

#     # Color scheme
#     COLOR_BG = "#1a1a1a"
#     COLOR_PRIMARY = "#00ff88"
#     COLOR_WARNING = "#ffaa00"
#     COLOR_DANGER = "#ff4444"
#     COLOR_TEXT = "#e0e0e0"
#     COLOR_TEXT_DIM = "#808080"
#     COLOR_BORDER = "#333333"

#     # Fuel constants
#     MIN_FUEL = 0.2  # Minimum fuel threshold in laps

#     def __init__(self, parent: QWidget, logger: logging.Logger, scale_factor: float):
#         """Initialise the fuel info page.

#         Args:
#             parent (QWidget): Parent widget
#             logger (logging.Logger): Logger
#             scale_factor (float): Scale factor
#         """
#         self.scale_factor = scale_factor
#         super().__init__(parent, logger, f"{super().KEY}.{self.KEY}", scale_factor, title="FUEL INFO")

#         # Widget references
#         self.curr_rate_widget = None
#         self.last_lap_widget = None
#         self.target_avg_widget = None
#         self.target_next_widget = None
#         self.surplus_label = None

#         self._build_ui()
#         self._init_event_handlers()
#         self.logger.debug(f"{self.OVERLAY_ID} | Fuel info widget initialized")

#     # ---------------------------------------------------------
#     # UI BUILD
#     # ---------------------------------------------------------

#     def _build_ui(self):
#         """Build the compact fuel info UI using a 2x2 grid + surplus text."""
#         content_widget = QWidget()
#         main_layout = QVBoxLayout(content_widget)
#         main_layout.setContentsMargins(0, 0, 0, 0)
#         main_layout.setSpacing(0)

#         # Add vertical centering
#         main_layout.addStretch()

#         # Container for the grid
#         grid_container = QWidget()
#         grid_layout = QVBoxLayout(grid_container)
#         grid_layout.setContentsMargins(self.scaled_card_padding, self.scaled_card_padding,
#                                       self.scaled_card_padding, self.scaled_card_padding)
#         grid_layout.setSpacing(0)

#         # --- 2×2 GRID ---------------------------------------------------
#         grid = QGridLayout()
#         grid.setSpacing(self.scaled_grid_spacing)
#         grid.setContentsMargins(0, 0, 0, 0)

#         self.curr_rate_widget = self._create_stat_widget("CURRENT RATE", "0.000", "kg/lap")
#         self.last_lap_widget = self._create_stat_widget("LAST LAP", "0.000", "kg")
#         self.target_avg_widget = self._create_stat_widget("TARGET AVG", "0.000", "kg/lap")
#         self.target_next_widget = self._create_stat_widget("TARGET NEXT", "0.000", "kg")

#         grid.addWidget(self.curr_rate_widget, 0, 0)
#         grid.addWidget(self.last_lap_widget, 0, 1)
#         grid.addWidget(self.target_avg_widget, 1, 0)
#         grid.addWidget(self.target_next_widget, 1, 1)

#         grid_layout.addLayout(grid)

#         # --- SURPLUS LABEL -----------------------------------------------
#         surplus_container = QWidget()
#         surplus_layout = QVBoxLayout(surplus_container)
#         surplus_layout.setContentsMargins(0, self.scaled_surplus_margin, 0, 0)
#         surplus_layout.setSpacing(0)

#         self.surplus_label = QLabel("Surplus: +0 laps")
#         s_font = QFont(self.SURPLUS_FONT_FACE, self.font_size_surplus)
#         s_font.setWeight(QFont.Weight.Medium)
#         self.surplus_label.setFont(s_font)
#         self.surplus_label.setStyleSheet(f"color: {self.COLOR_TEXT};")
#         self.surplus_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

#         surplus_layout.addWidget(self.surplus_label)
#         grid_layout.addWidget(surplus_container)

#         main_layout.addWidget(grid_container)
#         main_layout.addStretch()

#         self.page_layout.addWidget(content_widget)

#     def _create_stat_widget(self, label: str, value: str, unit: str) -> QFrame:
#         """Create a styled stat display widget with proper scaling."""
#         frame = QFrame()
#         frame.setStyleSheet(f"""
#             QFrame {{
#                 background-color: {self.COLOR_BG};
#                 border: {self.scaled_border_width}px solid {self.COLOR_BORDER};
#                 border-radius: {self.scaled_border_radius}px;
#             }}
#         """)

#         layout = QVBoxLayout(frame)
#         layout.setContentsMargins(self.scaled_card_padding, self.scaled_card_padding,
#                                  self.scaled_card_padding, self.scaled_card_padding)
#         layout.setSpacing(self.scaled_label_value_spacing)

#         # Label
#         label_widget = QLabel(label)
#         label_font = QFont(self.FONT_FACE, self.font_size_label)
#         label_font.setWeight(QFont.Medium)
#         label_widget.setFont(label_font)
#         label_widget.setStyleSheet(f"color: {self.COLOR_TEXT_DIM}; border: none;")
#         label_widget.setAlignment(Qt.AlignLeft)

#         # Calculate minimum height based on font metrics
#         label_metrics = QFontMetrics(label_font)
#         label_widget.setMinimumHeight(int(label_metrics.height() * 1.2))

#         layout.addWidget(label_widget)

#         # VALUE ROW
#         value_layout = QHBoxLayout()
#         value_layout.setSpacing(int(4 * self.scale_factor))
#         value_layout.setContentsMargins(0, 0, 0, 0)

#         value_widget = QLabel(value)
#         v_font = QFont(self.FONT_FACE, self.font_size_value)
#         v_font.setWeight(QFont.Bold)
#         value_widget.setFont(v_font)
#         value_widget.setStyleSheet(f"color: {self.COLOR_PRIMARY}; border: none;")

#         # Calculate minimum height for value
#         value_metrics = QFontMetrics(v_font)
#         value_widget.setMinimumHeight(int(value_metrics.height() * 1.2))

#         value_layout.addWidget(value_widget)

#         unit_widget = QLabel(unit)
#         u_font = QFont(self.FONT_FACE, self.font_size_unit)
#         u_font.setWeight(QFont.Medium)
#         unit_widget.setFont(u_font)
#         unit_widget.setStyleSheet(f"color: {self.COLOR_TEXT_DIM}; border: none;")
#         unit_widget.setAlignment(Qt.AlignBottom | Qt.AlignLeft)

#         # Calculate minimum height for unit
#         unit_metrics = QFontMetrics(u_font)
#         unit_widget.setMinimumHeight(int(unit_metrics.height() * 1.2))

#         value_layout.addWidget(unit_widget)
#         value_layout.addStretch()
#         layout.addLayout(value_layout)
#         layout.addStretch()

#         frame.value_label = value_widget
#         frame.unit_label = unit_widget

#         return frame

#     # ---------------------------------------------------------
#     # UPDATE HANDLING
#     # ---------------------------------------------------------

#     def _init_event_handlers(self) -> None:
#         @self.on_event("race_table_update")
#         def update(data: Dict[str, Any]) -> None:
#             """Update fuel information display."""
#             ref_row = get_ref_row(data)
#             if not ref_row:
#                 return

#             telemetry_settings = ref_row["driver-info"]["telemetry-setting"]
#             if telemetry_settings != "Public":
#                 self._show_telemetry_disabled()
#                 return

#             session_type = data["event-type"]

#             fuel_info = ref_row["fuel-info"]

#             # Extract values (may be None on first lap)
#             last = fuel_info.get("last-lap-fuel-used")
#             if is_race_type_session(session_type):
#                 curr = fuel_info.get("curr-fuel-rate")
#                 surplus = fuel_info.get("surplus-laps-png")
#                 tgt_avg = fuel_info.get("target-fuel-rate-average")
#                 tgt_next = fuel_info.get("target-fuel-rate-next-lap")
#             else:
#                 curr = None
#                 tgt_avg = None
#                 tgt_next = None
#                 surplus = fuel_info.get("surplus-laps-game")

#             # Update compact grid
#             self._update_or_dim(self.curr_rate_widget, curr)
#             self._update_or_dim(self.last_lap_widget, last)
#             self._update_or_dim(self.target_avg_widget, tgt_avg, use_primary=False)
#             self._update_or_dim(self.target_next_widget, tgt_next, use_primary=False)

#             # Surplus label
#             if surplus is not None:
#                 color = self._get_surplus_color(surplus)
#                 self.surplus_label.setText(f"Surplus: {F1Utils.formatFloat(surplus, precision=3, signed=True)} laps")
#                 self.surplus_label.setStyleSheet(f"color: {color};")
#             else:
#                 self.surplus_label.setText("Surplus: ---")
#                 self.surplus_label.setStyleSheet(f"color: {self.COLOR_TEXT_DIM};")

#     def _update_or_dim(self, widget: QFrame, value: float, use_primary: bool = True):
#         if value is not None:
#             widget.value_label.setText(f"{value:.3f}")
#             color = self.COLOR_PRIMARY if use_primary else self.COLOR_TEXT
#             widget.value_label.setStyleSheet(f"color: {color}; border: none;")
#         else:
#             widget.value_label.setText("---")
#             widget.value_label.setStyleSheet(f"color: {self.COLOR_TEXT_DIM}; border: none;")

#     def _get_surplus_color(self, surplus: float) -> str:
#         if surplus < 0:
#             return self.COLOR_DANGER
#         if surplus < self.MIN_FUEL:
#             return self.COLOR_WARNING
#         return self.COLOR_PRIMARY

#     def _show_telemetry_disabled(self):
#         disabled = ("---", self.COLOR_TEXT_DIM)

#         for widget in (
#             self.curr_rate_widget,
#             self.last_lap_widget,
#             self.target_avg_widget,
#             self.target_next_widget,
#         ):
#             widget.value_label.setText(disabled[0])
#             widget.value_label.setStyleSheet(f"color: {disabled[1]}; border: none;")

#         self.surplus_label.setText("Surplus: ---")
#         self.surplus_label.setStyleSheet(f"color: {self.COLOR_TEXT_DIM};")

#     # ---------------------------------------------------------
#     # SCALED PROPERTIES
#     # ---------------------------------------------------------

#     @property
#     def font_size_value(self) -> int:
#         """Get the scaled value font size."""
#         return int(self.FONT_SIZE_VALUE * self.scale_factor)

#     @property
#     def font_size_label(self) -> int:
#         """Get the scaled label font size."""
#         return int(self.FONT_SIZE_LABEL * self.scale_factor)

#     @property
#     def font_size_unit(self) -> int:
#         """Get the scaled unit font size."""
#         return int(self.FONT_SIZE_UNIT * self.scale_factor)

#     @property
#     def font_size_surplus(self) -> int:
#         """Get the scaled surplus font size."""
#         return int(self.FONT_SIZE_SURPLUS * self.scale_factor)

#     @property
#     def scaled_card_padding(self) -> int:
#         """Get the scaled card padding."""
#         return int(self.CARD_PADDING * self.scale_factor)

#     @property
#     def scaled_grid_spacing(self) -> int:
#         """Get the scaled grid spacing."""
#         return int(self.GRID_SPACING * self.scale_factor)

#     @property
#     def scaled_border_radius(self) -> int:
#         """Get the scaled border radius."""
#         return int(self.BORDER_RADIUS * self.scale_factor)

#     @property
#     def scaled_border_width(self) -> int:
#         """Get the scaled border width."""
#         return max(1, int(self.BORDER_WIDTH * self.scale_factor))

#     @property
#     def scaled_surplus_margin(self) -> int:
#         """Get the scaled surplus margin top."""
#         return int(self.SURPLUS_MARGIN_TOP * self.scale_factor)

#     @property
#     def scaled_label_value_spacing(self) -> int:
#         """Get the scaled spacing between label and value."""
#         return int(self.LABEL_VALUE_SPACING * self.scale_factor)

class FuelInfoPage(MfdPageBase):
    KEY = "fuel_info"

    def __init__(self, root, logger):
        super().__init__(root, logger)
        self._init_handlers()

    def _init_handlers(self):
        @self.on_event("race_table_update")
        def _update(data: Dict[str, Any]):
            ref = data.get("ref")
            if not ref:
                return

            surplus = ref["fuel"]["surplus-laps"]
            self._root.setProperty(
                "fuelSurplus",
                f"{surplus:+.2f} laps"
            )
