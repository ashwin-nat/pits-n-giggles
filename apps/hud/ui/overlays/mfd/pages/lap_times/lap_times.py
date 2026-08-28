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
from typing import Any, Dict, List, final

from apps.hud.ui.overlays.mfd.pages.base_page import MfdPageBase
from lib.config import MfdPageId, OverlayId, PngSettings
from lib.table_differ import TableDiffer

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class LapTimesPage(MfdPageBase):
    """Lap Times MFD Page."""
    OVERLAY_ID = OverlayId.LAP_TIMES
    KEY = MfdPageId.LAP_TIMES
    PAGE_QML_FILE: Path = Path(__file__).parent / "lap_times_page.qml"

    NUM_ROWS = 5
    BLANK_TEXT = "---"
    BLANK_COLOUR = "#808080"

    LAP_VALID_MASK = 1
    S1_VALID_MASK = 2
    S2_VALID_MASK = 4
    S3_VALID_MASK = 8

    @classmethod
    def standalone_show_title(cls, settings: PngSettings) -> bool:
        return settings.HUD.lap_times_show_title

    @final
    def on_page_activated(self):
        # The page item is new and its table model is empty, so the next update
        # must repopulate it in full rather than patch rows that aren't there.
        # Seeding the blanks here also fixes the model's role types (all string)
        # before any telemetry arrives.
        self._differ.invalidate()
        self._sync_table([self._blank_row() for _ in range(self.NUM_ROWS)])

    def _sync_table(self, rows: List[Dict[str, Any]]) -> None:
        """Diff rows and, if anything moved, write the one payload QML applies."""
        update = self._differ.update(rows)
        if update:
            self.push_qml_property("tableUpdate", update)

    def _blank_row(self) -> Dict[str, str]:
        """A placeholder row of dashes, for padding and for the pre-telemetry table."""
        return {
            'lapText': self.BLANK_TEXT, 'lapColour': self.BLANK_COLOUR,
            's1Text': self.BLANK_TEXT, 's1Colour': self.BLANK_COLOUR,
            's2Text': self.BLANK_TEXT, 's2Colour': self.BLANK_COLOUR,
            's3Text': self.BLANK_TEXT, 's3Colour': self.BLANK_COLOUR,
            'timeText': self.BLANK_TEXT, 'timeColour': self.BLANK_COLOUR,
        }

    @final
    def setup_page(self):
        self._differ = TableDiffer(self._stats)

        @self.on_event("stream_overlay_update")
        def _handle_stream_overlay_update(data: Dict[str, Any]):
            """Populate the lap table with up to the last 5 laps. Leave remaining rows blank."""
            lap_time_history = data.get("lap-time-history", {})
            if not lap_time_history:
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

                all_rows.append({
                    'lapText': str(lap_num), 'lapColour': lap_num_col,
                    's1Text': s1_disp, 's1Colour': s1_col,
                    's2Text': s2_disp, 's2Colour': s2_col,
                    's3Text': s3_disp, 's3Colour': s3_col,
                    'timeText': lap_disp, 'timeColour': lap_time_col,
                })

            # Pad with empty rows if we have fewer than NUM_ROWS
            while len(all_rows) < self.NUM_ROWS:
                all_rows.insert(0, self._blank_row())

            self._sync_table(all_rows)

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
