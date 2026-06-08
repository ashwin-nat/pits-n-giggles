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

from apps.hud.ui.overlays.base import BaseOverlayQML
from apps.hud.ui.overlays.mfd.pages.base_page import MfdPageBase
from lib.config import OverlayPosition

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class StandalonePageOverlay(BaseOverlayQML, MfdPageBase):
    """Base for MFD pages that can also run as standalone always-on-top overlay windows.

    MRO: StandalonePageOverlay → BaseOverlayQML → BaseOverlay → QObject → MfdPageBase
    - self.on_event       → BaseOverlayQML  (overlay command handlers)
    - self.on_page_event  → MfdPageBase     (page data handlers)

    Concrete subclasses must define: KEY, PAGE_QML_FILE, QML_FILE, OVERLAY_ID.
    """

    def __init__(
        self,
        config: OverlayPosition,
        logger: logging.Logger,
        locked: bool,
        opacity: int,
        scale_factor: float,
        windowed_overlay: bool,
        **page_kwargs,
    ):
        for k, v in page_kwargs.items():
            setattr(self, k, v)
        MfdPageBase.__init__(self, overlay=None, logger=logger)  # pylint: disable=unnecessary-dunder-call
        self._init_event_handlers()
        BaseOverlayQML.__init__(
            self,
            config=config,
            logger=logger,
            locked=locked,
            opacity=opacity,
            scale_factor=scale_factor,
            windowed_overlay=windowed_overlay,
            refresh_interval_ms=None,
        )

    def post_setup(self):
        self._on_page_activated(self.root)
        self._wire_standalone_handlers()

    def _wire_standalone_handlers(self):
        """Bridge page handlers into the overlay event system so broadcast events reach this page."""
        for event_type, handler in self._handlers.items():
            self.on_event(event_type)(lambda data, _h=handler: _h(data))

    @classmethod
    def create_for_mfd(cls, overlay, logger: logging.Logger, **kwargs) -> MfdPageBase:
        """Create a page instance for MFD-hosted use without opening a Qt window.

        Uses __new__ + explicit MfdPageBase.__init__ to allocate the object and
        initialise only the page half of the class, deliberately bypassing
        StandalonePageOverlay.__init__ (which would call BaseOverlayQML.__init__
        and open a Qt window).
        """
        obj = MfdPageBase.__new__(cls)
        for k, v in kwargs.items():
            setattr(obj, k, v)
        MfdPageBase.__init__(obj, overlay=overlay, logger=logger)  # pylint: disable=unnecessary-dunder-call
        obj._init_event_handlers()
        return obj

    def render_frame(self):
        pass  # telemetry-driven; no fixed-rate rendering needed
