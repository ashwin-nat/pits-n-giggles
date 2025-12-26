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
from typing import Any, Dict, List

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QWidget

from apps.hud.ui.overlays.mfd.pages.base_page import BasePage
from lib.assets_loader import load_icon

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class WeatherForecastCard:
    """Individual forecast card containing fixed-grid aligned UI elements."""

    # Font size constants
    TIME_FONT_SIZE = 15
    EMOJI_FONT_SIZE = 24
    TEMP_FONT_SIZE = 13
    CHANGE_FONT_SIZE = 14
    RAIN_FONT_SIZE = 13

    # Icon size constants
    ICON_SIZE = 16

    # Layout constants
    CARD_WIDTH = 100
    CARD_MIN_HEIGHT = 180
    ICON_COLUMN_WIDTH = 16
    TEMP_COLUMN_WIDTH = 30
    ARROW_COLUMN_WIDTH = 12

    def __init__(self, parent: QWidget, scale_factor: float, font_face: str,
                 track_temp_icon: QIcon, air_temp_icon: QIcon, logger: logging.Logger):
        self.scale_factor = scale_factor
        self.font_face = font_face
        self.logger = logger
        self.track_icon = track_temp_icon
        self.air_icon = air_temp_icon

        # Card container
        self.widget = QWidget(parent)
        self.widget.setFixedWidth(self.card_width)
        self.widget.setMinimumHeight(self.card_min_height)
        self.widget.setStyleSheet("background: transparent;")

        # Use grid layout for perfect alignment
        self.layout = QGridLayout(self.widget)
        self.layout.setColumnMinimumWidth(0, self.icon_column_width)
        self.layout.setColumnMinimumWidth(1, self.temp_column_width)
        self.layout.setColumnMinimumWidth(2, self.arrow_column_width)
        self.layout.setContentsMargins(4, 6, 4, 6)
        self.layout.setHorizontalSpacing(4)
        self.layout.setVerticalSpacing(6)

        # Column stretch so all cards align identically
        self.layout.setColumnStretch(0, 1)  # icon column
        self.layout.setColumnStretch(1, 2)  # temperature column
        self.layout.setColumnStretch(2, 1)  # arrow column

        # Create labels
        self.time_label = self._create_label(self.time_font_size, "color: #EEE; font-weight: 600;")
        self.emoji_label = self._create_label(self.emoji_font_size, "")

        # Track temp row
        self.track_row = self._create_temp_row(self.track_icon, self.icon_size)
        # Air temp row
        self.air_row = self._create_temp_row(self.air_icon, self.icon_size)

        # Rain label
        self.rain_label = self._create_label(self.rain_font_size, "color: #7dafff; font-weight: bold;")

        # Add widgets to fixed rows & columns
        self.layout.addWidget(self.time_label, 0, 0, 1, 3, Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.emoji_label, 1, 0, 1, 3, Qt.AlignmentFlag.AlignCenter)

        # Track row
        self.layout.addWidget(self.track_row["icon"],        2, 0)
        self.layout.addWidget(self.track_row["temp_label"],  2, 1)
        self.layout.addWidget(self.track_row["change_label"],2, 2)

        # Air row
        self.layout.addWidget(self.air_row["icon"],          3, 0)
        self.layout.addWidget(self.air_row["temp_label"],    3, 1)
        self.layout.addWidget(self.air_row["change_label"],  3, 2)

        # Rain
        self.layout.addWidget(self.rain_label, 4, 0, 1, 3, Qt.AlignmentFlag.AlignCenter)

        # Start empty
        self.clear()

    # ----------------------------------------------------------------------
    # Properties for scaled sizes

    @property
    def time_font_size(self) -> int:
        return int(self.TIME_FONT_SIZE * self.scale_factor)

    @property
    def emoji_font_size(self) -> int:
        return int(self.EMOJI_FONT_SIZE * self.scale_factor)

    @property
    def temp_font_size(self) -> int:
        return int(self.TEMP_FONT_SIZE * self.scale_factor)

    @property
    def change_font_size(self) -> int:
        return int(self.CHANGE_FONT_SIZE * self.scale_factor)

    @property
    def rain_font_size(self) -> int:
        return int(self.RAIN_FONT_SIZE * self.scale_factor)

    @property
    def icon_size(self) -> int:
        return int(self.ICON_SIZE * self.scale_factor)

    @property
    def card_width(self) -> int:
        return int(self.CARD_WIDTH * self.scale_factor)

    @property
    def card_min_height(self) -> int:
        return int(self.CARD_MIN_HEIGHT * self.scale_factor)

    @property
    def icon_column_width(self) -> int:
        return int(self.ICON_COLUMN_WIDTH * self.scale_factor)

    @property
    def temp_column_width(self) -> int:
        return int(self.TEMP_COLUMN_WIDTH * self.scale_factor)

    @property
    def arrow_column_width(self) -> int:
        return int(self.ARROW_COLUMN_WIDTH * self.scale_factor)

    # ----------------------------------------------------------------------

    def _create_label(self, font_size: int, style: str) -> QLabel:
        label = QLabel("", self.widget)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setFont(QFont(self.font_face, font_size))
        if style:
            label.setStyleSheet(style)
        return label

    def _create_temp_row(self, icon: QIcon, icon_size: int) -> Dict[str, Any]:
        icon_label = QLabel(self.widget)
        icon_label.setPixmap(icon.pixmap(icon_size, icon_size))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        temp_label = QLabel("", self.widget)
        temp_label.setFont(QFont(self.font_face, self.temp_font_size))
        temp_label.setStyleSheet("color: #EEE; font-weight: bold;")
        temp_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        change_label = QLabel("", self.widget)
        change_label.setFont(QFont(self.font_face, self.change_font_size))

        temp_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        change_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)


        return {
            "icon": icon_label,
            "temp_label": temp_label,
            "change_label": change_label
        }

    # ----------------------------------------------------------------------

    def update_data(self, data: Dict[str, Any], weather_emojis: Dict[str, str]) -> None:
        """Populate card with data and show all relevant widgets."""

        # Time
        time_offset = int(data.get("time-offset", 0))
        self.time_label.setText(f"+{time_offset}m" if time_offset > 0 else "Now")

        # Emoji
        self.emoji_label.setText(weather_emojis.get(data.get("weather", "Clear"), "☀️"))

        # Track temp
        self.track_row["temp_label"].setText(f"{data.get('track-temperature', 'N/A')}°C")
        change = data.get("track-temperature-change", "No Temperature Change")
        self.track_row["change_label"].setText(self._get_temp_arrow(change))
        self.track_row["change_label"].setStyleSheet(self._get_temp_color(change))

        # Air temp
        self.air_row["temp_label"].setText(f"{data.get('air-temperature', 'N/A')}°C")
        change = data.get("air-temperature-change", "No Temperature Change")
        self.air_row["change_label"].setText(self._get_temp_arrow(change))
        self.air_row["change_label"].setStyleSheet(self._get_temp_color(change))

        # Rain
        self.rain_label.setText(f"💧 {str(data.get('rain-percentage', '0')).strip()}%")

        # Ensure full card is visible
        self._show_all()

    # ----------------------------------------------------------------------

    def clear(self) -> None:
        """Clear content and hide inner widgets but preserve card area."""

        # Clear text
        self.time_label.setText("")
        self.emoji_label.setText("")
        self.track_row["temp_label"].setText("")
        self.track_row["change_label"].setText("")
        self.air_row["temp_label"].setText("")
        self.air_row["change_label"].setText("")
        self.rain_label.setText("")

        # Hide all inner elements
        self._hide_all()

        # But keep fixed card visible always
        self.widget.show()

    # ----------------------------------------------------------------------

    def _show_all(self):
        self.time_label.show()
        self.emoji_label.show()
        self.track_row["icon"].show()
        self.track_row["temp_label"].show()
        self.track_row["change_label"].show()
        self.air_row["icon"].show()
        self.air_row["temp_label"].show()
        self.air_row["change_label"].show()
        self.rain_label.show()

    def _hide_all(self):
        self.time_label.hide()
        self.emoji_label.hide()
        self.track_row["icon"].hide()
        self.track_row["temp_label"].hide()
        self.track_row["change_label"].hide()
        self.air_row["icon"].hide()
        self.air_row["temp_label"].hide()
        self.air_row["change_label"].hide()
        self.rain_label.hide()

    # ----------------------------------------------------------------------

    @staticmethod
    def _get_temp_arrow(change: str) -> str:
        if change == "Temperature Up":   return "▲"
        if change == "Temperature Down": return "▼"
        return "─"

    @staticmethod
    def _get_temp_color(change: str) -> str:
        if change == "Temperature Up":   return "color: #ff6666; font-weight: bold;"
        if change == "Temperature Down": return "color: #6699ff; font-weight: bold;"
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

    # Separator size constant
    SEPARATOR_HEIGHT = 120

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

        self.logger.debug(f"{self.OVERLAY_ID} | Weather forecast widget initialized")

    # ----------------------------------------------------------------------
    # Properties for scaled sizes

    @property
    def separator_height(self) -> int:
        return int(self.SEPARATOR_HEIGHT * self.scale_factor)

    # ----------------------------------------------------------------------

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
                separator.setFixedHeight(self.separator_height)
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
