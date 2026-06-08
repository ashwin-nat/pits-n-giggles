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

from PySide6.QtCore import QObject, QUrl

from apps.hud.ui.overlays.base import BaseOverlayQML
from apps.hud.ui.overlays.mfd.pages.base_page import MfdPageBase
from lib.config import OverlayPosition

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class StandalonePageOverlay(BaseOverlayQML, MfdPageBase):
    QML_FILE: Path = Path(__file__).parent / "standalone_wrapper.qml"
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
    ):
        MfdPageBase.__init__(self, overlay=None, logger=logger)
        self.setup_overlay()
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
        self.root.setProperty("pageSource", QUrl.fromLocalFile(str(self.PAGE_QML_FILE.resolve())))
        loader = self.root.findChild(QObject, "pageContent")
        assert loader is not None, f"{self.KEY} | standalone QML missing Loader with objectName 'pageContent'"
        page_item = loader.property("item")
        assert page_item is not None, f"{self.KEY} | Loader 'pageContent' item is None — page QML failed to load"
        self._on_page_activated(page_item)
        self._wire_standalone_handlers()

    def _wire_standalone_handlers(self):
        """Bridge page handlers into the overlay event system so broadcast events reach this page."""
        for event_type, handler in self._handlers.items():
            self.on_event(event_type)(lambda data, _h=handler: _h(data))

    @classmethod
    def _create_mfd_object(cls, overlay, logger: logging.Logger):
        """Allocate and initialise only the MfdPageBase half of this object.

        Uses __new__ + explicit MfdPageBase.__init__ to skip StandalonePageOverlay.__init__,
        which would call BaseOverlayQML.__init__ and open a Qt window. Called by
        create_for_mfd before _configure and setup_overlay.
        """
        obj = MfdPageBase.__new__(cls)
        MfdPageBase.__init__(obj, overlay=overlay, logger=logger)
        return obj

    def _configure(self) -> None:
        """Set page-specific config fields before _setup_page is called.

        Override in subclasses that require config kwargs (e.g. fuel_est_mode).
        Those subclasses also add the matching typed params to their _configure signature.
        Base implementation is a no-op for pages with no config kwargs.
        """

    @classmethod
    def create_for_mfd(cls, overlay, logger: logging.Logger, **kwargs) -> MfdPageBase:
        """Create an MFD-hosted instance.

        kwargs are forwarded verbatim to _configure so subclasses receive their
        typed config values without needing to override this classmethod.
        """
        obj = cls._create_mfd_object(overlay, logger)
        obj._configure(**kwargs)
        obj.setup_overlay()
        return obj

    def render_frame(self):
        pass  # telemetry-driven; no fixed-rate rendering needed
