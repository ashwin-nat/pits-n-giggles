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
    KEY = "weather_forecast"
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
    TEXT_FONT_SIZE = 13
    EMOJI_FONT_FACE = "Montserrat"
    EMOJI_FONT_SIZE = 22
    MAX_SAMPLES = 5

    def __init__(self, parent: QWidget, logger: logging.Logger, scale_factor: float):
        """Initialise the weather forecast page.

        Args:
            parent (QWidget): Parent widget
            logger (logging.Logger): Logger
            scale_factor (float): Scale factor
        """
        self.scale_factor = scale_factor
        super().__init__(parent, logger, f"{super().KEY}.{self.KEY}", scale_factor, title="Weather Forecast")
        self._last_processed_samples: List[Dict[str, Any]] = []

        # Compact horizontal layout filling available width
        self.forecast_container = QHBoxLayout()
        self.forecast_container.setSpacing(6)
        self.forecast_container.setContentsMargins(4, 4, 4, 4)
        self.forecast_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_layout.addLayout(self.forecast_container)
        self._init_event_handlers()

        self.logger.debug(f"{self.overlay_id} | Weather forecast widget initialized")

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
        card = self._create_card_widget()
        layout = self._create_card_layout(card)

        # Time
        time_label = self._create_time_label(data, card)
        layout.addWidget(time_label)

        # Emoji (icon)
        emoji_label = self._create_emoji_label(data, card)
        layout.addWidget(emoji_label)

        # Rain probability
        rain_label = self._create_rain_label(data, card)
        layout.addWidget(rain_label)

        return card

    def _create_card_widget(self) -> QWidget:
        """Create and configure the card widget container."""
        card = QWidget(self)
        card.setMinimumWidth(70)
        card.setMaximumWidth(200)
        card.setFixedHeight(70)
        card.setStyleSheet("background: transparent;")
        return card

    def _create_card_layout(self, parent: QWidget) -> QVBoxLayout:
        """Create and configure the card's vertical layout."""
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return layout

    def _create_time_label(self, data: Dict[str, Any], parent: QWidget) -> QLabel:
        """Create the time offset label."""
        time_offset = int(data.get("time-offset", 0))
        time_text = f"+{time_offset}m" if time_offset > 0 else "Now"
        return self._create_styled_label(
            text=time_text,
            parent=parent,
            font_size=self.text_font_size,
            style="color: #EEE; font-weight: 600;"
        )

    def _create_emoji_label(self, data: Dict[str, Any], parent: QWidget) -> QLabel:
        """Create the weather emoji label."""
        weather_type = data.get("weather", "Clear")
        emoji = self.WEATHER_EMOJIS.get(weather_type, "☀️")
        return self._create_styled_label(
            text=emoji,
            parent=parent,
            font_size=self.emoji_font_size,
            font_face=self.EMOJI_FONT_FACE
        )

    def _create_rain_label(self, data: Dict[str, Any], parent: QWidget) -> QLabel:
        """Create the rain probability label."""
        rain_prob = str(data.get("rain-probability", "0")).strip()
        return self._create_styled_label(
            text=f"💧{rain_prob}%",
            parent=parent,
            font_size=self.text_font_size,
            style="color: #7dafff; font-weight: bold;"
        )

    def _create_styled_label(
        self,
        text: str,
        parent: QWidget,
        font_size: int,
        font_face: str = None,
        style: str = ""
    ) -> QLabel:
        """Create a centered label with custom styling.

        Args:
            text: Label text
            parent: Parent widget
            font_size: Font size
            font_face: Font face (defaults to self.FONT_FACE)
            style: Additional CSS style string

        Returns:
            Configured QLabel instance
        """
        label = QLabel(text, parent)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        face = font_face if font_face is not None else self.FONT_FACE
        label.setFont(QFont(face, font_size))

        if style:
            label.setStyleSheet(style)

        return label

    def set_no_data_message(self) -> None:
        self._clear_forecast()
        label = QLabel("No forecast data", self)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setFont(QFont(self.FONT_FACE, self.text_font_size))
        label.setStyleSheet("color: #777; font-style: italic;")
        self.forecast_container.addWidget(label)

    @property
    def text_font_size(self) -> int:
        """Font size based on scale factor."""
        return int(self.TEXT_FONT_SIZE * self.scale_factor)

    @property
    def emoji_font_size(self) -> int:
        """Font size based on scale factor."""
        return int(self.EMOJI_FONT_SIZE * self.scale_factor)
