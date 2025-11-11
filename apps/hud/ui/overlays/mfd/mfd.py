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
from typing import Any, Dict, Optional

from PySide6.QtCore import QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout

from apps.hud.ui.infra.config import OverlaysConfig
from apps.hud.ui.overlays.base import BaseOverlay
from lib.f1_types import F1Utils


# -------------------------------------- CLASSES -----------------------------------------------------------------------

class MfdOverlay(BaseOverlay):

    OVERLAY_ID: str = "mfd"

    def __init__(self, config: OverlaysConfig, logger: logging.Logger, locked: bool, opacity: int):

        # Overlay specific fields
        self.curr_session_uid = None
        self.curr_lap_num: Optional[int] = None

        # constants
        self._default_time_str = "--:--.---"

        super().__init__(self.OVERLAY_ID, config, logger, locked, opacity)
        self._init_cmd_handlers()
        self.curr_lap_display_timer: QTimer = QTimer(self)

    def build_ui(self):

        # TODO: implement
        pass

    def _init_cmd_handlers(self):

        @self.on_command("race_table_update")
        def handle_race_update(data: Dict[str, Any]) -> None:
            pass

    def clear(self):
        pass
