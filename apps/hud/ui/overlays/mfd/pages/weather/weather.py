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
from typing import Any, Dict, List, final

from apps.hud.ui.overlays.mfd.pages.base_page import MfdPageBase

from PySide6.QtCore import QTimer

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class WeatherForecastPage(MfdPageBase):

    KEY = "weather_forecast"
    QML_FILE: Path = Path(__file__).parent / "weather_page.qml"

    MAX_SAMPLES = 5

    def __init__(self, overlay, logger: logging.Logger):
        self._last_processed_samples: List[Dict[str, Any]] = []
        super().__init__(overlay, logger)
        self._init_event_handlers()

    def _init_event_handlers(self):
        """Initialize event handlers."""
        @self.on_event("race_table_update")
        def race_table_update(data: Dict[str, Any]) -> None:
            forecast_data = data.get("weather-forecast-samples", [])[: self.MAX_SAMPLES]

            # Skip if data hasn't changed
            if forecast_data == self._last_processed_samples:
                return

            page_item = self.overlay.current_page_item
            if not page_item:
                return

            page_item.setProperty("forecastData", forecast_data)
            self._last_processed_samples = forecast_data

    @final
    def on_page_active(self):
        # Invalidate the cache after a delay
        QTimer.singleShot(1000, self._invalidate_cache)

    def _invalidate_cache(self):
        self._last_processed_samples = []
