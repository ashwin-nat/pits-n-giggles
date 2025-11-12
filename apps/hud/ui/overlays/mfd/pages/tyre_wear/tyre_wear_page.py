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
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QHeaderView, QLabel,
                               QTableWidget, QTableWidgetItem, QVBoxLayout,
                               QWidget)

from apps.hud.ui.overlays.mfd.pages.base_page import BasePage

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class TyreWearPage(BasePage):
    """Modern tyre wear and prediction display for MFD."""

    FONT_FACE = "Montserrat"
    FONT_SIZE = 9
    NUM_DECIMAL_PLACES = 2
    MED_WEAR = 50
    DANGER_WEAR = 75

    def __init__(self, parent: QWidget, logger: logging.Logger):
        super().__init__(parent, logger, "mfd.tyre_info", title="TYRE WEAR INFO")

        self._init_icons()
        self._build_ui()
        self.logger.info(f"{self.overlay_id} | Tyre info widget initialized")

    def _init_icons(self):
        icon_base_tyres = Path("assets") / "tyre-icons"
        self.tyre_icon_mappings = {
            "Soft": self.load_icon(str(icon_base_tyres / "soft_tyre.svg")),
            "Super Soft": self.load_icon(str(icon_base_tyres / "super_soft_tyre.svg")),
            "Medium": self.load_icon(str(icon_base_tyres / "medium_tyre.svg")),
            "Hard": self.load_icon(str(icon_base_tyres / "hard_tyre.svg")),
            "Inters": self.load_icon(str(icon_base_tyres / "intermediate_tyre.svg")),
            "Wet": self.load_icon(str(icon_base_tyres / "wet_tyre.svg")),
        }
        for name, icon in self.tyre_icon_mappings.items():
            if icon.isNull():
                self.logger.warning(f"{self.overlay_id} | Failed to load tyre icon: {name}")
            else:
                self.logger.debug(f"{self.overlay_id} | Loaded tyre icon successfully: {name}")

    def _build_ui(self) -> None:
        """Build the complete UI structure."""
        main_container = QWidget(self)
        main_layout = QVBoxLayout(main_container)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(10, 5, 10, 10)

        # Top section: Compound info and stats
        self._build_top_section(main_layout)

        # Separator
        self._add_separator(main_layout)

        # Bottom section: Wear table
        self._build_wear_table(main_layout)

        # Telemetry disabled message (hidden by default)
        self.telemetry_message = QLabel("Telemetry disabled - Wear data unavailable")
        self.telemetry_message.setFont(QFont(self.FONT_FACE, self.FONT_SIZE))
        self.telemetry_message.setStyleSheet("color: #FF6B6B;")
        self.telemetry_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.telemetry_message.hide()
        main_layout.addWidget(self.telemetry_message)

        self.page_layout.addWidget(main_container)

    def _build_top_section(self, parent_layout: QVBoxLayout) -> None:
        """Build the top section with compound and stats."""
        top_widget = QWidget()
        top_widget.setStyleSheet("""
            QWidget {
                background-color: #242424;
                border-radius: 4px;
            }
        """)
        top_layout = QHBoxLayout(top_widget)
        top_layout.setSpacing(15)
        top_layout.setContentsMargins(8, 6, 8, 6)

        # Left: Tyre icon and compound
        left_widget = QWidget()
        left_widget.setStyleSheet("background: transparent;")
        left_layout = QHBoxLayout(left_widget)
        left_layout.setSpacing(10)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.tyre_icon_label = QLabel()
        self.tyre_icon_label.setFixedSize(36, 36)
        self.tyre_icon_label.setScaledContents(True)
        left_layout.addWidget(self.tyre_icon_label)

        self.compound_label = QLabel("Medium")
        self.compound_label.setFont(QFont(self.FONT_FACE, 11, QFont.Weight.Bold))
        self.compound_label.setStyleSheet("color: #FFFFFF; background: transparent;")
        left_layout.addWidget(self.compound_label)

        top_layout.addWidget(left_widget)
        top_layout.addStretch()

        # Right: Stats (horizontal layout for sleeker look)
        right_widget = QWidget()
        right_widget.setStyleSheet("background: transparent;")
        right_layout = QHBoxLayout(right_widget)
        right_layout.setSpacing(15)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.age_label = self._create_compact_stat("Age:", "0")
        self.pitstops_label = self._create_compact_stat("Stops:", "0")

        right_layout.addWidget(self.age_label)
        right_layout.addWidget(self._create_stat_divider())
        right_layout.addWidget(self.pitstops_label)

        top_layout.addWidget(right_widget)

        parent_layout.addWidget(top_widget)

    def _create_compact_stat(self, title: str, value: str) -> QWidget:
        """Create a compact stat display."""
        widget = QWidget()
        widget.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        title_label = QLabel(title)
        title_label.setFont(QFont(self.FONT_FACE, self.FONT_SIZE))
        title_label.setStyleSheet("color: #888888; background: transparent;")
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setFont(QFont(self.FONT_FACE, self.FONT_SIZE, QFont.Weight.Bold))
        value_label.setStyleSheet("color: #00D4FF; background: transparent;")
        layout.addWidget(value_label)

        setattr(widget, 'value_label', value_label)
        return widget

    def _create_stat_divider(self) -> QLabel:
        """Create a vertical divider for stats."""
        divider = QLabel("•")
        divider.setFont(QFont(self.FONT_FACE, self.FONT_SIZE))
        divider.setStyleSheet("color: #444444; background: transparent;")
        return divider

    def _build_wear_table(self, parent_layout: QVBoxLayout) -> None:
        """Build the wear data table."""
        self.wear_table = QTableWidget()
        self.wear_table.setColumnCount(5)
        self.wear_table.setHorizontalHeaderLabels(["Lap", "FL", "FR", "RL", "RR"])

        # Disable interaction and scrolling
        self.wear_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.wear_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.wear_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.wear_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.wear_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Style the table
        self.wear_table.setFont(QFont(self.FONT_FACE, self.FONT_SIZE))
        self.wear_table.setStyleSheet("""
            QTableWidget {
                background-color: #1a1a1a;
                border: 1px solid #333;
                gridline-color: #333;
                color: #FFFFFF;
            }
            QTableWidget::item {
                padding: 3px;
            }
            QTableWidget::item:hover {
                background-color: #1a1a1a;
            }
            QHeaderView::section {
                background-color: #2a2a2a;
                color: #00D4FF;
                padding: 4px;
                border: 1px solid #333;
                font-weight: bold;
            }
            QHeaderView::section:hover {
                background-color: #2a2a2a;
            }
        """)

        # Configure headers
        self.wear_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.wear_table.horizontalHeader().setMinimumSectionSize(40)
        self.wear_table.verticalHeader().setVisible(False)
        self.wear_table.setShowGrid(True)

        # Set fixed height for compact display
        self.wear_table.setMaximumHeight(120)

        parent_layout.addWidget(self.wear_table)

    def _add_separator(self, parent_layout: QVBoxLayout) -> None:
        """Add a horizontal separator line."""
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #333333;")
        separator.setFixedHeight(1)
        parent_layout.addWidget(separator)

    def update(self, data: Dict[str, Any]) -> None:
        """Update tyre wear information display."""
        ref_row = self._get_ref_row(data)
        if not ref_row:
            return

        tyre_info = ref_row["tyre-info"]
        curr_wear = tyre_info["current-wear"]
        num_pit_stops = tyre_info["num-pitstops"]
        tyre_age = tyre_info["tyre-age"]
        visual_tyre_comp = tyre_info["visual-tyre-compound"]
        actual_tyre_comp = tyre_info["actual-tyre-compound"]

        telemetry_settings = ref_row["driver-info"]["telemetry-setting"]

        # Update compound display
        self._update_compound_display(visual_tyre_comp, actual_tyre_comp)

        # Update stats
        self.age_label.value_label.setText(f"{tyre_age}L")
        self.pitstops_label.value_label.setText(str(num_pit_stops))

        if telemetry_settings != "Public":
            self._show_telemetry_disabled()
            return
        self._hide_telemetry_disabled()

        # Update wear table
        curr_lap_num = ref_row["lap-info"]["current-lap"]
        predictions = None
        pit_lap = None

        if self._is_wear_prediction_supported(data):
            wear_prediction = tyre_info["wear-prediction"]
            pit_lap = wear_prediction["selected-pit-stop-lap"]
            predictions = wear_prediction["predictions"]

        self._update_wear_table(curr_wear, curr_lap_num, predictions, pit_lap)

    def _update_compound_display(self, visual_compound: str, actual_compound: str) -> None:
        """Update the tyre compound icon and label."""
        icon = self.tyre_icon_mappings.get(visual_compound)
        if icon and not icon.isNull():
            pixmap = icon.pixmap(32, 32)
            self.tyre_icon_label.setPixmap(pixmap)
        else:
            self.tyre_icon_label.clear()

        self.compound_label.setText(actual_compound)

    def _update_wear_table(self, curr_wear: Dict[str, float], curr_lap: int,
                          predictions: Optional[List[Dict]], pit_lap: Optional[int]) -> None:
        """Update the wear table with current and predicted values."""
        rows_data = [{
            'label': 'curr',
            'fl': curr_wear.get('front-left-wear', 0.0),
            'fr': curr_wear.get('front-right-wear', 0.0),
            'rl': curr_wear.get('rear-left-wear', 0.0),
            'rr': curr_wear.get('rear-right-wear', 0.0),
        }]

        # Add predictions if available
        if predictions and len(predictions) > 0:
            end_lap = pit_lap or predictions[-1]["lap-number"]
            mid_lap = curr_lap + (end_lap - curr_lap) // 2

            pred_mid = self._find_closest_prediction(predictions, mid_lap)
            pred_end = self._find_closest_prediction(predictions, end_lap)

            # Only add mid prediction if it's different from end
            if pred_mid and pred_end and pred_mid["lap-number"] != pred_end["lap-number"]:
                rows_data.append({
                    'label': f'{pred_mid["lap-number"]}',
                    'fl': pred_mid.get('front-left-wear', 0.0),
                    'fr': pred_mid.get('front-right-wear', 0.0),
                    'rl': pred_mid.get('rear-left-wear', 0.0),
                    'rr': pred_mid.get('rear-right-wear', 0.0),
                })

            if pred_end:
                label_suffix = " (Pit)" if pit_lap else ""
                rows_data.append({
                    'label': f'{pred_end["lap-number"]}{label_suffix}',
                    'fl': pred_end.get('front-left-wear', 0.0),
                    'fr': pred_end.get('front-right-wear', 0.0),
                    'rl': pred_end.get('rear-left-wear', 0.0),
                    'rr': pred_end.get('rear-right-wear', 0.0),
                })

        # Update table
        self.wear_table.setRowCount(len(rows_data))

        for row_idx, row_data in enumerate(rows_data):
            # Label column
            label_item = QTableWidgetItem(row_data['label'])
            label_item.setFont(QFont(self.FONT_FACE, self.FONT_SIZE - 1, QFont.Weight.Bold))
            label_item.setForeground(Qt.GlobalColor.white)
            self.wear_table.setItem(row_idx, 0, label_item)

            # Wear values
            for col_idx, tyre in enumerate(['fl', 'fr', 'rl', 'rr'], start=1):
                value = row_data[tyre]
                item = QTableWidgetItem(f"{value:.{self.NUM_DECIMAL_PLACES}f}%")
                item.setFont(QFont(self.FONT_FACE, self.FONT_SIZE - 1))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                # Color code based on wear level
                if value < self.MED_WEAR:
                    item.setForeground(Qt.GlobalColor.green)
                elif value < self.DANGER_WEAR:
                    item.setForeground(Qt.GlobalColor.yellow)
                else:
                    item.setForeground(Qt.GlobalColor.red)

                self.wear_table.setItem(row_idx, col_idx, item)

    def _find_closest_prediction(self, predictions: List[Dict], target_lap: int) -> Optional[Dict]:
        """Find the prediction closest to the target lap."""
        if not predictions:
            return None
        return min(predictions, key=lambda p: abs(p["lap-number"] - target_lap))

    def _show_telemetry_disabled(self) -> None:
        """Show telemetry disabled message and hide wear data."""
        self.telemetry_message.show()
        self.wear_table.hide()

    def _hide_telemetry_disabled(self) -> None:
        """Hide telemetry disabled message and show wear data."""
        self.telemetry_message.hide()
        self.wear_table.show()

    def _is_wear_prediction_supported(self, data: Dict[str, Any]) -> bool:
        """Check if wear prediction is supported for this event."""
        event_type: str = data.get("event-type", "")
        return event_type and "Race" in event_type
