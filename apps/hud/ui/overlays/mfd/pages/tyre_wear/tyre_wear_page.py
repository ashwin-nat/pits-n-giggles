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

from apps.hud.common import get_ref_row
from apps.hud.ui.overlays.mfd.pages.base_page import BasePage
from lib.assets_loader import load_icon

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class TyreInfoPage(BasePage):
    """Modern tyre wear and prediction display for MFD."""

    KEY = "tyre_info"
    FONT_FACE_TEXT = "Formula1 Display"
    FONT_FACE_NUMBERS = "B612 Mono"
    FONT_SIZE = 13
    NUM_DECIMAL_PLACES = 2
    MED_WEAR = 50
    DANGER_WEAR = 75

    def __init__(self, parent: QWidget, logger: logging.Logger, scale_factor: float):
        """Initialise the tyre wear page.

        Args:
            parent (QWidget): Parent widget
            logger (logging.Logger): Logger
            scale_factor (float): Scale factor
        """
        self.scale_factor = scale_factor
        super().__init__(parent, logger, f"{super().KEY}.{self.KEY}", scale_factor, title="TYRE WEAR INFO")

        self._init_icons()
        self._build_ui()
        self.logger.info(f"{self.overlay_id} | Tyre info widget initialized")
        self._init_event_handlers()

    def _init_icons(self):
        """Load tyre icons."""
        icon_base_tyres = Path("assets") / "tyre-icons"
        self.tyre_icon_mappings = {
            "Soft": load_icon(icon_base_tyres / "soft_tyre.svg", self.logger.debug, self.logger.error),
            "Super Soft": load_icon(icon_base_tyres / "super_soft_tyre.svg", self.logger.debug, self.logger.error),
            "Medium": load_icon(icon_base_tyres / "medium_tyre.svg", self.logger.debug, self.logger.error),
            "Hard": load_icon(icon_base_tyres / "hard_tyre.svg", self.logger.debug, self.logger.error),
            "Inters": load_icon(icon_base_tyres / "intermediate_tyre.svg", self.logger.debug, self.logger.error),
            "Wet": load_icon(icon_base_tyres / "wet_tyre.svg", self.logger.debug, self.logger.error),
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
        self.telemetry_message.setFont(QFont(self.FONT_FACE_TEXT, self.FONT_SIZE))
        self.telemetry_message.setStyleSheet("color: #FF6B6B;")
        self.telemetry_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.telemetry_message.hide()
        main_layout.addWidget(self.telemetry_message)

        self.page_layout.addWidget(main_container)

    def _build_top_section(self, parent_layout: QVBoxLayout) -> None:
        """Build a split top section with current tyre info (left) and available tyres (right)."""
        top_widget = QWidget()
        top_widget.setStyleSheet("""
            QWidget {
                background: #1b1b1b;
                border-radius: 6px;
            }
        """)
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(8, 4, 8, 4)
        top_layout.setSpacing(10)

        # LEFT HALF: Current tyre info
        left_widget = QWidget()
        left_widget.setStyleSheet("background: transparent;")
        left_main_layout = QVBoxLayout(left_widget)
        left_main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_main_layout.setContentsMargins(0, 0, 0, 0)
        left_main_layout.setSpacing(4)

        # TOP ROW: Icon, Compound, Age
        top_row_widget = QWidget()
        top_row_widget.setStyleSheet("background: transparent;")
        top_row_layout = QHBoxLayout(top_row_widget)
        top_row_layout.setContentsMargins(0, 0, 0, 0)
        top_row_layout.setSpacing(8)
        top_row_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Tyre icon
        self.tyre_icon_label = QLabel()
        self.tyre_icon_label.setFixedSize(28, 28)
        self.tyre_icon_label.setScaledContents(True)
        top_row_layout.addWidget(self.tyre_icon_label)

        # Compound name
        self.compound_label = QLabel("—")
        self.compound_label.setFont(QFont(self.FONT_FACE_TEXT, 10, QFont.Weight.Bold))
        self.compound_label.setStyleSheet("color: #FFFFFF; background: transparent;")
        top_row_layout.addWidget(self.compound_label)

        # Divider
        divider = QLabel("•")
        divider.setFont(QFont(self.FONT_FACE_TEXT, self.FONT_SIZE - 1))
        divider.setStyleSheet("color: #444; background: transparent;")
        top_row_layout.addWidget(divider)

        # Age stat
        age_label = QLabel("Age:")
        age_label.setFont(QFont(self.FONT_FACE_TEXT, self.FONT_SIZE - 1))
        age_label.setStyleSheet("color: #888; background: transparent;")
        top_row_layout.addWidget(age_label)

        self.tyre_age_label = QLabel("—")
        self.tyre_age_label.setFont(QFont(self.FONT_FACE_TEXT, self.FONT_SIZE - 1, QFont.Weight.Bold))
        self.tyre_age_label.setStyleSheet("color: #00D4FF; background: transparent;")
        top_row_layout.addWidget(self.tyre_age_label)

        top_row_layout.addStretch()
        left_main_layout.addWidget(top_row_widget)

        # BOTTOM ROW: Wear rate
        bottom_row_widget = QWidget()
        bottom_row_widget.setStyleSheet("background: transparent;")
        bottom_row_layout = QHBoxLayout(bottom_row_widget)
        bottom_row_layout.setContentsMargins(0, 0, 0, 0)
        bottom_row_layout.setSpacing(8)
        bottom_row_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Wear rate stat
        wear_rate_label = QLabel("Rate:")
        wear_rate_label.setFont(QFont(self.FONT_FACE_TEXT, self.FONT_SIZE - 1))
        wear_rate_label.setStyleSheet("color: #888; background: transparent;")
        bottom_row_layout.addWidget(wear_rate_label)

        self.wear_rate_value = QLabel("—")
        self.wear_rate_value.setFont(QFont(self.FONT_FACE_TEXT, self.FONT_SIZE - 1, QFont.Weight.Bold))
        self.wear_rate_value.setStyleSheet("color: #00D4FF; background: transparent;")
        bottom_row_layout.addWidget(self.wear_rate_value)

        bottom_row_layout.addStretch()
        left_main_layout.addWidget(bottom_row_widget)

        top_layout.addWidget(left_widget, stretch=1)

        # Vertical divider
        v_divider = QFrame()
        v_divider.setFrameShape(QFrame.Shape.VLine)
        v_divider.setStyleSheet("background-color: #333333;")
        v_divider.setFixedWidth(1)
        top_layout.addWidget(v_divider)

        # RIGHT HALF: Available fresh tyres
        right_widget = QWidget()
        right_widget.setStyleSheet("background: transparent;")
        right_main_layout = QVBoxLayout(right_widget)
        right_main_layout.setContentsMargins(0, 0, 0, 0)
        right_main_layout.setSpacing(2)

        # Title for unused tyres
        unused_title = QLabel("Unused Tyres")
        unused_title.setFont(QFont(self.FONT_FACE_TEXT, self.FONT_SIZE - 2))
        unused_title.setStyleSheet("color: #888; background: transparent;")
        unused_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_main_layout.addWidget(unused_title)

        # Create tyre grid
        tyres_container = self._create_tyre_grid()
        right_main_layout.addWidget(tyres_container)

        top_layout.addWidget(right_widget, stretch=1)

        parent_layout.addWidget(top_widget)

    def _create_tyre_grid(self) -> QWidget:
        """Create a 2x3 grid of tyre icons with count labels.

        Returns:
            QWidget: Container widget with tyre grid.
        """
        # Container for tyre icons in 2x3 grid
        tyres_container = QWidget()
        tyres_container.setStyleSheet("background: transparent;")
        grid_layout = QVBoxLayout(tyres_container)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setSpacing(4)
        grid_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Store reference to count labels for each tyre compound
        self.tyre_count_labels: Dict[str, QLabel] = {}

        # Define tyre order for grid: top row (Soft, Medium, Hard), bottom row (Super Soft, Inters, Wet)
        tyre_rows = [
            ["Soft", "Medium", "Hard"],
            ["Super Soft", "Inters", "Wet"]
        ]

        # Create 2 rows
        for row_compounds in tyre_rows:
            row_widget = QWidget()
            row_widget.setStyleSheet("background: transparent;")
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(12)
            row_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

            for compound in row_compounds:
                # Create container for icon + count
                tyre_container = QWidget()
                tyre_container.setStyleSheet("background: transparent;")
                tyre_container_layout = QVBoxLayout(tyre_container)
                tyre_container_layout.setContentsMargins(0, 0, 0, 0)
                tyre_container_layout.setSpacing(0)
                tyre_container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

                # Icon and count in horizontal layout
                icon_count_widget = QWidget()
                icon_count_widget.setStyleSheet("background: transparent;")
                icon_count_layout = QHBoxLayout(icon_count_widget)
                icon_count_layout.setContentsMargins(0, 0, 0, 0)
                icon_count_layout.setSpacing(0)
                icon_count_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

                # Icon
                icon_label = QLabel()
                icon_label.setFixedSize(24, 24)
                icon_label.setScaledContents(True)
                icon = self.tyre_icon_mappings.get(compound)
                if icon and not icon.isNull():
                    pixmap = icon.pixmap(24, 24)
                    icon_label.setPixmap(pixmap)
                icon_count_layout.addWidget(icon_label)

                # Count label (bottom right of icon)
                count_label = QLabel("x0")
                count_label.setFont(QFont(self.FONT_FACE_TEXT, 9, QFont.Weight.Bold))
                count_label.setStyleSheet("color: #666; background: transparent; padding-left: 2px;")
                count_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)
                icon_count_layout.addWidget(count_label)

                # Store reference to count label
                self.tyre_count_labels[compound] = count_label

                tyre_container_layout.addWidget(icon_count_widget)
                row_layout.addWidget(tyre_container)

            grid_layout.addWidget(row_widget)

        return tyres_container

    def _create_stat_divider(self) -> QLabel:
        """Create a vertical divider for stats."""
        divider = QLabel("•")
        divider.setFont(QFont(self.FONT_FACE_TEXT, self.FONT_SIZE))
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
        self.wear_table.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        # Style the table
        self.wear_table.setFont(QFont(self.FONT_FACE_TEXT, self.FONT_SIZE))
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

    def _init_event_handlers(self):
        """Initialise event handlers."""
        @self.on_event("race_table_update")
        def _handle_race_table_update(data: Dict[str, Any]) -> None:
            """Update tyre wear information display."""
            ref_row = get_ref_row(data)
            if not ref_row:
                return

            tyre_info = ref_row["tyre-info"]
            curr_wear = tyre_info["current-wear"]
            tyre_age = tyre_info["tyre-age"]
            visual_tyre_comp = tyre_info["visual-tyre-compound"]
            actual_tyre_comp = tyre_info["actual-tyre-compound"]

            telemetry_settings = ref_row["driver-info"]["telemetry-setting"]

            # Update compound display
            self._update_compound_display(visual_tyre_comp, actual_tyre_comp)

            # Update stats
            self.tyre_age_label.setText(f"{tyre_age}L")

            # Calculate and display wear rate
            tyre_wear_rates: Dict[str, Any] = tyre_info.get('wear-prediction', {}).get('rate', {})
            if tyre_wear_rates:
                avg_rate = sum(tyre_wear_rates.values()) / len(tyre_wear_rates.values())
                self.wear_rate_value.setText(f"{avg_rate:.{self.NUM_DECIMAL_PLACES}f}%/L")
            else:
                self.wear_rate_value.setText("—")

            if telemetry_settings != "Public":
                self._show_telemetry_disabled()
                return
            self._hide_telemetry_disabled()

            # Update wear table
            curr_lap_num = ref_row["lap-info"]["current-lap"]
            wear_prediction = tyre_info["wear-prediction"]
            predictions = None
            pit_lap = None
            tyre_wear_rates: Dict[str, Any] = wear_prediction['rate']
            avg_rate = sum(tyre_wear_rates.values()) / len(tyre_wear_rates.values())

            if self._is_wear_prediction_supported(data):
                pit_lap = wear_prediction["selected-pit-stop-lap"]
                predictions = wear_prediction["predictions"]

            self._update_wear_table(curr_wear, curr_lap_num, predictions, pit_lap)

        @self.on_event("stream_overlay_update")
        def _handle_stream_overlay_update(data: Dict[str, Any]) -> None:
            """Update tyre wear information display."""
            tyre_sets_info = data["tyre-sets"]
            if not tyre_sets_info:
                return

            fresh_avlb_tyre_sets = [
                tyre_set
                for tyre_set in tyre_sets_info["tyre-set-data"]
                if tyre_set["available"] and not tyre_set["fitted"] and tyre_set['wear'] == 0
            ]
            groupings_by_comp = self._get_tyres_grouping_by_vis_comp(fresh_avlb_tyre_sets)
            self._update_available_tyres_display(groupings_by_comp)

    def _get_tyres_grouping_by_vis_comp(self, tyre_sets: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Group tyre sets by visual tyre compound.

        Args:
            tyre_sets (List[Dict[str, Any]]): List of tyre sets.

        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of tyre set count grouped by visual tyre compound.
        """
        groupings_by_comp = {}
        for ts in tyre_sets:
            vis = ts['visual-tyre-compound']
            act = ts['actual-tyre-compound']

            stats = groupings_by_comp.setdefault(
                vis, {'actual-tyre-compound': act, 'count': 0}
            )
            stats['count'] += 1
        return groupings_by_comp

    def _update_available_tyres_display(self, groupings_by_comp: Dict[str, Dict[str, Any]]) -> None:
        """Update the right side of top section with available fresh tyres.

        Args:
            groupings_by_comp (Dict[str, Dict[str, Any]]): Dictionary of tyre counts by visual compound.
        """
        # Reset all counts to 0 first
        for label in self.tyre_count_labels.values():
            label.setText("x0")
            label.setStyleSheet("color: #666; background: transparent; padding-left: 2px;")

        # Update counts for available tyres
        for visual_compound, stats in groupings_by_comp.items():
            count = stats['count']
            if visual_compound in self.tyre_count_labels:
                label = self.tyre_count_labels[visual_compound]
                label.setText(f"x{count}")
                # Highlight available tyres
                label.setStyleSheet("color: #00D4FF; background: transparent; padding-left: 2px;")

    def _update_compound_display(self, visual_compound: str, actual_compound: str) -> None:
        """Update the tyre compound icon and label."""
        icon = self.tyre_icon_mappings.get(visual_compound)
        if icon and not icon.isNull():
            pixmap = icon.pixmap(28, 28)
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
            label_item.setFont(QFont(self.FONT_FACE_TEXT, self.FONT_SIZE - 1, QFont.Weight.Bold))
            label_item.setForeground(Qt.GlobalColor.white)
            label_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.wear_table.setItem(row_idx, 0, label_item)

            # Wear values
            for col_idx, tyre in enumerate(['fl', 'fr', 'rl', 'rr'], start=1):
                value = row_data[tyre]
                item = QTableWidgetItem(f"{value:.{self.NUM_DECIMAL_PLACES}f}%")
                item.setFont(QFont(self.FONT_FACE_TEXT, self.FONT_SIZE - 1))
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

