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
from typing import Any, Dict, Optional, final

from apps.hud.common import get_ref_row
from apps.hud.ui.infra.hf_types import HudOverlayData
from apps.hud.ui.overlays.base.base_overlay import BaseOverlay
from lib.config import OverlayId, PngSettings
from lib.f1_types import F1Utils
from lib.logger import PngLogger
from lib.track_segment_info import (ComplexCornerSegmentInfo,
                                    CornerSegmentInfo, TrackSegmentsDatabase)

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class CircuitInfoOverlay(BaseOverlay):
    """
    Extremely minimal QML overlay template.

    - Loads QML
    - Shows window
    """

    # Remember to update the spec file with the new QML path
    QML_FILE = Path(__file__).parent / "circuit_info.qml"
    OVERLAY_ID = OverlayId.CIRCUIT_INFO
    ANIMATION_DRIVEN = True

    GREEN_SECTOR_COLOUR = "#28a745"
    YELLOW_SECTOR_COLOUR = "#ffc107"
    RED_SECTOR_COLOUR = "#dc3545"
    PURPLE_SECTOR_COLOUR = "#9b30ff"
    NA_SECTOR_COLOUR = "#888888"

    def __init__(self, settings: PngSettings, logger: PngLogger) -> None:
        self.circuit_info_length = settings.HUD.circuit_info_length
        super().__init__(settings, logger)

        self.tracks_db = TrackSegmentsDatabase(Path(__file__).parents[5] / "assets/track-segments")

        # For high frequency/high refresh rate overlays, subscribe to HF types here and render in render_frame.
        self.subscribe_hf(HudOverlayData)
        self._register_handlers()

    @final
    def post_setup(self):
        """Set initial QML properties when the window is ready."""
        self._set_bar_width_property(self.circuit_info_length)

    def _register_handlers(self):
        @self.on_event("set_circuit_info_length")
        def _handle_set_circuit_info_length(data: dict):
            self.logger.debug('%s | Received "set_circuit_info_length" event. Length: %s', self.OVERLAY_ID, data)
            self.circuit_info_length = data["length"]
            self._set_bar_width_property(self.circuit_info_length)

        @self.on_event("race_table_update")
        def _handle_race_table_update(data: dict):
            session_type = data["event-type"]
            if session_type == "None":
                return

            ref_row = get_ref_row(data)
            if not ref_row:
                return

            lap_info = ref_row["lap-info"]
            curr_lap = lap_info["curr-lap"]

            sectors = curr_lap["sector-status"]
            # Ignore the final sector which will never be "completed" in the current lap
            for i, sector in enumerate(sectors[:-1]):
                sector_num = i + 1
                sector_colour = {
                    F1Utils.SECTOR_STATUS_NA : self.NA_SECTOR_COLOUR,
                    F1Utils.SECTOR_STATUS_YELLOW : self.YELLOW_SECTOR_COLOUR,
                    F1Utils.SECTOR_STATUS_GREEN : self.GREEN_SECTOR_COLOUR,
                    F1Utils.SECTOR_STATUS_INVALID : self.RED_SECTOR_COLOUR,
                    F1Utils.SECTOR_STATUS_PURPLE : self.PURPLE_SECTOR_COLOUR,
                }.get(sector, self.NA_SECTOR_COLOUR)

                self.set_completed_sector_color(sector_num, sector_colour)

    def _set_bar_width_property(self, length: int):
        self.set_qml_property("barWidth", length)

    def set_completed_sector_color(self, sector: int, color: str) -> None:
        """Set the completed-sector fill colour for a single sector (1 or 2)."""
        if sector == 1:
            self.set_qml_property("completedSector1Color", color)
        elif sector == 2:
            self.set_qml_property("completedSector2Color", color)

    def set_completed_sector_colors(self, s1_color: str, s2_color: str) -> None:
        """Set the completed-sector fill colours for both sectors at once."""
        self.set_qml_property("completedSector1Color", s1_color)
        self.set_qml_property("completedSector2Color", s2_color)

    ## For high frequency data, register HF types in ctor and render periodically in render_frame.
    @final
    def render_frame(self):
        """
        This will be called by the base class periodically based on the refresh rate specified in the ctor.
        Get the latest HF data and render it in the window
        """
        data = self.get_latest_hf_data(HudOverlayData)
        if not data:
            return

        self.set_qml_property("circuitPosM", data.circuit_pos_m)
        self.set_qml_property("circuitLength", data.circuit_length or self.circuit_info_length)

        sectors = self.tracks_db.get_sectors(data.circuit_num)
        self.set_qml_property(
            "sectorsInfo",
            {"s1": sectors.s1, "s2": sectors.s2} if sectors else None,
        )

        self.set_qml_property("segmentInfo", self._get_segment_dict(data))

    def _get_segment_dict(self, data: HudOverlayData) -> Optional[Dict[str, Any]]:
        """Get the segment info for the current circuit position.
           Dict will contain "type", "above" and "below" keys.
        """
        qml_segment = None
        if segment_info := self.tracks_db.get_segment_info(data.circuit_num, data.circuit_pos_m):
            match segment_info.TYPE:
                case "straight":
                    qml_segment = {
                        "type": "straight",
                        "above": segment_info.name,
                        "below": "",
                    }
                case "corner":
                    corner_segment: CornerSegmentInfo = segment_info
                    if segment_info.name:
                        below = f"T{corner_segment.corner_number}"
                    else:
                        below = f"Turn {corner_segment.corner_number}"
                    qml_segment = {
                        "type": "corner",
                        "above": corner_segment.name,
                        "below": below,
                    }
                case "complex_corner":
                    complex_segment: ComplexCornerSegmentInfo = segment_info
                    first, last = complex_segment.corner_numbers[0], complex_segment.corner_numbers[-1]
                    qml_segment = {
                        "type": "corner",
                        "above": complex_segment.name,
                        "below": f"Turns {first}-{last}",
                    }
        return qml_segment
