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
from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QFont
from PySide6.QtWidgets import (QFrame, QHeaderView, QTableWidget,
                               QTableWidgetItem, QVBoxLayout)

from lib.assets_loader import load_icon
from lib.f1_types import F1Utils

from .border_delegate import BorderDelegate
from .drs_ers_delegate import DrsErsDelegate

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class RaceTimingTable:
    """Reusable race timing table component."""

    def __init__(
        self,
        parent_layout: QVBoxLayout,
        logger: logging.Logger,
        overlay_id: str,
        num_rows: int = 5,
        scale_factor: float = 1.0
    ):
        """
        Initialize the race timing table.

        Args:
            parent_layout: The layout to attach this table to
            logger: Logger instance
            overlay_id: Identifier for logging purposes
            num_rows: Number of rows in the table
            scale_factor: Scaling factor for the table size (default 1.5 = 50% larger)
        """
        self.logger = logger
        self.overlay_id = overlay_id
        self.num_rows = num_rows
        self.scale_factor = scale_factor

        # UI components
        self.timing_table: Optional[QTableWidget] = None
        self.border_delegate = None
        self.drs_ers_delegate = None

        # Icon mappings
        self.tyre_icon_mappings = {}
        self.team_logo_mappings = {}
        self.default_team_logo = None

        # Initialize and attach to layout
        self._init_icons()
        self._build_ui()
        self._attach_to_layout(parent_layout)

    def _init_icons(self):
        """Initialize tyre and team icons."""
        icon_base_tyres = Path("assets") / "tyre-icons"
        self.tyre_icon_mappings = {
            "Soft": load_icon(icon_base_tyres / "soft_tyre.svg", self.logger.debug, self.logger.error),
            "Super Soft": load_icon(icon_base_tyres / "super_soft_tyre.svg", self.logger.debug, self.logger.error),
            "Medium": load_icon(icon_base_tyres / "medium_tyre.svg", self.logger.debug, self.logger.error),
            "Hard": load_icon(icon_base_tyres / "hard_tyre.svg", self.logger.debug, self.logger.error),
            "Inters": load_icon(icon_base_tyres / "intermediate_tyre.svg", self.logger.debug, self.logger.error),
            "Wet": load_icon(icon_base_tyres / "wet_tyre.svg", self.logger.debug, self.logger.error),
        }
        for name, icon in self.tyre_icon_mappings.items():
            if icon.isNull():
                self.logger.warning(f"{self.overlay_id} | Failed to load tyre icon: {name}")
            else:
                self.logger.debug(f"{self.overlay_id} | Loaded tyre icon successfully: {name}")

        icon_base_teams = Path("assets") / "team-logos"
        self.team_logo_mappings = {
            "Alpine": load_icon(icon_base_teams / "alpine.svg", self.logger.debug, self.logger.error),
            "Aston Martin": load_icon(icon_base_teams / "aston_martin.svg", self.logger.debug, self.logger.error),
            "Ferrari": load_icon(icon_base_teams / "ferrari.svg", self.logger.debug, self.logger.error),
            "Haas": load_icon(icon_base_teams / "haas.svg", self.logger.debug, self.logger.error),
            "McLaren": load_icon(icon_base_teams / "mclaren.svg", self.logger.debug, self.logger.error),
            "Mclaren": load_icon(icon_base_teams / "mclaren.svg", self.logger.debug, self.logger.error),
            "Mercedes": load_icon(icon_base_teams / "mercedes.svg", self.logger.debug, self.logger.error),
            "RB": load_icon(icon_base_teams / "rb.svg", self.logger.debug, self.logger.error),
            "VCARB": load_icon(icon_base_teams / "rb.svg", self.logger.debug, self.logger.error),
            "Alpha Tauri": load_icon(icon_base_teams / "rb.svg", self.logger.debug, self.logger.error),
            "Red Bull": load_icon(icon_base_teams / "red_bull.svg", self.logger.debug, self.logger.error),
            "Red Bull Racing": load_icon(icon_base_teams / "red_bull.svg", self.logger.debug, self.logger.error),
            "Sauber": load_icon(icon_base_teams / "sauber.svg", self.logger.debug, self.logger.error),
            "Alfa Romeo": load_icon(icon_base_teams / "sauber.svg", self.logger.debug, self.logger.error),
            "Williams": load_icon(icon_base_teams / "williams.svg", self.logger.debug, self.logger.error),
        }
        self.default_team_logo = load_icon(icon_base_teams / "default.svg", self.logger.debug, self.logger.error)

        for name, icon in self.team_logo_mappings.items():
            if icon.isNull():
                self.logger.warning(f"{self.overlay_id} | Failed to load team icon: {name}")
            else:
                self.logger.debug(f"{self.overlay_id} | Loaded team icon successfully: {name}")
        if self.default_team_logo.isNull():
            self.logger.warning(f"{self.overlay_id} | Failed to load default team icon")
        else:
            self.logger.debug(f"{self.overlay_id} | Loaded default team icon successfully")

    def _build_ui(self):
        """Build the timing table UI."""
        content_width = self._calculate_content_width()
        self.timing_table = self._create_timing_table(content_width)
        self.clear()

    def _attach_to_layout(self, layout: QVBoxLayout):
        """Attach the table widget to the provided layout."""
        layout.addWidget(self.timing_table)

    def _calculate_content_width(self) -> int:
        """Return total content width based on column sizes."""
        base_width = 40 + 30 + 160 + 90 + 75 + 75 + 50
        return int(base_width * self.scale_factor)

    def _create_timing_table(self, content_width: int) -> QTableWidget:
        """Create and configure the timing table."""
        table = QTableWidget(self.num_rows, 7)
        table.setHorizontalHeaderLabels(["Pos", "Team", "Driver", "Delta", "Tyre", "ERS", "Pens"])

        self._configure_table_behavior(table)
        self._set_table_dimensions(table, content_width)
        self._apply_table_style(table)

        return table

    def _configure_table_behavior(self, table: QTableWidget) -> None:
        """Disable editing, selection, scrollbars, etc."""
        table.setShowGrid(False)
        table.setAlternatingRowColors(True)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setVisible(False)
        table.setMouseTracking(False)
        table.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        header.setStretchLastSection(False)

        # Create ERS delegate with border support
        self.drs_ers_delegate = DrsErsDelegate(table, self.scale_factor)
        table.setItemDelegateForColumn(5, self.drs_ers_delegate)

        # Create border delegate for all other columns to handle reference row highlighting
        self.border_delegate = BorderDelegate(table)
        for col in range(7):  # All columns except ERS
            if col != 5:  # Exclude ERS column
                table.setItemDelegateForColumn(col, self.border_delegate)

    def _set_table_dimensions(self, table: QTableWidget, content_width: int) -> None:
        """Set column widths, row heights, and overall table size."""
        base_column_widths = [40, 30, 160, 90, 75, 75, 50]
        scaled_column_widths = [int(w * self.scale_factor) for w in base_column_widths]

        for i, width in enumerate(scaled_column_widths):
            table.setColumnWidth(i, width)

        row_height = int(32 * self.scale_factor)
        for i in range(self.num_rows):
            table.setRowHeight(i, row_height)

        table_height = row_height * self.num_rows + 4
        table.setFixedSize(content_width, table_height)
        table.setFrameShape(QFrame.Shape.NoFrame)
        table.setContentsMargins(0, 0, 0, 0)

    def _apply_table_style(self, table: QTableWidget) -> None:
        """Apply modern dark theme styling to the table."""
        table.setStyleSheet("""
            QTableWidget {
                background-color: rgba(15, 15, 15, 220);
                border: none;
                border-radius: 6px;
                gridline-color: transparent;
            }

            QTableWidget::item {
                color: white;
                padding: 4px 8px;
                border: none;
                background-color: rgba(25, 25, 25, 180);
            }

            QTableWidget::item:alternate {
                background-color: rgba(20, 20, 20, 180);
            }

            QTableWidget::item:hover {
                background-color: rgba(45, 45, 45, 200);
            }
        """)

    def _create_table_item(
        self,
        text: str,
        alignment: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignCenter,
        color: Optional[QColor] = None,
        font_family: str = "Formula1 Display",
        font_size_unscaled: int = 12
    ) -> QTableWidgetItem:
        """Helper to create styled table items."""
        item = QTableWidgetItem(text)
        item.setTextAlignment(alignment)

        if color:
            item.setForeground(QBrush(color))

        font = QFont()
        font.setFamily(font_family)
        font.setPointSize(int(font_size_unscaled * self.scale_factor))
        font.setWeight(QFont.Weight.Normal)

        item.setFont(font)
        return item

    def update_data(self, relevant_rows: List[Dict[str, Any]], ref_index: int) -> None:
        """
        Update the table with the given rows.

        Args:
            relevant_rows: List of row data dictionaries
            ref_index: Index of the reference driver
        """
        # Clear any existing spans from error messages
        self._clear_spans()

        # If no data, hide all rows
        if not relevant_rows:
            for i in range(self.num_rows):
                self.timing_table.setRowHidden(i, True)
        else:
            num_rows_with_data = min(len(relevant_rows), self.num_rows)

            # Populate rows with data
            for idx, row_data in enumerate(relevant_rows):
                self.timing_table.setRowHidden(idx, False)
                driver_info: Dict[str, Any] = row_data.get("driver-info", {})
                delta_info: Dict[str, Any] = row_data.get("delta-info", {})
                tyre_info: Dict[str, Any] = row_data.get("tyre-info", {})
                ers_info: Dict[str, Any] = row_data.get("ers-info", {})
                warns_pens_info: Dict[str, Any] = row_data.get("warns-pens-info", {})
                telemetry_public = driver_info.get("telemetry-setting") == "Public"

                position = driver_info.get("position", 0)
                name = driver_info.get("name", "UNKNOWN")
                team = driver_info.get("team", "UNKNOWN")
                driver_idx = driver_info.get("index", -1)
                is_pitting = driver_info.get("is_pitting", False)

                delta = delta_info.get("relative-delta", 0)

                tyre_compound = tyre_info.get("visual-tyre-compound", "UNKNOWN")
                if telemetry_public:
                    # Tyre wear if telemetry is public
                    max_wear = F1Utils.getMaxTyreWear(tyre_info["current-wear"])
                    tyre_wear_age_str = f"{F1Utils.formatFloat(max_wear['max-wear'], 0)}%"
                else:
                    # Tyre age if telemetry is not public
                    tyre_age = tyre_info.get("tyre-age", 0)
                    tyre_wear_age_str = f"{tyre_age}L"

                ers_mode = ers_info.get("ers-mode", "None")
                ers_perc = ers_info.get("ers-percent-float", 0.0)
                if telemetry_public:
                    ers_text = f"{F1Utils.formatFloat(ers_perc, precision=0, signed=False)}%"
                else:
                    ers_text = "N/A"
                drs = driver_info.get("drs", False)

                self._update_row(
                    idx, position, team, name, delta, tyre_compound, tyre_wear_age_str,
                    ers_mode, ers_text, (driver_idx == ref_index), drs, warns_pens_info, is_pitting
                )

            # Hide remaining empty rows
            for i in range(num_rows_with_data, self.num_rows):
                self.timing_table.setRowHidden(i, True)

    def _update_row(
        self,
        row_idx: int,
        position: int,
        team: str,
        name: str,
        delta: Optional[float],
        tyre_compound: str,
        max_tyre_wear_str: str,
        ers_mode: str,
        ers: str,
        is_ref: bool,
        drs: bool,
        warns_pens_info: Dict[str, int],
        is_pitting: bool
    ):
        """Update a specific row in the timing table.

        Args:
            row_idx: Index of the row to update
            position: Position of the driver
            team: Team of the driver
            name: Name of the driver
            delta: Relative delta of the driver
            tyre_compound: Tyre compound of the driver
            max_tyre_wear_str: Maximum tyre wear of the driver
            ers_mode: ERS mode of the driver
            ers: ERS percentage of the driver
            is_ref: Is the driver the reference driver
            drs: Is the driver in DRS
            warns_pens_info: Warns and penalties of the driver
            is_pitting: Is the driver in pit lane
        """
        self._update_position_cell(row_idx, position)
        self._update_team_cell(row_idx, team)
        self._update_name_cell(row_idx, name)
        self._update_delta_cell(row_idx, delta, is_ref, is_pitting)
        self._update_tyre_cell(row_idx, tyre_compound, max_tyre_wear_str)
        self._update_ers_cell(row_idx, ers, ers_mode, drs)
        self._update_pens_cell(row_idx, warns_pens_info)
        self._update_reference_highlight(row_idx, is_ref)

    def _update_position_cell(self, row_idx: int, position: int) -> None:
        """Update position cell (column 0).

        Args:
            row_idx: Index of the row to update
            position: Position of the driver
        """
        if position < 10:
            pos_str = f"{position} "
        else:
            pos_str = f"{position}"
        pos_item = self._create_table_item(
            pos_str, Qt.AlignmentFlag.AlignCenter, QColor("#ddd"),
            font_family="Consolas", font_size_unscaled=11
        )
        self.timing_table.setItem(row_idx, 0, pos_item)

    def _update_team_cell(self, row_idx: int, team: str) -> None:
        """Update team cell (column 1) with team icon.

        Args:
            row_idx: Index of the row to update
            team: Team of the driver
        """
        team_icon = self.team_logo_mappings.get(team)
        if team_icon and not team_icon.isNull():
            team_item = QTableWidgetItem(team_icon, "")
        elif self.default_team_logo and not self.default_team_logo.isNull():
            team_item = QTableWidgetItem(self.default_team_logo, "")
        else:
            team_item = self._create_table_item("??", Qt.AlignmentFlag.AlignCenter)

        team_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timing_table.setItem(row_idx, 1, team_item)

    def _update_name_cell(self, row_idx: int, name: str) -> None:
        """Update driver name cell (column 2).

        Args:
            row_idx: Index of the row to update
            name: Name of the driver
        """
        name_item = self._create_table_item(
            name,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            QColor("#ffffff"),
            font_family="Formula1 Display"
        )
        self.timing_table.setItem(row_idx, 2, name_item)

    def _update_delta_cell(self, row_idx: int, delta: Optional[float], is_ref: bool, is_pitting: bool) -> None:
        """Update delta cell (column 3).

        Args:
            row_idx: Index of the row to update
            delta: Relative delta of the driver
            is_ref: Is the driver the reference driver
            is_pitting: Is the driver in pit lane
        """
        delta_text = (
            "PIT" if is_pitting else
            "---" if is_ref or not delta else
            F1Utils.formatFloat(delta / 1000, precision=3, signed=True)
        )

        delta_item = self._create_table_item(
            delta_text, Qt.AlignmentFlag.AlignCenter, QColor("#00ff99"), font_family="Consolas"
        )
        self.timing_table.setItem(row_idx, 3, delta_item)

    def _update_tyre_cell(self, row_idx: int, tyre_compound: str, max_tyre_wear_str: str) -> None:
        """Update tyre cell (column 4) with icon + wear percentage.

        Args:
            row_idx: Index of the row to update
            tyre_compound: Tyre compound of the driver
            max_tyre_wear_str: Maximum tyre wear of the driver
        """
        tyre_icon = self.tyre_icon_mappings.get(tyre_compound)
        if tyre_icon and not tyre_icon.isNull():
            tyre_item = QTableWidgetItem(tyre_icon, max_tyre_wear_str)
            font = tyre_item.font()
            font.setPointSize(int(11 * self.scale_factor))
            font.setFamily("Consolas")
            tyre_item.setFont(font)
        else:
            tyre_display = (
                f"{tyre_compound[:1]}({max_tyre_wear_str})" if tyre_compound else "--"
            )
            tyre_item = self._create_table_item(
                tyre_display, Qt.AlignmentFlag.AlignCenter
            )

        tyre_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timing_table.setItem(row_idx, 4, tyre_item)

    def _update_ers_cell(self, row_idx: int, ers: str, ers_mode: str, drs: bool) -> None:
        """Update ERS cell (column 5).

        Args:
            row_idx: Index of the row to update
            ers: ERS percentage of the driver
            ers_mode: ERS mode of the driver
            drs: Is the driver in DRS
        """
        ers_item = self._create_table_item(ers, Qt.AlignmentFlag.AlignCenter, font_family="Formula1 Display")
        ers_item.setData(
            Qt.ItemDataRole.UserRole,
            {"ers-mode": ers_mode, "drs": drs},
        )
        self.timing_table.setItem(row_idx, 5, ers_item)

    def _update_pens_cell(self, row_idx: int, warns_pens_info: Dict[str, int]) -> None:
        """Update penalties cell (column 6).

        Args:
            row_idx: Index of the row to update
            warns_pens_info: Warns and penalties of the driver
        """
        pens_sec    = warns_pens_info.get("time-penalties", 0)
        num_dt      = warns_pens_info.get("num-dt", 0)
        pens_str = (
            f"{num_dt}DT" if num_dt else
            f"+{pens_sec}sec" if pens_sec else
            ""
        )

        pens_item = self._create_table_item(
            pens_str, Qt.AlignmentFlag.AlignCenter, QColor("#ffcc00"), font_family="Formula1 Display",
            font_size_unscaled=10
        )
        self.timing_table.setItem(row_idx, 6, pens_item)

    def _update_reference_highlight(self, row_idx: int, is_ref: bool) -> None:
        """Highlight the reference row and trigger repaint.

        Args:
            row_idx: Index of the row to update
            is_ref: True if the row is the reference
        """
        if not is_ref:
            return

        if self.border_delegate:
            self.border_delegate.set_reference_row(row_idx)
        if self.drs_ers_delegate:
            self.drs_ers_delegate.set_reference_row(row_idx)

        # Force repaint
        for col in range(7):
            index = self.timing_table.model().index(row_idx, col)
            self.timing_table.update(index)

    def _clear_spans(self):
        """Clear any cell spans (used by error messages)."""
        # Only clear row 0, column 0 span (where error messages are placed)
        # Check if a span exists before trying to clear it
        if self.timing_table.rowSpan(0, 0) > 1 or self.timing_table.columnSpan(0, 0) > 1:
            self.timing_table.setSpan(0, 0, 1, 1)

    def clear(self):
        """Clear all timing data."""
        self._clear_spans()
        for i in range(self.num_rows):
            self.timing_table.setRowHidden(i, True)

    def show_error(self, message: str) -> None:
        """Display a single-row full-width error message in the timing table."""
        if not self.timing_table:
            return

        # Clear any existing spans first
        self._clear_spans()

        # Ensure table has at least one visible row
        for i in range(self.num_rows):
            self.timing_table.setRowHidden(i, True)

        # Use row 0 for the message (un-hide it)
        self.timing_table.setRowHidden(0, False)

        # Create the message item and style it
        msg_item = QTableWidgetItem(message)
        msg_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(int(12 * self.scale_factor))
        font.setBold(True)
        msg_item.setFont(font)
        msg_item.setForeground(QBrush(QColor("#ffb86b")))  # orange-ish warning color

        # Place the item in column 0 and span across all columns
        self.timing_table.setItem(0, 0, msg_item)
        self.timing_table.setSpan(0, 0, 1, 7)

        # Clear any leftover items in the spanned columns (avoid duplicate visuals)
        for c in range(1, 7):
            self.timing_table.setItem(0, c, QTableWidgetItem(""))

        # Ensure remaining rows are hidden
        for i in range(1, self.num_rows):
            self.timing_table.setRowHidden(i, True)
