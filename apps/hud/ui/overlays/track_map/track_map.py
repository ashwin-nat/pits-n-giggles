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

# pylint: disable-all

import logging
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Optional

from apps.hud.ui.overlays.base import BaseOverlayQML
from lib.config import OverlayPosition

# -------------------------------------- CLASSES -----------------------------------------------------------------------

# NOTE: All track map SVG's were fetched and constructed from https://api.multiviewer.app/api/v1/circuits/{track_id}/2025
# To get a list of all track ID's https://api.multiviewer.app/api/v1/circuits

class TrackMapOverlay(BaseOverlayQML):
    """
    Track map overlay that displays an SVG representation of the current circuit.

    - Loads appropriate SVG based on circuit name
    - Displays the track map in the QML window
    - Updates when circuit changes
    """

    QML_FILE = Path(__file__).parent / "track_map.qml"
    OVERLAY_ID = "track_map"

    TEAM_COLOURS_HEX = defaultdict(
        lambda: '#FFFFFF',
        {
            'Red Bull Racing': '#3671C6',
            'Red Bull': '#3671C6',

            'VCARB': '#6692FF',
            'RB': '#6692FF',

            'Mercedes': '#27F4D2',
            'Ferrari': '#E8002D',
            'McLaren': '#FF8000',
            'Mclaren': '#FF8000',
            'Aston Martin': '#229971',
            'Alpine': '#FF87BC',

            'Alpha Tauri': '#1E2850',
            'Alfa Romeo': '#9B0000',
            'Haas': '#B6BABD',
            'Williams': '#64C4FF',
            'Sauber': '#52E252',
        }
    )

    def __init__(self,
                 config: OverlayPosition,
                 logger: logging.Logger,
                 locked: bool,
                 opacity: int,
                 scale_factor: float,
                 windowed_overlay: bool,
                 refresh_interval_ms: int) -> None:

        assert refresh_interval_ms
        super().__init__(config, logger, locked, opacity, scale_factor, windowed_overlay, refresh_interval_ms)
        self._init_handlers()

        self.curr_circuit_name: Optional[str] = None
        self.circuit_svg_path: Optional[str] = None

    def _init_handlers(self):

        @self.on_event("stream_overlay_update")
        def _handle_stream_overlay_update(data: Dict[str, Any]):

            circuit = data["circuit-enum-name"]
            if not circuit and self.curr_circuit_name:
                # Clear map if no circuit
                self._clear_track_map()
                return

            motion_list = data["motion"]
            if not motion_list:
                return

            # Load new circuit if changed
            if circuit != self.curr_circuit_name:
                self.curr_circuit_name = circuit
                self.circuit_svg_path = self._get_circuit_svg_path(circuit)
                self._update_qml_track_map()
                self.logger.debug(f"{self.OVERLAY_ID} | Loaded new circuit: {circuit}")

            # TODO: Process car positions from motion_list
            for car in motion_list:
                name = car["name"]
                team = car["team"]
                index = car["index"]
                ers_mode = car["ers"]["mode"]
                motion_data = car["motion"]
                if not motion_data:
                    continue

                world_pos = motion_data["world-position"]
                world_vel = motion_data["world-velocity"]
                world_fwd_dir = motion_data["world-forward-dir"]
                world_right_dir = motion_data["world-right-dir"]
                orientation = motion_data["orientation"]

    def _get_circuit_svg_path(self, circuit_name: str) -> Optional[str]:
        """
        Get the absolute file path to the circuit SVG.
        Returns the path as a string suitable for QML Image source.
        """
        suffix = "_Reverse"
        base_path = Path("assets") / "track-maps"
        svg_name = f"{(circuit_name[:-len(suffix)] if circuit_name.endswith(suffix) else circuit_name)}.svg"

        svg_path = base_path / svg_name

        if not svg_path.exists():
            self.logger.error(f"{self.OVERLAY_ID} | SVG not found: {svg_path}")
            return None

        # Return absolute path as file URL for QML
        abs_path = svg_path.resolve()
        return abs_path.as_uri()

    def _update_qml_track_map(self):
        """Update the QML window with the new track map."""
        if self._root and self.circuit_svg_path:
            self._root.setProperty("svgPath", self.circuit_svg_path)
            self.logger.debug(f"{self.OVERLAY_ID} | Updated QML with SVG: {self.circuit_svg_path}")
        else:
            self.logger.warning(f"{self.OVERLAY_ID} | Cannot update QML - root={self._root}, path={self.circuit_svg_path}")

    def _clear_track_map(self):
        """Clear the track map from the QML window."""
        self._root.setProperty("svgPath", "")
        self.curr_circuit_name = None
        self.circuit_svg_path = None
        self.logger.debug(f"{self.OVERLAY_ID} | Cleared track map")
