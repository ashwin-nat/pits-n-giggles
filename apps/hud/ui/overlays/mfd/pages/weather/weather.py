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
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, final

from PySide6.QtCore import QTimer
from PySide6.QtQuick import QQuickItem

from apps.hud.ui.overlays.mfd.pages.base_page import MfdPageBase

if TYPE_CHECKING:
    from apps.hud.ui.overlays.mfd.mfd import MfdOverlay

# -------------------------------------- CLASSES -----------------------------------------------------------------------

@dataclass
class SessionGroup:
    session_type: str
    items: List[Dict[str, Any]] = field(default_factory=list)

class WeatherForecastPage(MfdPageBase):

    KEY = "weather_forecast"
    QML_FILE: Path = Path(__file__).parent / "weather_page.qml"

    MAX_SAMPLES = 5

    def __init__(self, overlay: "MfdOverlay", logger: logging.Logger):
        self._last_processed_samples: List[Dict[str, Any]] = []
        self.session_index: int = 0
        self.num_sessions: int = 0
        self.session_uid: int = 0
        super().__init__(overlay, logger)
        self._init_event_handlers()

    def _init_event_handlers(self):
        """Initialize event handlers."""
        @self.on_event("race_table_update")
        def race_table_update(data: Dict[str, Any]) -> None:
            forecast_data_flat = data.get("weather-forecast-samples", [])
            if not forecast_data_flat:
                return

            # Reset index if session changes
            incoming_session_uid = data["session-uid"]
            if incoming_session_uid != self.session_uid:
                self._clear()
                self.session_uid = incoming_session_uid

            # Skip if data hasn't changed
            if forecast_data_flat == self._last_processed_samples:
                return

            self._display_weather_data(forecast_data_flat)

        @self.on_event("mfd_interact")
        def mfd_interact(data: Dict[str, Any]) -> None:
            self.logger.debug("%s | Received mfd_interact command. args: %s", self.KEY, data)
            # Cycle through the sessions
            self.session_index = (self.session_index + 1) % self.num_sessions
            last_data = self._last_processed_samples
            self._invalidate_cache()
            if last_data:
                self._display_weather_data(last_data)

    @final
    def on_page_activated(self, item: QQuickItem):
        super().on_page_activated(item)
        # Invalidate the cache after a delay
        QTimer.singleShot(1000, self._invalidate_cache)

    def _invalidate_cache(self):
        self._last_processed_samples = []

    def _group_by_session_type(self, data: List[Dict[str, Any]]) -> List[SessionGroup]:
        """Group data by session type. Order is preserved."""
        groups: List[SessionGroup] = []
        index: Dict[str, int] = {}

        for item in data:
            session = item["session-type"]
            if session not in index:
                index[session] = len(groups)
                groups.append(SessionGroup(session_type=session))
            groups[index[session]].items.append(item)

        return groups

    def _get_session_info(self, data: List[Dict[str, Any]]) -> Tuple[Optional[str], Optional[List[Dict[str, Any]]]]:

        """Get session info.

        Args:
            data (List[Dict[str, Any]]): Raw incoming weather forecast samples

        Returns:
            Tuple[Optional[str], Optional[List[Dict[str, Any]]]]: Session title and weather forecast list
        """
        if not data:
            return None, None

        groups = self._group_by_session_type(data)
        total = len(groups)

        if not (0 <= self.session_index < total):
            self.logger.warning(f"{self.KEY} | Invalid session index {self.session_index}. Resetting it to 0")
            self.session_index = 0

        session = groups[self.session_index]

        if total > 1:
            title = f"{session.session_type} ({self.session_index + 1}/{total})"
        else:
            title = session.session_type

        self.num_sessions = total

        return title, session.items

    def _clear(self):
        self._last_processed_samples = []
        self.session_index = 0
        self.num_sessions = 0

    def _display_weather_data(self, forecast_data_flat: List[Dict[str, Any]]) -> None:
        """Display weather data.

        Args:
            forecast_data_flat (List[Dict[str, Any]]): Raw incoming weather forecast samples
        """
        assert forecast_data_flat

        page_item = self._page_item
        if not page_item:
            return

        session_title, session_forecast = self._get_session_info(forecast_data_flat)

        page_item.setProperty("forecastData", session_forecast[: self.MAX_SAMPLES])
        page_item.setProperty("sessionTitle", session_title or "")

        self._last_processed_samples = forecast_data_flat
