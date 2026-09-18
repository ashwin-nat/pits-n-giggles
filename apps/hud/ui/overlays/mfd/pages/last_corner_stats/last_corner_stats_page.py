# MIT License
#
# Copyright (c) [2026] [Ashwin Natarajan]
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
from typing import Any, Dict, Tuple, final

from apps.hud.ui.overlays.mfd.pages.base_page import MfdPageBase
from lib.config import OverlayId, OverlaysSpeedUnit, PngSettings
from lib.logger import PngLogger

_KMPH_TO_MPH = 0.621371

# -------------------------------------- CLASSES -----------------------------------------------------------------------


class LastCornerStatsPage(MfdPageBase):
    """Last Corner Stats standalone overlay (not part of the MFD carousel).

    Shows the minimum speed through the most recently completed corner (or
    complex corner). Keeps showing that data across a new corner starting to
    accumulate — LastCornerTracker only clears last_pub_data on reset(), not
    on corner entry — so the strip never blanks out mid-corner.
    """
    OVERLAY_ID = OverlayId.LAST_CORNER_STATS
    KEY = "last_corner_stats"
    PAGE_QML_FILE: Path = Path(__file__).parent / "last_corner_stats_page.qml"

    def __init__(self, logger: PngLogger, speed_unit: OverlaysSpeedUnit = OverlaysSpeedUnit.KMPH):
        # Set before super().__init__ - it calls setup_page(), which doesn't
        # need this directly, but _format_min_speed (called from event
        # handlers registered there) does.
        self._speed_unit = speed_unit
        super().__init__(logger)

    @classmethod
    def from_settings(cls, settings: PngSettings, logger: PngLogger) -> "LastCornerStatsPage":
        return cls(logger, speed_unit=settings.HUD.overlays_speed_unit)

    @classmethod
    def standalone_show_title(cls, settings: PngSettings) -> bool:
        # No title bar for this overlay — it's a compact strip meant to sit
        # unobtrusively without chrome.
        return False

    @final
    def setup_page(self):
        @self.on_event("stream_overlay_update")
        def _handle_stream_overlay_update(data: Dict[str, Any]) -> None:
            last_corner_stats = data.get("last-corner-stats") or {}
            # Independent of last_pub_data - a corner can be mid-accumulation
            # while the strip still shows the previous corner's stats.
            self.set_qml_property("isAccumulating", bool(last_corner_stats.get("is_accumulating")))

            last_pub_data = last_corner_stats.get("last_pub_data")
            if not last_pub_data:
                self._show_no_data()
                return

            self._show_data(last_pub_data)

    # -- QML updates -------------------------------------------------------

    def _show_no_data(self) -> None:
        self.set_qml_property("hasData", False)

    def _show_data(self, stats: Dict[str, Any]) -> None:
        segment = stats.get("segment", {})
        corner_label, corner_name = self._format_segment(segment)
        min_speed_kmph = stats.get("min_speed_kmph")

        self.set_qml_property("hasData", True)
        self.set_qml_property("hasName", bool(corner_name))
        self.set_qml_property("cornerLabel", corner_label)
        self.set_qml_property("cornerName", corner_name.upper())
        self.set_qml_property("minSpeedText", self._format_min_speed(min_speed_kmph, self._speed_unit))

    # -- Formatting helpers --------------------------------------------------

    @staticmethod
    def _format_segment(segment: Dict[str, Any]) -> Tuple[str, str]:
        """Return (corner label, corner name), e.g. ("T10-11", "Ascari")."""
        name = segment.get("name") or ""

        if segment.get("type") == "complex_corner":
            numbers = segment.get("corner_numbers") or []
            label = f"T{numbers[0]}-{numbers[-1]}" if len(numbers) >= 2 else ""
        else:
            corner_number = segment.get("corner_number")
            label = f"T{corner_number}" if corner_number is not None else ""

        return label, name

    @staticmethod
    def _format_min_speed(min_speed_kmph: Any, speed_unit: OverlaysSpeedUnit) -> str:
        if min_speed_kmph is None:
            return "---"
        if speed_unit == OverlaysSpeedUnit.MPH:
            return f"{round(min_speed_kmph * _KMPH_TO_MPH)} mph"
        return f"{min_speed_kmph} km/h"
