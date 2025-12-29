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

from pathlib import Path
import logging
from enum import Enum
from typing import Any, Dict, List

from PySide6.QtCore import QMetaObject, Qt, Q_ARG
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QHeaderView, QSizePolicy, QTableWidget,
                               QTableWidgetItem, QWidget)

from apps.hud.ui.overlays.mfd.pages.base_page import MfdPageBase

# -------------------------------------- CLASSES -----------------------------------------------------------------------


class LapTimesPage(MfdPageBase):
    """Lap Times MFD Page."""
    KEY = "lap_times"
    QML_FILE: Path = Path(__file__).parent / "lap_times_page.qml"

    NUM_ROWS = 5

    LAP_VALID_MASK = 1
    S1_VALID_MASK = 2
    S2_VALID_MASK = 4
    S3_VALID_MASK = 8

    def __init__(self, overlay, logger):
        self._last_processed_data: List[Dict[str, Any]] = []
        super().__init__(overlay, logger)
        self._init_event_handlers()

    def _init_event_handlers(self):
        """Initialize event handlers."""
        @self.on_event("stream_overlay_update")
        def _handle_stream_overlay_update(data: Dict[str, Any]):
            """Populate the lap table with up to the last 5 laps. Leave remaining rows blank."""
            lap_time_history = data.get("lap-time-history", {})
            if not lap_time_history:
                return

            if self._last_processed_data == lap_time_history:
                return

            history_data = lap_time_history.get("lap-time-history-data", [])
            if not history_data:
                return

            # Get the last 5 laps (if fewer exist, it's fine)
            recent_laps = history_data[-self.NUM_ROWS:]
            if not recent_laps:
                return

            pb_lap_num = lap_time_history["fastest-lap-number"]
            pb_s1_lap_num = lap_time_history["fastest-s1-lap-number"]
            pb_s2_lap_num = lap_time_history["fastest-s2-lap-number"]
            pb_s3_lap_num = lap_time_history["fastest-s3-lap-number"]
            glob_best_lap_ms = lap_time_history["global-fastest-lap-ms"]
            glob_best_s1_ms = lap_time_history["global-fastest-s1-ms"]
            glob_best_s2_ms = lap_time_history["global-fastest-s2-ms"]
            glob_best_s3_ms = lap_time_history["global-fastest-s3-ms"]

            page_item = self.overlay.current_page_item
            if not page_item:
                self.logger.error("Page not found")
                return

            # Build the complete rows array
            all_rows = []
            for lap_info in reversed(recent_laps):
                lap_num = lap_info["lap-number"]

                s1_time_ms  = lap_info["sector-1-time-in-ms"]
                s2_time_ms  = lap_info["sector-2-time-in-ms"]
                s3_time_ms  = lap_info["sector-3-time-in-ms"]
                lap_time_ms = lap_info["lap-time-in-ms"]

                s1_str  = lap_info["sector-1-time-str"]
                s2_str  = lap_info["sector-2-time-str"]
                s3_str  = lap_info["sector-3-time-str"]
                lap_str = lap_info["lap-time-str"]

                validFlags = lap_info["lap-valid-bit-flags"]

                s1_valid  = bool(validFlags & self.S1_VALID_MASK)
                s2_valid  = bool(validFlags & self.S2_VALID_MASK)
                s3_valid  = bool(validFlags & self.S3_VALID_MASK)
                lap_valid = bool(validFlags & self.LAP_VALID_MASK)

                # Replace zeros with ---
                s1_disp  = s1_str if s1_str not in ("0.000", "00:00.000") else "---"
                s2_disp  = s2_str if s2_str not in ("0.000", "00:00.000") else "---"
                s3_disp  = s3_str if s3_str not in ("0.000", "00:00.000") else "---"
                lap_disp = lap_str if lap_str not in ("0.000", "00:00.000") else "---"

                lap_num_col  = "#e0e0e0"
                s1_col   = self._get_cell_text_colour(
                                lap_num, s1_time_ms, glob_best_s1_ms, pb_s1_lap_num, s1_valid)
                s2_col   = self._get_cell_text_colour(
                                lap_num, s2_time_ms, glob_best_s2_ms, pb_s2_lap_num, s2_valid)
                s3_col   = self._get_cell_text_colour(
                                lap_num, s3_time_ms, glob_best_s3_ms, pb_s3_lap_num, s3_valid)
                lap_time_col = self._get_cell_text_colour(
                                lap_num, lap_time_ms, glob_best_lap_ms, pb_lap_num, lap_valid)

                row = [
                    {'text': str(lap_num), 'color': lap_num_col},
                    {'text': s1_disp, 'color': s1_col},
                    {'text': s2_disp, 'color': s2_col},
                    {'text': s3_disp, 'color': s3_col},
                    {'text': lap_disp, 'color': lap_time_col}
                ]
                all_rows.append(row)

            # Pad with empty rows if we have fewer than NUM_ROWS
            while len(all_rows) < self.NUM_ROWS:
                all_rows.insert(0, [
                    {'text': '---', 'color': '#808080'},
                    {'text': '---', 'color': '#808080'},
                    {'text': '---', 'color': '#808080'},
                    {'text': '---', 'color': '#808080'},
                    {'text': '---', 'color': '#808080'}
                ])

            self.logger.info(f"Setting rows property with {len(all_rows)} rows")
            if all_rows:
                self.logger.info(f"First row: {all_rows[0]}")

            # Set the entire rows property at once
            page_item.setProperty("rows", all_rows)

            # Force update by incrementing version counter
            current_version = page_item.property("rowsVersion")
            if current_version is None:
                current_version = 0
            page_item.setProperty("rowsVersion", current_version + 1)

            # Verify it was set
            current_rows = page_item.property("rows")
            self.logger.info(f"Property after setting, length: {len(current_rows) if current_rows else 0}")

            # Update the cache
            self._last_processed_data = lap_time_history

    def _get_cell_text_colour(self, lap_num: int, time_ms: int, global_best_time_ms: int,
                            pb_lap_num: int, isValid: bool) -> str:
        """Get the text colour for a cell"""
        if global_best_time_ms and (time_ms == global_best_time_ms):
            return "magenta"
        if pb_lap_num and (lap_num == pb_lap_num):
            return "lime"
        if not isValid:
            return "red"
        return "#e0e0e0"

    def _get_cell_text_colour(self, lap_num: int, time_ms: int, global_best_time_ms: int,
                              pb_lap_num: int, isValid: bool) -> SyntaxError:
        """Get the text colour for a cell"""
        if global_best_time_ms and (time_ms == global_best_time_ms):
            return "magenta"
        if pb_lap_num and (lap_num == pb_lap_num):
            return "lime"
        if not isValid:
            return "red"
        return "#e0e0e0"
