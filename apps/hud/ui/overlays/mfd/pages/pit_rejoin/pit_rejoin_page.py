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
                               QTableWidgetItem, QVBoxLayout, QWidget)

from apps.hud.ui.overlays.mfd.pages.base_page import BasePage
from apps.hud.ui.overlays.timing_tower.border_delegate import BorderDelegate
from apps.hud.ui.overlays.timing_tower.drs_ers_delegate import DrsErsDelegate
from lib.f1_types import F1Utils

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class PitRejoinPredictionPage(BasePage):
    """Pit rejoin position prediction page."""

    def __init__(self, parent: QWidget, logger: logging.Logger):

        # Overlay specific fields
        self.num_adjacent_cars = 2
        # total rows = (num_adjacent_cars * 2) + 1
        self.total_rows = (self.num_adjacent_cars * 2) + 1

        # UI components
        self.timing_table: Optional[QTableWidget] = None
        self.border_delegate = None
        self.drs_ers_delegate = None

        super().__init__(parent, logger, "mfd.pit_rejoin", title="PIT REJOIN PREDICTION")
        self._init_icons()
        self._build_ui()

    def _init_icons(self):

        icon_base_tyres = Path("assets") / "tyre-icons"
        self.tyre_icon_mappings = {
            "Soft": self.load_icon(str(icon_base_tyres / "soft_tyre.svg")),
            "Super Soft": self.load_icon(str(icon_base_tyres / "super_soft_tyre.svg")),
            "Medium": self.load_icon(str(icon_base_tyres / "medium_tyre.svg")),
            "Hard": self.load_icon(str(icon_base_tyres / "hard_tyre.svg")),
            "Inters": self.load_icon(str(icon_base_tyres / "intermediate_tyre.svg")),
            "Wet": self.load_icon(str(icon_base_tyres / "wet_tyre.svg")),
        }
        for name, icon in self.tyre_icon_mappings.items():
            if icon.isNull():
                self.logger.warning(f"{self.overlay_id} | Failed to load tyre icon: {name}")
            else:
                self.logger.debug(f"{self.overlay_id} | Loaded tyre icon successfully: {name}")

        icon_base_teams = Path("assets") / "team-logos"
        self.team_logo_mappings = {
            "Alpine": self.load_icon(str(icon_base_teams / "alpine.svg")),
            "Aston Martin": self.load_icon(str(icon_base_teams / "aston_martin.svg")),
            "Ferrari": self.load_icon(str(icon_base_teams / "ferrari.svg")),
            "Haas": self.load_icon(str(icon_base_teams / "haas.svg")),

            "McLaren": self.load_icon(str(icon_base_teams / "mclaren.svg")),
            "Mclaren": self.load_icon(str(icon_base_teams / "mclaren.svg")),

            "Mercedes": self.load_icon(str(icon_base_teams / "mercedes.svg")),

            "RB": self.load_icon(str(icon_base_teams / "rb.svg")),
            "VCARB": self.load_icon(str(icon_base_teams / "rb.svg")),
            "Alpha Tauri": self.load_icon(str(icon_base_teams / "rb.svg")),

            "Red Bull": self.load_icon(str(icon_base_teams / "red_bull.svg")),
            "Red Bull Racing": self.load_icon(str(icon_base_teams / "red_bull.svg")),

            "Sauber": self.load_icon(str(icon_base_teams / "sauber.svg")),
            "Alfa Romeo": self.load_icon(str(icon_base_teams / "sauber.svg")),

            "Williams": self.load_icon(str(icon_base_teams / "williams.svg"))
        }
        self.default_team_logo = self.load_icon(str(icon_base_teams / "default.svg"))

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
        """Build the timing tower UI"""
        self._configure_main_layout(self.page_layout)

        content_width = self._calculate_content_width()

        self.timing_table = self._create_timing_table(content_width)
        self.page_layout.addWidget(self.timing_table)

        self._apply_overall_style()
        self._clear()

    def _configure_main_layout(self, layout: QVBoxLayout) -> None:
        """Configure main layout spacing, margins, and alignment."""
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def _calculate_content_width(self) -> int:
        """Return total content width based on column sizes."""
        return 40 + 30 + 160 + 90 + 75 + 75 + 50

    def _create_timing_table(self, content_width: int) -> QTableWidget:
        """Create and configure the timing table."""
        table = QTableWidget(self.total_rows, 7)
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
        self.drs_ers_delegate = DrsErsDelegate(table)
        table.setItemDelegateForColumn(5, self.drs_ers_delegate)

        # Create border delegate for all other columns to handle reference row highlighting
        self.border_delegate = BorderDelegate(table)
        for col in range(6):  # Columns 0-4, excluding ERS column, and including the new penalty column
            if col != 5: # Exclude ERS column
                table.setItemDelegateForColumn(col, self.border_delegate)

    def _set_table_dimensions(self, table: QTableWidget, content_width: int) -> None:
        """Set column widths, row heights, and overall table size."""
        column_widths = [40, 30, 160, 90, 75, 75, 50]
        for i, width in enumerate(column_widths):
            table.setColumnWidth(i, width)

        for i in range(self.total_rows):
            table.setRowHeight(i, 32)

        table_height = 32 * self.total_rows + 4
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

    def _apply_overall_style(self) -> None:
        """Apply background and border styling to the main widget."""
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(10, 10, 10, 220);
                border-radius: 8px;
            }
        """)

    def _create_table_item(self, text: str, alignment: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignCenter,
                          color: Optional[QColor] = None, font_family: str = None,
                          bold: bool = False) -> QTableWidgetItem:
        """Helper to create styled table items"""
        item = QTableWidgetItem(text)
        item.setTextAlignment(alignment)

        if color:
            item.setForeground(QBrush(color))

        if font_family or bold:
            font = QFont()
            if font_family:
                font.setFamily(font_family)
            if bold:
                font.setBold(True)
            font.setPointSize(11)
            item.setFont(font)

        return item

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
        ers: float,
        is_ref: bool,
        drs: bool,
        pens_sec: int
    ):
        """Update a specific row in the timing table."""

        self._update_position_cell(row_idx, position)
        self._update_team_cell(row_idx, team)
        self._update_name_cell(row_idx, name)
        self._update_delta_cell(row_idx, delta, is_ref)
        self._update_tyre_cell(row_idx, tyre_compound, max_tyre_wear_str)
        self._update_ers_cell(row_idx, ers, ers_mode, drs)
        self._update_pens_cell(row_idx, pens_sec) # This line already exists
        self._update_reference_highlight(row_idx, is_ref)

    # -------------------------
    # Per-column update helpers
    # -------------------------

    def _update_position_cell(self, row_idx: int, position: int) -> None:
        """Update position cell (column 0)."""
        pos_item = self._create_table_item(
            str(position), Qt.AlignmentFlag.AlignCenter, QColor("#ddd"), bold=True
        )
        self.timing_table.setItem(row_idx, 0, pos_item)

    def _update_team_cell(self, row_idx: int, team: str) -> None:
        """Update team cell (column 1) with team icon."""
        team_icon = self.team_logo_mappings.get(team)
        if team_icon and not team_icon.isNull():
            team_item = QTableWidgetItem(team_icon, "")
        elif self.default_team_logo and not self.default_team_logo.isNull():
            team_item = QTableWidgetItem(self.default_team_logo, "")
        else:
            team_item = self._create_table_item("??", Qt.AlignmentFlag.AlignCenter, bold=True)

        team_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timing_table.setItem(row_idx, 1, team_item)

    def _update_name_cell(self, row_idx: int, name: str) -> None:
        """Update driver name cell (column 2)."""
        name_item = self._create_table_item(
            name,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            QColor("#ffffff"),
            bold=True,
        )
        self.timing_table.setItem(row_idx, 2, name_item)

    def _update_delta_cell(self, row_idx: int, delta: Optional[float], is_ref: bool) -> None:
        """Update delta cell (column 3)."""
        if is_ref or delta == 0 or delta is None:
            delta_text = "---"
        else:
            delta_text = f"{F1Utils.formatFloat(delta / 1000, precision=3, signed=True)}"

        delta_item = self._create_table_item(
            delta_text, Qt.AlignmentFlag.AlignCenter, QColor("#00ff99"), font_family="Courier New"
        )
        self.timing_table.setItem(row_idx, 3, delta_item)

    def _update_tyre_cell(self, row_idx: int, tyre_compound: str, max_tyre_wear_str: str) -> None:
        """Update tyre cell (column 4) with icon + wear percentage."""
        tyre_icon = self.tyre_icon_mappings.get(tyre_compound)
        if tyre_icon and not tyre_icon.isNull():
            tyre_item = QTableWidgetItem(tyre_icon, max_tyre_wear_str)
            font = tyre_item.font()
            font.setPointSize(11)
            tyre_item.setFont(font)
        else:
            tyre_display = (
                f"{tyre_compound[:1]}({max_tyre_wear_str})" if tyre_compound else "--"
            )
            tyre_item = self._create_table_item(
                tyre_display, Qt.AlignmentFlag.AlignCenter, bold=True
            )

        tyre_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timing_table.setItem(row_idx, 4, tyre_item)

    def _update_ers_cell(self, row_idx: int, ers: float, ers_mode: str, drs: bool) -> None:
        """Update ERS cell (column 5)."""
        ers_text = f"{F1Utils.formatFloat(ers, precision=0, signed=False)}%"
        ers_item = self._create_table_item(ers_text, Qt.AlignmentFlag.AlignCenter)
        ers_item.setData(
            Qt.ItemDataRole.UserRole,
            {"ers-mode": ers_mode, "drs": drs},
        )
        self.timing_table.setItem(row_idx, 5, ers_item)

    def _update_pens_cell(self, row_idx: int, pens_sec: int) -> None:
        """Update penalties cell (column 6)."""
        pens_str = f"+{pens_sec}s" if pens_sec > 0 else ""
        pens_item = self._create_table_item(pens_str, Qt.AlignmentFlag.AlignCenter, QColor("#ffcc00"), bold=True)
        self.timing_table.setItem(row_idx, 6, pens_item)

    def _update_reference_highlight(self, row_idx: int, is_ref: bool) -> None:
        """Highlight the reference row and trigger repaint."""
        if not is_ref:
            return

        if self.border_delegate:
            self.border_delegate.set_reference_row(row_idx)
        if self.drs_ers_delegate:
            self.drs_ers_delegate.set_reference_row(row_idx)

        # Force repaint
        for col in range(7): # Changed from 6 to 7 to include the new column
            index = self.timing_table.model().index(row_idx, col)
            self.timing_table.update(index)


    def _clear_row(self, row_idx: int):
        """Clear a specific row"""
        self.timing_table.setItem(row_idx, 0, self._create_table_item("--"))
        self.timing_table.setItem(row_idx, 1, self._create_table_item("---"))
        self.timing_table.setItem(row_idx, 2, self._create_table_item("---", Qt.AlignmentFlag.AlignLeft))
        self.timing_table.setItem(row_idx, 3, self._create_table_item("--.-"))
        self.timing_table.setItem(row_idx, 4, self._create_table_item("--"))
        self.timing_table.setItem(row_idx, 5, self._create_table_item("0%"))
        self.timing_table.setItem(row_idx, 6, self._create_table_item(""))

        # Clear reference row border if this was the reference
        if self.border_delegate and self.border_delegate.reference_row == row_idx:
            self.border_delegate.set_reference_row(-1)
        if self.drs_ers_delegate and self.drs_ers_delegate.reference_row == row_idx:
            self.drs_ers_delegate.set_reference_row(-1)


    def update(self, data: Dict[str, Any]) -> None:

        session_type = data["event-type"]
        if not self._is_race_type_session(session_type):
            self._show_error("Only supported in Race/Sprint Sessions")
            return

        table_entries = data["table-entries"]
        if not table_entries:
            self._clear()
            return

        ref_row = self._get_ref_row(data)
        if not ref_row:
            self._show_error("ERROR: Please check the logs")
            return
        ref_index = ref_row["driver-info"]["index"]

        pit_time_loss = data.get("pit-time-loss")
        if not pit_time_loss:
            self._show_error("Pit time loss not configured for this track")
            return

        table_entries.sort(key=lambda x: x["driver-info"]["position"])
        updated_entries = self._add_pit_time_loss(table_entries, pit_time_loss, ref_row)
        relevant_rows = self._get_relevant_race_table_rows(updated_entries, ref_index, self.num_adjacent_cars)
        self._insert_relative_deltas_race(relevant_rows, ref_index)

        # If no data, hide all rows
        if not relevant_rows:
            for i in range(self.total_rows):
                self.timing_table.setRowHidden(i, True)
        else:
            num_rows_with_data = min(len(relevant_rows), self.total_rows)

            # Populate rows with data
            for idx, row_data in enumerate(relevant_rows):
                if idx < self.total_rows:
                    self.timing_table.setRowHidden(idx, False)
                    driver_info: Dict[str, Any] = row_data.get("driver-info", {})
                    delta_info: Dict[str, Any]  = row_data.get("delta-info", {})
                    tyre_info: Dict[str, Any]   = row_data.get("tyre-info", {})
                    ers_info: Dict[str, Any]    = row_data.get("ers-info", {})
                    warns_pens_info: Dict[str, Any] = row_data.get("warns-pens-info", {})

                    position = driver_info.get("position", 0)
                    name = driver_info.get("name", "UNKNOWN")
                    team = driver_info.get("team", "UNKNOWN")
                    driver_idx = driver_info.get("index", -1)

                    delta = delta_info.get("relative-delta", 0)

                    tyre_compound = tyre_info.get("visual-tyre-compound", "UNKNOWN")
                    max_wear = F1Utils.getMaxTyreWear(tyre_info["current-wear"])
                    max_wear_str = f"{F1Utils.formatFloat(max_wear['max-wear'], 0)}%"

                    ers_mode = ers_info.get("ers-mode", "None")
                    ers_perc = ers_info.get("ers-percent-float", 0.0)
                    drs = driver_info.get("drs", False)

                    time_pens_sec = warns_pens_info.get("time-penalties", 0)

                    self._update_row(idx, position, team, name, delta, tyre_compound, max_wear_str, ers_mode, ers_perc,
                                        (driver_idx == ref_index), drs, time_pens_sec)

            # Hide remaining empty rows
            for i in range(num_rows_with_data, self.total_rows):
                self.timing_table.setRowHidden(i, True)

    def _clear(self):
        """Clear all timing data"""
        # Hide all rows when clearing
        for i in range(self.total_rows):
            self.timing_table.setRowHidden(i, True)

    def _get_relevant_race_table_rows(self,
                                         sorted_table_entries: Dict[str, Any],
                                         ref_index: int,
                                         num_adjacent_cars: int
                                         ) -> List[Dict[str, Any]]:

        ref_row = next(
            (row for row in sorted_table_entries if row["driver-info"]["index"] == ref_index),
            None
        )
        if not ref_row:
            self.logger.warning(f'{self.overlay_id} Reference row is None!')
            return []

        ref_position = ref_row["driver-info"]["position"]
        total_cars = len(sorted_table_entries)
        lower_bound, upper_bound = self._get_adjacent_positions(ref_position, total_cars, num_adjacent_cars)

        if lower_bound is None:
            self.logger.warning(f'{self.overlay_id} Lower bound is None!')
            return []

        lower_index = lower_bound - 1
        result = sorted_table_entries[lower_index:upper_bound] # since upper bound is exclusive

        if total_cars >= 5:
            assert len(result) == 5
        else:
            assert len(result) == total_cars

        return result

    def _get_adjacent_positions(self, position, total_cars, num_adjacent_cars):
        if not (1 <= position <= total_cars):
            return None, None

        min_valid_lower_bound = 1
        max_valid_upper_bound = total_cars

        # Calculate a window of num_adjacent_cars on each side of the position (inclusive bounds).
        # If the window exceeds valid bounds, shift it towards the center while capping at boundaries
        # to ensure lower_bound stays >= 1 and upper_bound stays <= total_cars.
        lower_bound = position - num_adjacent_cars
        upper_bound = position + num_adjacent_cars

        # Adjust if window exceeds boundaries
        if lower_bound < min_valid_lower_bound:
            shift = min_valid_lower_bound - lower_bound
            lower_bound = min_valid_lower_bound
            upper_bound = min(upper_bound + shift, max_valid_upper_bound)

        if upper_bound > max_valid_upper_bound:
            shift = upper_bound - max_valid_upper_bound
            upper_bound = max_valid_upper_bound
            lower_bound = max(lower_bound - shift, min_valid_lower_bound)

        return lower_bound, upper_bound

    def _is_race_type_session(self, session_type: str) -> bool:
        return "Race" in session_type

    def _insert_relative_deltas_race(self, relevant_rows, ref_index) -> None:
        if ref_index is None:
            return

        # Map driver index --> position in relevant_rows
        index_to_pos = {
            row["driver-info"]["index"]: i for i, row in enumerate(relevant_rows)
        }

        ref_pos = index_to_pos.get(ref_index)
        if ref_pos is None:
            return

        # For each car, sum the deltas between it and the reference car;
        # cars ahead get negative values, cars behind get positive values.
        for i, row in enumerate(relevant_rows):
            if i == ref_pos:
                row["delta-info"]["relative-delta"] = 0
                continue

            if i < ref_pos:
                # Car(s) ahead of reference
                total_delta = sum(
                    relevant_rows[j + 1]["delta-info"]["delta-to-car-in-front"]
                    for j in range(i, ref_pos)
                )
                row["delta-info"]["relative-delta"] = -total_delta
            else:
                # Car(s) behind reference
                total_delta = sum(
                    relevant_rows[j + 1]["delta-info"]["delta-to-car-in-front"]
                    for j in range(ref_pos, i)
                )
                row["delta-info"]["relative-delta"] = total_delta

    def _insert_relative_deltas_fp_quali(self, relevant_rows, ref_index) -> None:
        if ref_index is None:
            return

        ref_row = next(
            (
                row
                for row in relevant_rows
                if row["driver-info"]["index"] == ref_index
            ),
            None
        )
        if not ref_row:
            self.logger.warning(f'{self.overlay_id} Reference row is None!')
            return
        ref_best_lap_ms = ref_row["lap-info"]["best-lap"]["lap-time-ms"]

        # For each car, compute the best lap delta against the ref car
        # ref lap - car lap
        for row in relevant_rows:
            best_lap_ms = row["lap-info"]["best-lap"]["lap-time-ms"]
            if ref_best_lap_ms is None or best_lap_ms is None:
                row["delta-info"]["relative-delta"] = 0
            else:
                row["delta-info"]["relative-delta"] = best_lap_ms - ref_best_lap_ms

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
            # Leader case — no car ahead
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

    def _show_error(self, message: str) -> None:
        """Display a single-row full-width error message in the timing table."""
        if not self.timing_table:
            return

        # Ensure table has at least one visible row
        for i in range(self.total_rows):
            self.timing_table.setRowHidden(i, True)

        # Use row 0 for the message (un-hide it)
        self.timing_table.setRowHidden(0, False)

        # Create the message item and style it
        msg_item = QTableWidgetItem(message)
        msg_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        msg_item.setFont(font)
        msg_item.setForeground(QBrush(QColor("#ffb86b")))  # orange-ish warning color

        # Place the item in column 0 and span across all columns
        self.timing_table.setItem(0, 0, msg_item)
        self.timing_table.setSpan(0, 0, 1, 7) # Hardcoded to 7 columns

        # Clear any leftover items in the spanned columns (avoid duplicate visuals)
        for c in range(1, 7): # Hardcoded to 7 columns
            self.timing_table.setItem(0, c, QTableWidgetItem(""))

        # Ensure remaining rows are hidden
        for i in range(1, self.total_rows):
            self.timing_table.setRowHidden(i, True)
