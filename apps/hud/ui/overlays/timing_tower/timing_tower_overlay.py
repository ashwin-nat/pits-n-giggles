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
from typing import Any, Dict, Optional, List, Tuple

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QFont
from PySide6.QtWidgets import (QHeaderView, QLabel, QTableWidget, QFrame,
                               QTableWidgetItem, QVBoxLayout, QWidget)

from apps.hud.ui.infra.config import OverlaysConfig
from apps.hud.ui.overlays.base import BaseOverlay
from lib.f1_types import F1Utils

from .border_delegate import BorderDelegate
from .drs_ers_delegate import DrsErsDelegate

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class TimingTowerOverlay(BaseOverlay):

    OVERLAY_ID: str = "timing_tower"

    def __init__(self, config: OverlaysConfig, logger: logging.Logger, locked: bool, opacity: int):

        # Overlay specific fields
        self.num_adjacent_cars = 2
        # total rows = (num_adjacent_cars * 2) + 1
        self.total_rows = (self.num_adjacent_cars * 2) + 1

        # UI components
        self.header_label: Optional[QLabel] = None
        self.session_info_label: Optional[QLabel] = None
        self.timing_table: Optional[QTableWidget] = None

        self.border_delegate = None
        self.drs_ers_delegate = None

        super().__init__(self.OVERLAY_ID, config, logger, locked, opacity)
        self._init_cmd_handlers()
        self._init_icons()

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

    def build_ui(self):
        """Build the timing tower UI"""
        main_layout = QVBoxLayout(self)
        self._configure_main_layout(main_layout)

        content_width = self._calculate_content_width()

        header_widget = self._create_header_section(content_width)
        main_layout.addWidget(header_widget)

        self.timing_table = self._create_timing_table(content_width)
        main_layout.addWidget(self.timing_table)

        self._apply_overall_style()
        self.clear()

    def _configure_main_layout(self, layout: QVBoxLayout) -> None:
        """Configure main layout spacing, margins, and alignment."""
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def _calculate_content_width(self) -> int:
        """Return total content width based on column sizes."""
        return 40 + 30 + 160 + 90 + 75 + 75

    def _create_header_section(self, content_width: int) -> QWidget:
        """Create the header section with title and session info."""
        header_widget = QWidget()
        header_widget.setFixedWidth(content_width)

        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 5, 0, 5)
        header_layout.setSpacing(3)

        self.header_label = QLabel("TIMING TOWER")
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.header_label.setStyleSheet("""
            QLabel {
                background-color: rgba(200, 0, 0, 220);
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 6px;
                border-radius: 4px;
            }
        """)

        self.session_info_label = QLabel("-- / --")
        self.session_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.session_info_label.setStyleSheet("""
            QLabel {
                background-color: rgba(40, 40, 40, 200);
                color: #00ff00;
                font-size: 13px;
                font-weight: bold;
                font-family: 'Courier New', monospace;
                padding: 5px;
                border-radius: 3px;
            }
        """)

        header_layout.addWidget(self.header_label)
        header_layout.addWidget(self.session_info_label)

        header_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(15, 15, 15, 200);
                border-radius: 5px;
            }
        """)

        return header_widget

    def _create_timing_table(self, content_width: int) -> QTableWidget:
        """Create and configure the timing table."""
        table = QTableWidget(self.total_rows, 6)
        table.setHorizontalHeaderLabels(["Pos", "Team", "Driver", "Delta", "Tyre", "ERS"])

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
        for col in range(5):  # Columns 0-4, excluding ERS column
            table.setItemDelegateForColumn(col, self.border_delegate)

    def _set_table_dimensions(self, table: QTableWidget, content_width: int) -> None:
        """Set column widths, row heights, and overall table size."""
        column_widths = [40, 30, 160, 90, 75, 75]
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

    def _update_row(self, row_idx: int, position: int, team: str, name: str, delta: Optional[float],
                   tyre_compound: str, tyre_age: int, ers_mode: str, ers: float, is_ref: bool, drs: bool):
        """Update a specific row in the timing table"""

        # Position
        pos_item = self._create_table_item(str(position), Qt.AlignmentFlag.AlignCenter,
                                          QColor("#ddd"), bold=True)
        self.timing_table.setItem(row_idx, 0, pos_item)

        # Team logo
        team_icon = self.team_logo_mappings.get(team)
        if team_icon and not team_icon.isNull():
            team_item = QTableWidgetItem(team_icon, "")
        elif self.default_team_logo and not self.default_team_logo.isNull():
            team_item = QTableWidgetItem(self.default_team_logo, "")
        else:
            team_display = "??"
            team_item = self._create_table_item(team_display, Qt.AlignmentFlag.AlignCenter, bold=True)

        team_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timing_table.setItem(row_idx, 1, team_item)

        # Driver name
        name_item = self._create_table_item(name, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                                           QColor("#ffffff"), bold=True)
        self.timing_table.setItem(row_idx, 2, name_item)

        # Delta
        if is_ref or delta == 0 or delta is None:
            delta_text = "---"
        else:
            delta_text = f"{F1Utils.formatFloat(delta/1000, precision=3, signed=True)}"

        delta_item = self._create_table_item(delta_text, Qt.AlignmentFlag.AlignCenter,
                                            QColor("#00ff99"), font_family="Courier New")
        self.timing_table.setItem(row_idx, 3, delta_item)

        # Tyre compound
        tyre_icon = self.tyre_icon_mappings.get(tyre_compound)
        tyre_text = f"{tyre_age}L"
        if tyre_icon and not tyre_icon.isNull():
            # Icon found -> show icon + text (e.g., "5L")
            tyre_item = QTableWidgetItem(tyre_icon, tyre_text)
            font = tyre_item.font()
            font.setPointSize(11)
            font.setBold(False)
            tyre_item.setFont(font)
        else:
            # No icon -> show fallback display text (first letter or "--")
            tyre_display = (f"{tyre_compound[:1]}({tyre_text})") if tyre_compound else "--"
            tyre_item = self._create_table_item(tyre_display, Qt.AlignmentFlag.AlignCenter, bold=True)

        tyre_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timing_table.setItem(row_idx, 4, tyre_item)

        # ERS with mode color bar
        ers_text = f"{F1Utils.formatFloat(ers, precision=0, signed=False)}%"
        ers_item = self._create_table_item(ers_text, Qt.AlignmentFlag.AlignCenter)

        # Store ERS mode color in item data for the delegate to use
        ers_item.setData(Qt.ItemDataRole.UserRole, {
            "ers-mode": ers_mode,
            "drs" : drs,
        })
        self.timing_table.setItem(row_idx, 5, ers_item)

        # Update border delegates to highlight reference row
        if is_ref:
            if self.border_delegate:
                self.border_delegate.set_reference_row(row_idx)
            if self.drs_ers_delegate:
                self.drs_ers_delegate.set_reference_row(row_idx)
            # Force repaint of all cells in this row
            for col in range(6):
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

        # Clear reference row border if this was the reference
        if self.border_delegate and self.border_delegate.reference_row == row_idx:
            self.border_delegate.set_reference_row(-1)
        if self.drs_ers_delegate and self.drs_ers_delegate.reference_row == row_idx:
            self.drs_ers_delegate.set_reference_row(-1)

    def _init_cmd_handlers(self):

        @self.on_command("race_table_update")
        def handle_race_update(data: Dict[str, Any]) -> None:

            session_type = data["event-type"]
            relevant_rows, ref_index = self._get_relevant_race_table_rows(data, self.num_adjacent_cars)
            if self._is_race_type_session(session_type):
                self._insert_relative_deltas_race(relevant_rows, ref_index)
            elif not self._is_tt_session(session_type):
                self._insert_relative_deltas_fp_quali(relevant_rows, ref_index)
            session_type: str = data.get("event-type", "N/A")

            # Update header with session type
            self.header_label.setText(f"{session_type.upper()}")

            # Update session info (lap or time)
            if session_type == 'None':
                self.header_label.setText("TIMING TOWER")
                self.session_info_label.setText("----")
            elif self._should_show_lap_number(session_type):
                current_lap = data.get("current-lap", 0)
                total_laps = data.get("total-laps", 0)
                self.session_info_label.setText(f"LAP {current_lap} / {total_laps}")
            else:
                time_remaining_sec = data.get("session-time-left", 0)
                minutes = int(time_remaining_sec // 60)
                seconds = int(time_remaining_sec % 60)
                self.session_info_label.setText(f"TIME: {minutes:02d}:{seconds:02d}")

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

                        position = driver_info.get("position", 0)
                        name = driver_info.get("name", "UNKNOWN")
                        team = driver_info.get("team", "UNKNOWN")
                        driver_idx = driver_info.get("index", -1)

                        delta = delta_info.get("relative-delta", 0)

                        tyre_compound = tyre_info.get("visual-tyre-compound", "UNKNOWN")
                        tyre_age = tyre_info.get("tyre-age", 0)

                        ers_mode = ers_info.get("ers-mode", "None")
                        ers_perc = ers_info.get("ers-percent-float", 0.0)

                        drs = driver_info.get("drs", False)

                        self._update_row(idx, position, team, name, delta, tyre_compound, tyre_age, ers_mode, ers_perc,
                                         (driver_idx == ref_index), drs)

                # Hide remaining empty rows
                for i in range(num_rows_with_data, self.total_rows):
                    self.timing_table.setRowHidden(i, True)

    def clear(self):
        """Clear all timing data"""
        self.header_label.setText("TIMING TOWER")
        self.session_info_label.setText("-- / --")

        # Hide all rows when clearing
        for i in range(self.total_rows):
            self.timing_table.setRowHidden(i, True)

    def _get_relevant_race_table_rows(self,
                                      data: Dict[str, Any],
                                      num_adjacent_cars: int) -> Tuple[List[Dict[str, Any]], Optional[int]]:
        table_entries = data.get("table-entries", [])

        if len(table_entries) == 0:
            # Normal before session start, when no data is available
            return [], None

        ref_index = self._get_ref_row_index(data)

        if ref_index is None:
            self.logger.warning('<<TIMING_TOWER>> Reference index is None!')
            return [], None

        ref_position = table_entries[ref_index]["driver-info"]["position"]
        total_cars = len(table_entries)
        lower_bound, upper_bound = self._get_adjacent_positions(ref_position, total_cars, num_adjacent_cars)

        if lower_bound is None:
            self.logger.warning('<<TIMING_TOWER>> Lower bound is None!')
            return [], None

        # Sort the list by position before computing relevant positions and update rejoin positions
        sorted_table_entries = sorted(table_entries, key=lambda x: x.get("driver-info", {}).get("position", 999))

        lower_index = lower_bound - 1
        result = sorted_table_entries[lower_index:upper_bound] # since upper bound is exclusive

        if total_cars >= 5:
            assert len(result) == 5
        else:
            assert len(result) == total_cars

        return result, ref_index

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

    def _is_tt_session(self, session_type: str) -> bool:
        return session_type == "Time Trial"

    def _is_race_type_session(self, session_type: str) -> bool:
        return "Race" in session_type

    def _should_show_lap_number(self, session_type: str) -> bool:
        unsupported_session_types = ['Qualifying', 'Practice', 'Shootout']
        return not any(sub in session_type for sub in unsupported_session_types)

    def _insert_relative_deltas_race(self, relevant_rows, ref_index) -> None:
        if ref_index is None:
            return

        # Map driver index → position in relevant_rows
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
            self.logger.warning('<<TIMING_TOWER>> Reference row is None!')
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
