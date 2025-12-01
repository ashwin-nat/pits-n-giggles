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
from PySide6.QtGui import QFont, QFontMetrics
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from apps.hud.common import (get_ref_row, get_relevant_race_table_rows,
                             insert_relative_deltas_race, is_race_type_session)
from apps.hud.ui.overlays.mfd.pages.base_page import BasePage
from lib.assets_loader import load_icon, load_team_icons_dict
from lib.f1_types import F1Utils

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class PitRejoinPredictionPage(BasePage):
    """Pit rejoin position prediction page."""
    KEY = "pit_rejoin"

    # Font configuration
    FONT_FACE = "Formula1 Display"
    FONT_SIZE = 10
    HEADER_FONT_SIZE = 11

    def __init__(self, parent: QWidget, logger: logging.Logger, scale_factor: float):
        """Initialise the pit rejoin prediction page.

        Args:
            parent (QWidget): Parent widget
            logger (logging.Logger): Logger
            scale_factor (float): Scale factor
        """
        # Overlay specific fields
        super().__init__(parent, logger, f"{super().KEY}.{self.KEY}", scale_factor, title="PIT REJOIN PREDICTION")

        self.num_adjacent_cars = 2
        self.total_rows = (self.num_adjacent_cars * 2) + 1

        self.team_icons = load_team_icons_dict(debug_log_printer=logger.debug, error_log_printer=logger.error)
        icon_base_teams = Path("assets") / "team-logos"
        self.default_team_logo = load_icon(icon_base_teams / "default.svg", self.logger.debug, self.logger.error)

        self._build_ui()
        self._init_event_handlers()

    @property
    def font_size(self) -> int:
        """Get scaled font size."""
        return int(self.FONT_SIZE * self.scale_factor)

    @property
    def header_font_size(self) -> int:
        """Get scaled header font size."""
        return int(self.HEADER_FONT_SIZE * self.scale_factor)

    @property
    def row_height(self) -> int:
        """Get scaled row height based on font metrics."""
        font = QFont(self.FONT_FACE, self.font_size)
        metrics = QFontMetrics(font)
        # Add padding (2x line height for comfortable spacing)
        return metrics.height() * 2

    @property
    def icon_size(self) -> int:
        """Get scaled icon size."""
        return int(25 * self.scale_factor)

    @property
    def spacing(self) -> int:
        """Get scaled spacing."""
        return int(5 * self.scale_factor)

    @property
    def padding(self) -> int:
        """Get scaled padding."""
        return int(5 * self.scale_factor)

    def _build_ui(self):
        """Build the timing tower UI"""
        # Remove center alignment from page layout
        self.page_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Pit time loss label
        self.pit_time_loss_label = QLabel("Pit Time Loss: --", self)
        self.pit_time_loss_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont(self.FONT_FACE, self.header_font_size)
        font.setBold(True)
        self.pit_time_loss_label.setFont(font)
        self.pit_time_loss_label.setStyleSheet(
            "background-color: rgba(0, 0, 0, 0.7); "
            "color: white; "
            f"padding: {self.padding}px; "
            "border: 1px solid #444;"
        )
        self.page_layout.addWidget(self.pit_time_loss_label)

        # Table container
        self.table_widget = QWidget(self)
        self.table_layout = QVBoxLayout(self.table_widget)
        self.table_layout.setContentsMargins(0, 0, 0, 0)
        self.table_layout.setSpacing(0)
        self.page_layout.addWidget(self.table_widget)

        # Store row widgets for updates
        self.table_rows: List[QFrame] = []

        # Initialize with empty rows
        self._show_empty_table()

    def _create_table_row(self, position: int, team: str, name: str, delta: str, is_ref: bool) -> QFrame:
        """Create a single table row.

        Args:
            position (int): Position number
            team (str): Team identifier
            name (str): Driver name
            delta (str): Delta time string
            is_ref (bool): Whether this is the reference driver

        Returns:
            QFrame: The row widget
        """
        row_frame = QFrame(self)
        row_frame.setFixedHeight(self.row_height)

        # Add border styling
        border_width = int(2 * self.scale_factor)
        border_style = f"border: {border_width}px solid white;" if is_ref else "border: none;"
        row_frame.setStyleSheet(
            f"background-color: rgba(0, 0, 0, 0.5); "
            f"border-top: 1px solid #444; "
            f"{border_style}"
        )

        row_layout = QHBoxLayout(row_frame)
        row_layout.setContentsMargins(self.spacing, 0, self.spacing, 0)
        row_layout.setSpacing(self.spacing)

        # Position label (10%)
        pos_label = QLabel(str(position), row_frame)
        pos_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pos_label.setFont(QFont(self.FONT_FACE, self.font_size, QFont.Weight.Bold))
        pos_label.setStyleSheet("color: white; background: transparent; border: none;")
        row_layout.addWidget(pos_label, 10)

        # Team logo (10%)
        team_icon_label = QLabel(row_frame)
        team_icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        team_icon_label.setStyleSheet("background: transparent; border: none;")

        # Load team icon if available
        icon = self.team_icons.get(team, self.default_team_logo)
        pixmap = icon.pixmap(self.icon_size, self.icon_size)
        team_icon_label.setPixmap(pixmap)

        row_layout.addWidget(team_icon_label, 10)

        # Driver name (50%)
        name_label = QLabel(name, row_frame)
        name_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        name_label.setFont(QFont(self.FONT_FACE, self.font_size))
        name_label.setStyleSheet("color: white; background: transparent; border: none;")
        row_layout.addWidget(name_label, 50)

        # Delta (30%)
        delta_label = QLabel(delta, row_frame)
        delta_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        delta_label.setFont(QFont(self.FONT_FACE, self.font_size, QFont.Weight.Bold))

        # Color code delta
        delta_color = "white"
        if delta.startswith("+"):
            delta_color = "#FF4444"
        elif delta.startswith("-"):
            delta_color = "#44FF44"

        delta_label.setStyleSheet(f"color: {delta_color}; background: transparent; border: none;")
        row_layout.addWidget(delta_label, 30)

        return row_frame

    def _create_blank_row(self) -> QFrame:
        """Create an empty table row with no text or icons."""
        row_frame = QFrame(self)
        row_frame.setFixedHeight(self.row_height)

        # Match the visual style of normal rows
        row_frame.setStyleSheet(
            f"background-color: rgba(0, 0, 0, 0.5); "
            "border-top: 1px solid #444;"
        )

        row_layout = QHBoxLayout(row_frame)
        row_layout.setContentsMargins(self.spacing, 0, self.spacing, 0)
        row_layout.setSpacing(self.spacing)

        # Add empty placeholders so layout proportions stay identical
        # Position (10%)
        pos = QLabel("", row_frame)
        pos.setStyleSheet("background: transparent; border: none;")
        row_layout.addWidget(pos, 10)

        # Team icon placeholder (10%)
        icon = QLabel("", row_frame)
        icon.setStyleSheet("background: transparent; border: none;")
        row_layout.addWidget(icon, 10)

        # Driver name (50%)
        name = QLabel("", row_frame)
        name.setStyleSheet("background: transparent; border: none;")
        row_layout.addWidget(name, 50)

        # Delta (30%)
        delta = QLabel("", row_frame)
        delta.setStyleSheet("background: transparent; border: none;")
        row_layout.addWidget(delta, 30)

        return row_frame


    def _clear_table(self):
        """Clear all rows from the table."""
        for row in self.table_rows:
            self.table_layout.removeWidget(row)
            row.deleteLater()
        self.table_rows.clear()

    def _show_empty_table(self):
        """Display empty table with placeholder rows."""
        self._clear_table()
        for _ in range(self.total_rows):
            row_widget = self._create_blank_row()
            self.table_layout.addWidget(row_widget)
            self.table_rows.append(row_widget)

    def _update_table(self, rows_data: List[Dict[str, Any]], ref_index: int):
        """Update the table with new data.

        Args:
            rows_data (List[Dict[str, Any]]): List of row data dictionaries
            ref_index (int): Reference driver index
        """
        self._clear_table()

        for row_data in rows_data:
            driver_info: Dict[str, Any] = row_data.get("driver-info", {})
            delta_info: Dict[str, Any] = row_data.get("delta-info", {})

            position = driver_info.get("position", 0)
            team = driver_info.get("team", "")
            name = driver_info.get("name", "")
            delta_value = delta_info.get("relative-delta", 0.0)
            driver_idx = driver_info.get("index", -1)
            is_ref = (driver_idx == ref_index)

            # Format delta
            if is_ref:
                delta_str = '---'
            else:
                delta_str = F1Utils.formatFloat(delta_value / 1000, precision=3, signed=True)

            row_widget = self._create_table_row(position, team, name, delta_str, is_ref)
            self.table_layout.addWidget(row_widget)
            self.table_rows.append(row_widget)

    def _init_event_handlers(self):
        @self.on_event("race_table_update")
        def _handle_race_table_update(data: Dict[str, Any]) -> None:
            """Update the page with new data.

            Args:
                data (Dict[str, Any]): The incoming data from the server (top level, including all keys)
            """
            session_type = data["event-type"]
            if not is_race_type_session(session_type):
                self._show_empty_table()
                return

            table_entries = data["table-entries"]
            if not table_entries:
                self._show_empty_table()
                return

            ref_row = get_ref_row(data)
            if not ref_row:
                self._show_empty_table()
                return
            ref_index = ref_row["driver-info"]["index"]

            pit_time_loss = data.get("pit-time-loss")
            if not pit_time_loss:
                self._show_empty_table()
                return

            # Update pit time loss header
            pit_time_loss_str = f"Pit Time Loss: {pit_time_loss:.1f}s"
            self.pit_time_loss_label.setText(pit_time_loss_str)

            table_entries.sort(key=lambda x: x["driver-info"]["position"])
            updated_entries = self._add_pit_time_loss(table_entries, pit_time_loss, ref_row)
            relevant_rows = get_relevant_race_table_rows(updated_entries, self.num_adjacent_cars, ref_index)
            insert_relative_deltas_race(relevant_rows, ref_index)

            # Update the table
            self._update_table(relevant_rows, ref_index)

    def _add_pit_time_loss(
        self,
        table_entries: List[Dict[str, Any]],
        pit_time_loss: float,
        ref_row: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Estimate where a driver would rejoin after a pit stop and update their deltas accordingly.
        """

        assert ref_row is not None
        assert pit_time_loss is not None

        # Convert pit loss from seconds --> milliseconds for consistent comparison
        pit_time_loss_ms = pit_time_loss * 1000.0

        # Step 1: Compute projected gap to leader after pit
        ref_delta = ref_row["delta-info"]["delta-to-leader"]
        projected_gap = ref_delta + pit_time_loss_ms

        # Step 2: Find rejoin position (where projected gap would place them)
        rejoin_index = len(table_entries) - 1  # assume they rejoin last
        for i, row in enumerate(table_entries):
            if projected_gap < row["delta-info"]["delta-to-leader"]:
                rejoin_index = i - 1
                break

        rejoin_index = max(rejoin_index, 0)

        # Step 3: Update ref driver info
        ref_row["delta-info"]["delta-to-leader"] = projected_gap

        if rejoin_index >= 0:
            front_driver = table_entries[rejoin_index]
            ref_row["delta-info"]["delta-to-car-in-front"] = (
                projected_gap - front_driver["delta-info"]["delta-to-leader"]
            )
        else:
            # Leader case - no car ahead
            ref_row["delta-info"]["delta-to-car-in-front"] = 0

        # Step 4: Remove driver from current position
        table_entries = [r for r in table_entries if r is not ref_row]

        # Step 5: Insert at new position
        table_entries.insert(rejoin_index + 1, ref_row)

        # Step 6: Reassign positions
        for pos, row in enumerate(table_entries, start=1):
            row["driver-info"]["position"] = pos

        # Step 7: Recompute delta-to-car-in-front for consistency
        for i in range(1, len(table_entries)):
            prev = table_entries[i - 1]["delta-info"]["delta-to-leader"]
            curr = table_entries[i]["delta-info"]["delta-to-leader"]
            table_entries[i]["delta-info"]["delta-to-car-in-front"] = curr - prev

        return table_entries
