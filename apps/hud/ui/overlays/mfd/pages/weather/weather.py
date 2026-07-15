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

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, final

from PySide6.QtCore import QTimer

from apps.hud.ui.overlays.mfd.pages.base_page import MfdPageBase
from lib.config import MfdPageId, OverlayId, PngSettings, WeatherMFDUIType
from lib.logger import PngLogger

# -------------------------------------- CLASSES -----------------------------------------------------------------------

@dataclass
class SessionGroup:
    session_type: str
    items: List[Dict[str, Any]] = field(default_factory=list)

class WeatherForecastPage(MfdPageBase):

    OVERLAY_ID = OverlayId.WEATHER
    KEY = MfdPageId.WEATHER_FORECAST
    PAGE_QML_FILE: Path = Path(__file__).parent / "weather_page.qml"

    MAX_SAMPLES = 5

    @classmethod
    def from_settings(cls, settings: PngSettings, logger: PngLogger) -> "WeatherForecastPage":
        return cls(
            logger,
            graph_based_ui=(settings.HUD.mfd_weather_page_ui_type == WeatherMFDUIType.GRAPH),
        )

    @classmethod
    def standalone_show_title(cls, settings: PngSettings) -> bool:
        return settings.HUD.weather_show_title

    def __init__(self, logger: PngLogger, graph_based_ui: bool):
        self.graph_based_ui = graph_based_ui
        super().__init__(logger)

    @final
    def setup_page(self):
        self._last_processed_samples: List[Dict[str, Any]] = []
        self.session_index: int = 0
        self.num_sessions: int = 0
        self.session_uid: int = 0

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

            self._display_weather_data(forecast_data_flat)

        @self.on_event("mfd_interact")
        def mfd_interact(data: Dict[str, Any]) -> None:
            self.logger.debug("%s | Received mfd_interact command. args: %s", self.KEY, data)
            if not self.num_sessions:
                self.logger.debug("%s | No sessions available. Ignoring mfd_interact command.", self.KEY)
                return

            # Cycle through the sessions
            self.session_index = (self.session_index + 1) % self.num_sessions
            last_data = self._last_processed_samples
            self._invalidate_cache()
            if last_data:
                self._display_weather_data(last_data)

    @final
    def on_page_activated(self):
        self.set_qml_property("graphBasedUI", self.graph_based_ui)
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
            self.logger.warning("%s | Invalid session index %s. Resetting it to 0", self.KEY, self.session_index)
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

        session_title, session_forecast = self._get_session_info(forecast_data_flat)

        self.set_qml_property("forecastData", session_forecast[: self.MAX_SAMPLES])
        self.set_qml_property("sessionTitle", session_title or "")

        self._last_processed_samples = forecast_data_flat
