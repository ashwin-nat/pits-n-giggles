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
from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon, QPixmap
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout,
                               QWidget)

from apps.hud.ui.overlays.mfd.pages.base_page import BasePage
from lib.assets_loader import load_icon

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class WeatherForecastCard:
    """Individual forecast card containing all labels."""

    def __init__(self, parent: QWidget, scale_factor: float, font_face: str,
                 track_temp_icon: QIcon, air_temp_icon: QIcon, logger: logging.Logger):
        self.scale_factor = scale_factor
        self.font_face = font_face
        self.logger = logger
        self.track_icon = track_temp_icon
        self.air_icon = air_temp_icon

        # Create card container
        self.widget = QWidget(parent)
        self.widget.setFixedWidth(int(100 * scale_factor))
        self.widget.setMinimumHeight(int(180 * scale_factor))
        self.widget.setStyleSheet("background: transparent;")

        # Vertical layout for card
        self.layout = QVBoxLayout(self.widget)
        self.layout.setContentsMargins(4, 6, 4, 6)
        self.layout.setSpacing(4)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Create time and emoji labels
        self.time_label = self._create_label(int(12 * scale_factor), "color: #EEE; font-weight: 600;")
        self.emoji_label = self._create_label(int(24 * scale_factor), "")

        # Track temperature row (icon + temp + change)
        self.track_row = self._create_temp_row(self.track_icon, int(16 * scale_factor))
        self.track_temp_label = self.track_row["temp_label"]
        self.track_change_label = self.track_row["change_label"]

        # Air temperature row (icon + temp + change)
        self.air_row = self._create_temp_row(self.air_icon, int(16 * scale_factor))
        self.air_temp_label = self.air_row["temp_label"]
        self.air_change_label = self.air_row["change_label"]

        # Rain label
        self.rain_label = self._create_label(int(11 * scale_factor), "color: #7dafff; font-weight: bold;")

        # Add to layout
        self.layout.addWidget(self.time_label)
        self.layout.addWidget(self.emoji_label)
        self.layout.addWidget(self.track_row["widget"])
        self.layout.addWidget(self.air_row["widget"])
        self.layout.addWidget(self.rain_label)
        self.layout.addStretch()

    def _create_label(self, font_size: int, style: str) -> QLabel:
        """Create a centered label with styling."""
        label = QLabel("", self.widget)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setFont(QFont(self.font_face, font_size))
        if style:
            label.setStyleSheet(style)
        return label

    def _create_temp_row(self, icon: QIcon, icon_size: int) -> Dict[str, Any]:
        """Create a horizontal row with icon, temperature, and change indicator."""
        row_widget = QWidget(self.widget)
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(4)
        row_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Icon
        icon_label = QLabel(row_widget)
        pixmap = icon.pixmap(icon_size, icon_size)
        icon_label.setPixmap(pixmap)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Temperature value
        temp_label = QLabel("", row_widget)
        temp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        temp_label.setFont(QFont(self.font_face, int(11 * self.scale_factor)))
        temp_label.setStyleSheet("color: #EEE; font-weight: bold;")

        # Change indicator
        change_label = QLabel("", row_widget)
        change_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        change_label.setFont(QFont(self.font_face, int(14 * self.scale_factor)))

        row_layout.addWidget(icon_label)
        row_layout.addWidget(temp_label)
        row_layout.addWidget(change_label)

        return {
            "widget": row_widget,
            "temp_label": temp_label,
            "change_label": change_label
        }

    def update_data(self, data: Dict[str, Any], weather_emojis: Dict[str, str]) -> None:
        """Update card with forecast data."""
        # Time
        time_offset = int(data.get("time-offset", 0))
        time_text = f"+{time_offset}m" if time_offset > 0 else "Now"
        self.time_label.setText(time_text)

        # Weather emoji
        weather_type = data.get("weather", "Clear")
        emoji = weather_emojis.get(weather_type, "☀️")
        self.emoji_label.setText(emoji)

        # Track temperature
        track_temp = data.get("track-temperature", "N/A")
        self.track_temp_label.setText(f"{track_temp}°C")

        # Track temperature change
        track_change = data.get("track-temperature-change", "No Temperature Change")
        track_arrow = self._get_temp_arrow(track_change)
        self.track_change_label.setText(track_arrow)
        self.track_change_label.setStyleSheet(self._get_temp_color(track_change))

        # Air temperature
        air_temp = data.get("air-temperature", "N/A")
        self.air_temp_label.setText(f"{air_temp}°C")

        # Air temperature change
        air_change = data.get("air-temperature-change", "No Temperature Change")
        air_arrow = self._get_temp_arrow(air_change)
        self.air_change_label.setText(air_arrow)
        self.air_change_label.setStyleSheet(self._get_temp_color(air_change))

        # Rain probability
        rain_prob = str(data.get("rain-percentage", "0")).strip()
        self.rain_label.setText(f"💧 {rain_prob}%")

        # Show rows + emoji when data is present
        self.emoji_label.show()
        self.track_row["widget"].show()
        self.air_row["widget"].show()
        self.rain_label.show()

        self.widget.show()
    def clear(self) -> None:
        """Clear all data but keep the card visible with fixed size."""

        # Clear text
        self.time_label.setText("")
        self.emoji_label.setText("")
        self.track_temp_label.setText("")
        self.track_change_label.setText("")
        self.air_temp_label.setText("")
        self.air_change_label.setText("")
        self.rain_label.setText("")

        # Hide rows & emoji so empty cards look blank
        self.emoji_label.hide()
        self.track_row["widget"].hide()
        self.air_row["widget"].hide()
        self.rain_label.hide()

        # Keep card visible to preserve layout spacing
        self.widget.show()

    @staticmethod
    def _get_temp_arrow(change: str) -> str:
        """Get arrow indicator for temperature change."""
        if change == "Temperature Up":
            return "▲"
        elif change == "Temperature Down":
            return "▼"
        else:
            return "─"

    @staticmethod
    def _get_temp_color(change: str) -> str:
        """Get color style for temperature change."""
        if change == "Temperature Up":
            return "color: #ff6666; font-weight: bold;"
        elif change == "Temperature Down":
            return "color: #6699ff; font-weight: bold;"
        else:
            return "color: #999999; font-weight: bold;"


class WeatherForecastPage(BasePage):
    """Weather forecast widget showing detailed forecast data."""
    KEY = "weather_forecast"
    WEATHER_EMOJIS = {
        "Clear": "☀️",
        "Light Cloud": "🌤️",
        "Overcast": "☁️",
        "Light Rain": "🌦️",
        "Heavy Rain": "🌧️",
        "Storm": "⛈️",
        "Thunderstorm": "⛈️"
    }

    FONT_FACE = "Consolas"
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
        self._cards: List[WeatherForecastCard] = []
        self._separators: List[QLabel] = []

        # Load icons
        icon_base_tyres = Path("assets") / "overlays"
        self.track_temp_icon = load_icon(icon_base_tyres / "road.svg", self.logger.debug, self.logger.error)
        self.air_temp_icon = load_icon(icon_base_tyres / "thermometer-half.svg", self.logger.debug, self.logger.error)

        self._build_ui()
        self._init_event_handlers()

        self.logger.debug(f"{self.overlay_id} | Weather forecast widget initialized")

    def _build_ui(self) -> None:
        """Build the UI with pre-created cards."""
        # Horizontal layout for cards
        self.forecast_container = QHBoxLayout()
        self.forecast_container.setSpacing(8)
        self.forecast_container.setContentsMargins(4, 4, 4, 4)
        self.forecast_container.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Create MAX_SAMPLES cards with separators
        for i in range(self.MAX_SAMPLES):
            card = WeatherForecastCard(self, self.scale_factor, self.FONT_FACE,
                                      self.track_temp_icon, self.air_temp_icon, self.logger)
            card.clear()  # Start hidden
            self._cards.append(card)
            self.forecast_container.addWidget(card.widget)

            # Add separator after each card except the last one
            if i < self.MAX_SAMPLES - 1:
                separator = QLabel(self)
                separator.setFixedWidth(1)
                separator.setFixedHeight(int(120 * self.scale_factor))
                separator.setStyleSheet("background-color: #444444;")
                separator.hide()  # Start hidden
                self._separators.append(separator)
                self.forecast_container.addWidget(separator, alignment=Qt.AlignmentFlag.AlignVCenter)

        # Add stretch before and after to center vertically
        self.page_layout.addStretch()
        self.page_layout.addLayout(self.forecast_container)
        self.page_layout.addStretch()

    def _init_event_handlers(self) -> None:
        @self.on_event("race_table_update")
        def update(data: Dict[str, Any]) -> None:
            forecast_data = data.get("weather-forecast-samples", [])[: self.MAX_SAMPLES]

            if not forecast_data:
                self._clear_all_cards()
                return

            if forecast_data == self._last_processed_samples:
                return

            # Update cards with data
            for i, card in enumerate(self._cards):
                if i < len(forecast_data):
                    card.update_data(forecast_data[i], self.WEATHER_EMOJIS)
                else:
                    card.clear()

            # Update separator visibility - show separator only between visible cards
            for i, separator in enumerate(self._separators):
                # Show separator if both adjacent cards are visible
                if forecast_data:
                    separator.show()
                else:
                    separator.hide()

            self._last_processed_samples = forecast_data

    def _clear_all_cards(self) -> None:
        """Clear and hide all cards."""
        for card in self._cards:
            card.clear()
        for separator in self._separators:
            separator.hide()
        self._last_processed_samples = []
