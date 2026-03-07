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
from typing import final, Optional
from apps.hud.ui.infra.hf_types import DummyHFType

from apps.hud.ui.overlays.base import BaseOverlayQML
from lib.config import OverlayPosition

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class TemplateOverlay(BaseOverlayQML):
    """
    Extremely minimal QML overlay template.

    - Loads QML
    - Shows window
    """

    # Remember to update the spec file with the new QML path
    QML_FILE = Path(__file__).parent / "minimal_overlay.qml"
    OVERLAY_ID = "minimal_overlay" # Hard code the overlay ID in lib/config/schema/hud/layout.py and use it here

    def __init__(
        self,
        config: OverlayPosition,
        logger: logging.Logger,
        locked: bool,
        opacity: int,
        scale_factor: float,
        windowed_overlay: bool,
        refresh_interval_ms: Optional[int] = None,  # Set none for event-driven rendering (low frequency)
    ) -> None:

        super().__init__(
            config=config,
            logger=logger,
            locked=locked,
            opacity=opacity,
            scale_factor=scale_factor,
            windowed_overlay=windowed_overlay,
            refresh_interval_ms=refresh_interval_ms,
        )

        # For low frequency/low refresh rate overlays, register event handlers here and update window in the handlers.
        self._register_event_handlers()

        # For high frequency/high refresh rate overlays, subscribe to HF types here and render in render_frame.
        self.subscribe_hf(DummyHFType)

    ## For high frequency data, register HF types in ctor and render periodically in render_frame.
    @final
    def render_frame(self):
        """
        This will be called by the base class periodically based on the refresh rate specified in the ctor.
        Get the latest HF data and render it in the window
        """
        dummy_obj = self.get_latest_hf_data(DummyHFType)
        if not dummy_obj:
            return

        pass

    def _register_event_handlers(self):
        """
        Register incoming data event handlers here
        """

        @self.on_event("dummy-event")
        def handle_dummy_event(_data):
            self.logger.info("Received dummy event")
