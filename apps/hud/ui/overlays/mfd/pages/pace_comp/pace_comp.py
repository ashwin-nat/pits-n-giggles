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
from typing import Any, Dict, TYPE_CHECKING, final

from PySide6.QtQuick import QQuickItem
from PySide6.QtCore import QTimer

from apps.hud.common import get_ref_row, is_race_type_session
from apps.hud.ui.overlays.mfd.pages.base_page import MfdPageBase
from lib.f1_types import F1Utils

if TYPE_CHECKING:
    from apps.hud.ui.overlays.mfd.mfd import MfdOverlay

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class PaceCompPage(MfdPageBase):
    KEY = "pace_comp"
    QML_FILE: Path = Path(__file__).parent / "pace_comp.qml"

    def __init__(self, overlay: "MfdOverlay", logger: logging.Logger):
        super().__init__(overlay, logger)
        self._last_processed_data = {}
        self._init_handlers()

    def _init_handlers(self):
        @self.on_event("stream_overlay_update")
        def update(data: Dict[str, Any]) -> None:
            """Update fuel information display."""

            page_item = self._page_item
            if not page_item:
                return

            pace_comp_data = data["pace-comparison"]
            if self._last_processed_data == pace_comp_data:
                return  # No changes

            player_data = pace_comp_data["player"]
            next_data = pace_comp_data["next"]
            prev_data = pace_comp_data["prev"]


            # TODO: update data

            # "player": {
            #   "ers": {
            #     "ers-deployed-this-lap": null,
            #     "ers-harvested-by-mguk-this-lap": null,
            #     "ers-mode": null,
            #     "ers-percent": null
            #   },
            #   "lap-ms": null,
            #   "name": null,
            #   "sector-1-ms": null,
            #   "sector-2-ms": null,
            #   "sector-3-ms": null
            # },

            self._last_processed_data = pace_comp_data

    @final
    def on_page_activated(self, item: QQuickItem):
        super().on_page_activated(item)
        # Invalidate the cache after a delay
        QTimer.singleShot(1000, self._invalidate_cache)

    def _invalidate_cache(self):
        self._last_processed_data = {}
