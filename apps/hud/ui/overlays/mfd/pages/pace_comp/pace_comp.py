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
from typing import TYPE_CHECKING, Any, Dict, final

from PySide6.QtCore import QTimer
from PySide6.QtQuick import QQuickItem

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
        self._last_processed_data: Dict[str, Any] = {}
        self._init_handlers()

    def _init_handlers(self):
        @self.on_event("stream_overlay_update")
        def update(data: Dict[str, Any]) -> None:
            item: QQuickItem | None = self._page_item
            if not item:
                return

            payload = data.get("pace-comparison")
            if not payload or payload == self._last_processed_data:
                return

            player = payload.get("player", {})
            prev = payload.get("prev", {})
            next_ = payload.get("next", {})

            item.setProperty("playerRow", self._row_player(player))
            item.setProperty("prevRow", self._row_other(prev, player))
            item.setProperty("nextRow", self._row_other(next_, player))

            self._last_processed_data = payload

    @final
    def on_page_activated(self, item: QQuickItem):
        super().on_page_activated(item)
        QTimer.singleShot(1000, self._invalidate_cache)

    def _invalidate_cache(self):
        self._last_processed_data = {}

    def _fmt_abs_lap(self, ms: int | None) -> str:
        if not ms or ms <= 0:
            return "--:--.---"
        return F1Utils.millisecondsToMinutesSecondsMilliseconds(ms)

    def _fmt_abs_sector(self, ms: int | None) -> str:
        if not ms or ms <= 0:
            return "--.---"
        return F1Utils.millisecondsToSecondsMilliseconds(ms)

    def _fmt_rel(self, ms: int | None, ref: int | None) -> str:
        if not ms or not ref:
            return "---"
        d = (ms - ref) / 1000.0
        sign = "+" if d > 0 else ""
        return f"{sign}{d:.3f}"

    def _row_player(self, p: Dict[str, Any]) -> Dict[str, str]:
        return {
            "name": p.get("name", "---"),
            "s1": self._fmt_abs_sector(p.get("sector-1-ms")),
            "s2": self._fmt_abs_sector(p.get("sector-2-ms")),
            "s3": self._fmt_abs_sector(p.get("sector-3-ms")),
            "lap": self._fmt_abs_lap(p.get("lap-ms")),
        }

    def _row_other(self, o: Dict[str, Any], p: Dict[str, Any]) -> Dict[str, str]:
        return {
            "name": o.get("name", "---"),
            "s1": self._fmt_rel(o.get("sector-1-ms"), p.get("sector-1-ms")),
            "s2": self._fmt_rel(o.get("sector-2-ms"), p.get("sector-2-ms")),
            "s3": self._fmt_rel(o.get("sector-3-ms"), p.get("sector-3-ms")),
            "lap": self._fmt_rel(o.get("lap-ms"), p.get("lap-ms")),
        }
