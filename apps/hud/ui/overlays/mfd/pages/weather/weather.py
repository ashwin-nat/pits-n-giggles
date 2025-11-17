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
from typing import Any, Dict, List

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout,
                               QWidget)

from apps.hud.ui.overlays.mfd.pages.base_page import BasePage

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class WeatherForecastPage(BasePage):
    """Ultra-compact weather forecast widget showing time, emoji, and rain %."""

    WEATHER_EMOJIS = {
        "Clear": "☀️",
        "Light Cloud": "☁️",
        "Overcast": "☁️",
        "Light Rain": "🌦️",
        "Heavy Rain": "🌧️",
        "Storm": "⛈️",
        "Thunderstorm": "⛈️"
    }

    FONT_FACE = "Montserrat"
    TIME_FONT_SIZE = 13
    RAIN_FONT_SIZE = 13
    EMOJI_FONT_FACE = "Montserrat"
    EMOJI_FONT_SIZE = 22
    MAX_SAMPLES = 5

    def __init__(self, parent: QWidget, logger: logging.Logger):
        """Initialise the weather forecast page.

        Args:
            parent (QWidget): Parent widget
            logger (logging.Logger): Logger
        """
        super().__init__(parent, logger, "mfd.weather_forecast", title="Weather Forecast")
        self._last_processed_samples: List[Dict[str, Any]] = []

        # Compact horizontal layout filling available width
        self.forecast_container = QHBoxLayout()
        self.forecast_container.setSpacing(6)
        self.forecast_container.setContentsMargins(4, 4, 4, 4)
        self.forecast_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_layout.addLayout(self.forecast_container)
        self._init_event_handlers()

        self.logger.info(f"{self.overlay_id} | Weather forecast widget initialized")

    def _init_event_handlers(self) -> None:
        @self.on_event("race_table_update")
        def update(data: Dict[str, Any]) -> None:
            forecast_data = data.get("weather-forecast-samples", [])[: self.MAX_SAMPLES]
            if not forecast_data:
                self.set_no_data_message()
                return

            if forecast_data == self._last_processed_samples:
                return

            self._clear_forecast()

            for item_data in forecast_data:
                card = self._create_forecast_item(item_data)
                card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
                self.forecast_container.addWidget(card, 1)

            self._last_processed_samples = forecast_data

    def _clear_forecast(self) -> None:
        while self.forecast_container.count():
            item = self.forecast_container.takeAt(0)
            if widget := item.widget():
                widget.deleteLater()

    def _create_forecast_item(self, data: Dict[str, Any]) -> QWidget:
        """
        Card layout:
            [time]
            [ emoji ]
            [rain %]
        """
        card = QWidget(self)
        card.setMinimumWidth(70)
        card.setMaximumWidth(200)
        card.setFixedHeight(70)
        card.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Time
        time_offset = int(data.get("time-offset", 0))
        time_text = f"+{time_offset}m" if time_offset > 0 else "Now"
        time_label = QLabel(time_text, card)
        time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        time_label.setFont(QFont(self.FONT_FACE, self.TIME_FONT_SIZE))
        time_label.setStyleSheet("color: #EEE; font-weight: 600;")
        layout.addWidget(time_label)

        # Emoji (icon)
        weather_type = data.get("weather", "Clear")
        emoji = self.WEATHER_EMOJIS.get(weather_type, "☀️")
        emoji_label = QLabel(emoji, card)
        emoji_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        emoji_label.setFont(QFont(self.EMOJI_FONT_FACE, self.EMOJI_FONT_SIZE))
        layout.addWidget(emoji_label)

        # Rain probability
        rain_prob = str(data.get("rain-probability", "0")).strip()
        rain_label = QLabel(f"💧{rain_prob}%", card)
        rain_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rain_label.setFont(QFont(self.FONT_FACE, self.RAIN_FONT_SIZE))
        rain_label.setStyleSheet("color: #7dafff; font-weight: bold;")
        layout.addWidget(rain_label)

        return card

    def set_no_data_message(self) -> None:
        self._clear_forecast()
        label = QLabel("No forecast data", self)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setFont(QFont(self.FONT_FACE, 8))
        label.setStyleSheet("color: #777; font-style: italic;")
        self.forecast_container.addWidget(label)
