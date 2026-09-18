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
from lib.config import OverlayId, PngSettings

# -------------------------------------- CLASSES -----------------------------------------------------------------------


class LastCornerStatsPage(MfdPageBase):
    """Last Corner Stats standalone overlay (not part of the MFD carousel).

    Shows the minimum speed through the most recently completed corner (or
    complex corner). Stays on-screen unchanged while the car is on a straight;
    clears the moment a new corner starts, since no complete stats exist for
    it yet.
    """
    OVERLAY_ID = OverlayId.LAST_CORNER_STATS
    KEY = "last_corner_stats"
    PAGE_QML_FILE: Path = Path(__file__).parent / "last_corner_stats_page.qml"

    @classmethod
    def standalone_show_title(cls, settings: PngSettings) -> bool:
        # No title bar for this overlay — it's a compact strip meant to sit
        # unobtrusively without chrome.
        return False

    @final
    def setup_page(self):
        @self.on_event("stream_overlay_update")
        def _handle_stream_overlay_update(data: Dict[str, Any]) -> None:
            last_corner_stats = data.get("last-corner-stats")
            if not last_corner_stats:
                self._show_no_data()
                return

            self._show_data(last_corner_stats)

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
        self.set_qml_property("minSpeedText", self._format_min_speed(min_speed_kmph))

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
    def _format_min_speed(min_speed_kmph: Any) -> str:
        return f"{min_speed_kmph} km/h" if min_speed_kmph is not None else "---"
