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
from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QFontMetrics
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QHeaderView, QLabel, QSizePolicy,
                               QTableWidget, QTableWidgetItem, QVBoxLayout,
                               QWidget)

from apps.hud.common import get_ref_row
from apps.hud.ui.overlays.mfd.pages.base_page import BasePage
from lib.assets_loader import load_tyre_icons_dict

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class TyreInfoPage(BasePage):
    """Modern tyre wear and prediction display for MFD."""

    KEY = "tyre_info"
    FONT_FACE_TEXT = "Formula1"
    FONT_FACE_NUMBERS = "B612 Mono"
    FONT_SIZE = 13
    FONT_SIZE_HYPHEN = 10
    FONT_SIZE_MISC = FONT_SIZE - 1
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
        self.logger.debug(f"{self.OVERLAY_ID} | Tyre info widget initialized")
        self._init_event_handlers()

    def _init_font_metrics(self):
        """Initialize font metrics for text measurement."""
        # Main text font
        self.text_font = QFont(self.FONT_FACE_TEXT, self.font_size)
        self.text_font_metrics = QFontMetrics(self.text_font)

        # Bold text font
        self.text_font_bold = QFont(self.FONT_FACE_TEXT, self.font_size, QFont.Weight.Bold)
        self.text_font_bold_metrics = QFontMetrics(self.text_font_bold)

        # Misc font
        self.misc_font = QFont(self.FONT_FACE_TEXT, self.font_size_misc)
        self.misc_font_metrics = QFontMetrics(self.misc_font)

        # Misc bold font
        self.misc_font_bold = QFont(self.FONT_FACE_TEXT, self.font_size_misc, QFont.Weight.Bold)
        self.misc_font_bold_metrics = QFontMetrics(self.misc_font_bold)

        # Small font for tyre counts
        self.small_font = QFont(self.FONT_FACE_TEXT, max(7, int(9 * self.scale_factor)), QFont.Weight.Bold)
        self.small_font_metrics = QFontMetrics(self.small_font)

        # Title font (smaller)
        self.title_font = QFont(self.FONT_FACE_TEXT, max(8, self.font_size_misc - 2))
        self.title_font_metrics = QFontMetrics(self.title_font)

    def _init_icons(self):
        """Load tyre icons."""
        self.tyre_icon_mappings = load_tyre_icons_dict(
            debug_log_printer=self.logger.debug, error_log_printer=self.logger.error)
        for name, icon in self.tyre_icon_mappings.items():
            if icon.isNull():
                self.logger.warning(f"{self.OVERLAY_ID} | Failed to load tyre icon: {name}")
            else:
                self.logger.debug(f"{self.OVERLAY_ID} | Loaded tyre icon successfully: {name}")

    def _build_ui(self) -> None:
        """Build the complete UI structure."""
        self._init_font_metrics()
        main_container = QWidget(self)
        main_layout = QVBoxLayout(main_container)
        main_layout.setSpacing(self.scaled_spacing_medium)
        main_layout.setContentsMargins(
            self.scaled_spacing_large,
            self.scaled_spacing_tiny,
            self.scaled_spacing_large,
            self.scaled_spacing_large
        )

        # Top section: Compound info and stats
        self._build_top_section(main_layout)

        # Separator
        self._add_separator(main_layout)

        # Bottom section: Wear table
        self._build_wear_table(main_layout)

        # Telemetry disabled message (hidden by default)
        self.telemetry_message = QLabel("Telemetry disabled - Wear data unavailable")
        self.telemetry_message.setFont(self.text_font)
        self.telemetry_message.setStyleSheet("color: #FF6B6B;")
        self.telemetry_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.telemetry_message.hide()
        main_layout.addWidget(self.telemetry_message)

        self.page_layout.addWidget(main_container)

    def _build_top_section(self, parent_layout: QVBoxLayout) -> None:
        """Build a split top section with current tyre info (left) and available tyres (right)."""
        top_widget = QWidget()
        top_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        top_widget.setStyleSheet(f"""
            QWidget {{
                background: #1b1b1b;
                border-radius: {self.scaled_border_radius}px;
            }}
        """)
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(
            self.scaled_spacing_medium,
            self.scaled_spacing_tiny,
            self.scaled_spacing_medium,
            self.scaled_spacing_tiny
        )
        top_layout.setSpacing(self.scaled_spacing_large)

        # LEFT HALF: Current tyre info
        left_widget = self._create_current_tyre_section()
        top_layout.addWidget(left_widget, stretch=1)

        # Vertical divider
        v_divider = QFrame()
        v_divider.setFrameShape(QFrame.Shape.VLine)
        v_divider.setStyleSheet("background-color: #333333;")
        v_divider.setFixedWidth(1)
        top_layout.addWidget(v_divider)

        # RIGHT HALF: Available fresh tyres
        right_widget = self._create_available_tyres_section()
        top_layout.addWidget(right_widget, stretch=1)

        parent_layout.addWidget(top_widget)

    def _create_current_tyre_section(self) -> QWidget:
        """Create the left section showing current tyre information."""
        left_widget = QWidget()
        left_widget.setStyleSheet("background: transparent;")
        left_main_layout = QVBoxLayout(left_widget)
        left_main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_main_layout.setContentsMargins(0, 0, 0, 0)
        left_main_layout.setSpacing(self.scaled_spacing_tiny)

        # TOP ROW: Icon, Compound, Age
        top_row_widget = self._create_top_info_row()
        left_main_layout.addWidget(top_row_widget)

        # BOTTOM ROW: Wear rate
        bottom_row_widget = self._create_wear_rate_row()
        left_main_layout.addWidget(bottom_row_widget)

        return left_widget

    def _create_top_info_row(self) -> QWidget:
        """Create the top row with tyre icon, compound name, and age."""
        top_row_widget = QWidget()
        top_row_widget.setStyleSheet("background: transparent;")
        top_row_layout = QHBoxLayout(top_row_widget)
        top_row_layout.setContentsMargins(0, 0, 0, 0)
        top_row_layout.setSpacing(self.scaled_spacing_small)
        top_row_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Tyre icon
        self.tyre_icon_label = QLabel()
        self.tyre_icon_label.setFixedSize(
            self.scaled_icon_size_large,
            self.scaled_icon_size_large
        )
        self.tyre_icon_label.setScaledContents(True)
        top_row_layout.addWidget(self.tyre_icon_label)

        # Compound name
        self.compound_label = QLabel("—")
        self.compound_label.setFont(self.text_font_bold)
        self.compound_label.setStyleSheet("color: #FFFFFF; background: transparent;")
        top_row_layout.addWidget(self.compound_label)

        # Divider
        divider = QLabel("•")
        divider.setFont(self.misc_font)
        divider.setStyleSheet("color: #444; background: transparent;")
        top_row_layout.addWidget(divider)

        # Age stat
        self.tyre_age_label = self._create_stat_pair(
            top_row_layout, "Age:", "#888", "#00D4FF"
        )

        top_row_layout.addStretch()
        return top_row_widget

    def _create_wear_rate_row(self) -> QWidget:
        """Create the bottom row with wear rate information."""
        bottom_row_widget = QWidget()
        bottom_row_widget.setStyleSheet("background: transparent;")
        bottom_row_layout = QHBoxLayout(bottom_row_widget)
        bottom_row_layout.setContentsMargins(0, 0, 0, 0)
        bottom_row_layout.setSpacing(self.scaled_spacing_small)
        bottom_row_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Wear rate stat
        self.wear_rate_value = self._create_stat_pair(
            bottom_row_layout, "Rate:", "#888", "#00D4FF"
        )

        bottom_row_layout.addStretch()
        return bottom_row_widget

    def _create_stat_pair(
        self,
        layout: QHBoxLayout,
        label_text: str,
        label_color: str,
        value_color: str
    ) -> QLabel:
        """Create a label-value pair for displaying stats.

        Args:
            layout: The layout to add widgets to
            label_text: Text for the label (e.g., "Age:")
            label_color: Color for the label text
            value_color: Color for the value text

        Returns:
            The value QLabel for later updates
        """
        label = QLabel(label_text)
        label.setFont(self.misc_font)
        label.setStyleSheet(f"color: {label_color}; background: transparent;")
        layout.addWidget(label)

        value_label = QLabel("—")
        value_label.setFont(self.misc_font_bold)
        value_label.setStyleSheet(f"color: {value_color}; background: transparent;")
        layout.addWidget(value_label)

        return value_label

    def _create_available_tyres_section(self) -> QWidget:
        """Create the right section showing available fresh tyres."""
        right_widget = QWidget()
        right_widget.setStyleSheet("background: transparent;")
        right_main_layout = QVBoxLayout(right_widget)
        right_main_layout.setContentsMargins(0, 0, 0, 0)
        right_main_layout.setSpacing(0)

        # Title for unused tyres
        unused_title = QLabel("Unused Tyres")
        unused_title.setFont(self.title_font)
        unused_title.setStyleSheet("color: #888; background: transparent;")
        unused_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Calculate title height based on font metrics
        title_height = self.title_font_metrics.height()
        unused_title.setMaximumHeight(title_height + self.scaled_spacing_tiny)

        right_main_layout.addWidget(unused_title)
        right_main_layout.addSpacing(self.scaled_spacing_tiny)

        # Create tyre grid
        right_main_layout.addWidget(self._create_tyre_grid())

        return right_widget

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
        grid_layout.setSpacing(self.scaled_spacing_tiny)
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
            row_layout.setSpacing(self.scaled_spacing_small)
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
                icon_label.setFixedSize(
                    self.scaled_icon_size_small,
                    self.scaled_icon_size_small
                )
                icon_label.setScaledContents(True)
                icon = self.tyre_icon_mappings.get(compound)
                if icon and not icon.isNull():
                    pixmap = icon.pixmap(
                        self.scaled_icon_size_small,
                        self.scaled_icon_size_small
                    )
                    icon_label.setPixmap(pixmap)
                icon_count_layout.addWidget(icon_label)

                # Count label (bottom right of icon)
                count_label = QLabel("x0")
                count_label.setFont(self.small_font)
                count_label.setStyleSheet(
                    f"color: #666; background: transparent; "
                    f"padding-left: {max(1, self.scaled_spacing_tiny // 2)}px;"
                )
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
        divider.setFont(self.text_font)
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

        # Style the table with scaled padding
        padding = max(2, self.scaled_spacing_small)
        self.wear_table.setFont(self.misc_font)
        self.wear_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: #1a1a1a;
                border: 1px solid #333;
                gridline-color: #333;
                color: #FFFFFF;
            }}
            QTableWidget::item {{
                padding: {padding}px;
            }}
            QTableWidget::item:hover {{
                background-color: #1a1a1a;
            }}
            QHeaderView::section {{
                background-color: #2a2a2a;
                color: #00D4FF;
                padding: {padding}px;
                border: 1px solid #333;
                font-weight: bold;
            }}
            QHeaderView::section:hover {{
                background-color: #2a2a2a;
            }}
        """)

        # Configure headers
        self.wear_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.wear_table.horizontalHeader().setMinimumSectionSize(int(30 * self.scale_factor))
        self.wear_table.verticalHeader().setVisible(False)
        self.wear_table.setShowGrid(True)

        # Calculate proper table height based on font metrics and expected rows
        header_height = self.misc_font_metrics.height() + (padding * 2) + 2
        row_height = self.misc_font_metrics.height() + (padding * 2)
        self.wear_table.setRowCount(3) # Pre-construct 3 rows
        max_rows = 3

        min_height = header_height + (row_height * max_rows) + 6

        self.wear_table.setMinimumHeight(min_height)
        self.wear_table.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Expanding
        )

        parent_layout.addWidget(self.wear_table)

        # Add small margin below table
        parent_layout.addSpacing(self.scaled_spacing_medium)

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
            label.setStyleSheet(f"color: #666; background: transparent; "
                                f"padding-left: {max(1, self.scaled_spacing_tiny // 2)}px;")

        # Update counts for available tyres
        for visual_compound, stats in groupings_by_comp.items():
            count = stats['count']
            if visual_compound in self.tyre_count_labels:
                label = self.tyre_count_labels[visual_compound]
                label.setText(f"x{count}")
                # Highlight available tyres
                label.setStyleSheet(f"color: #00D4FF; background: transparent; "
                                    f"padding-left: {max(1, self.scaled_spacing_tiny // 2)}px;")

    def _update_compound_display(self, visual_compound: str, actual_compound: str) -> None:
        """Update the tyre compound icon and label."""
        icon = self.tyre_icon_mappings.get(visual_compound)
        if icon and not icon.isNull():
            pixmap = icon.pixmap(
                self.scaled_icon_size_large,
                self.scaled_icon_size_large
            )
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
            end_lap = predictions[-1]["lap-number"]

            if pit_lap:
                lap_sequence = [curr_lap, pit_lap, end_lap]
            else:
                mid_lap = curr_lap + (end_lap - curr_lap) // 2
                lap_sequence = [curr_lap, mid_lap, end_lap]

            # Skip curr lap (already added)
            for lap in lap_sequence[1:]:
                pred = self._find_closest_prediction(predictions, lap)
                if not pred:
                    continue

                label = f"{pred['lap-number']}"
                if pit_lap and lap == pit_lap:
                    label += " (Pit)"

                rows_data.append({
                    'label': label,
                    'fl': pred.get('front-left-wear', 0.0),
                    'fr': pred.get('front-right-wear', 0.0),
                    'rl': pred.get('rear-left-wear', 0.0),
                    'rr': pred.get('rear-right-wear', 0.0),
                })

        # Update table
        # Always populate the first 3 rows and clear any excess
        for row_idx in range(3): # Iterate for the 3 pre-constructed rows
            if row_idx < len(rows_data):
                row_data = rows_data[row_idx]
                # Label column
                label_item = QTableWidgetItem(row_data['label'])
                label_item.setFont(self.misc_font_bold)
                label_item.setForeground(Qt.GlobalColor.white)
                label_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.wear_table.setItem(row_idx, 0, label_item)

                # Wear values
                for col_idx, tyre in enumerate(['fl', 'fr', 'rl', 'rr'], start=1):
                    value = row_data[tyre]
                    item = QTableWidgetItem(f"{value:.{self.NUM_DECIMAL_PLACES}f}%")
                    item.setFont(self.misc_font)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                    # Color code based on wear level
                    if value < self.MED_WEAR:
                        item.setForeground(Qt.GlobalColor.green)
                    elif value < self.DANGER_WEAR:
                        item.setForeground(Qt.GlobalColor.yellow)
                    else:
                        item.setForeground(Qt.GlobalColor.red)

                    self.wear_table.setItem(row_idx, col_idx, item)
            else:
                # Clear excess rows
                for col_idx in range(self.wear_table.columnCount()):
                    self.wear_table.setItem(row_idx, col_idx, QTableWidgetItem(""))

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

    @property
    def font_size(self) -> int:
        """Get the font size based on the scale factor."""
        return max(9, int(self.FONT_SIZE * self.scale_factor))

    @property
    def font_size_misc(self) -> int:
        """Get the misc font size based on the scale factor."""
        return max(8, int(self.FONT_SIZE_MISC * self.scale_factor))

    @property
    def font_size_hyphen(self) -> int:
        """Get the hyphen font size based on the scale factor."""
        return max(8, int(self.FONT_SIZE_HYPHEN * self.scale_factor))

    @property
    def scaled_icon_size_large(self) -> int:
        """Get scaled large icon size (28px base)."""
        return max(20, int(28 * self.scale_factor))

    @property
    def scaled_icon_size_small(self) -> int:
        """Get scaled small icon size (24px base)."""
        return max(16, int(24 * self.scale_factor))

    @property
    def scaled_spacing_large(self) -> int:
        """Get scaled large spacing (10px base)."""
        return max(6, int(10 * self.scale_factor))

    @property
    def scaled_spacing_medium(self) -> int:
        """Get scaled medium spacing (6px base)."""
        return max(4, int(6 * self.scale_factor))

    @property
    def scaled_spacing_small(self) -> int:
        """Get scaled small spacing (4px base)."""
        return max(2, int(4 * self.scale_factor))

    @property
    def scaled_spacing_tiny(self) -> int:
        """Get scaled tiny spacing (2px base)."""
        return max(1, int(2 * self.scale_factor))

    @property
    def scaled_table_height(self) -> int:
        """Get scaled table max height based on font metrics."""
        # This is now calculated dynamically in _build_wear_table
        return max(80, int(140 * self.scale_factor))

    @property
    def scaled_border_radius(self) -> int:
        """Get scaled border radius (6px base)."""
        return max(3, int(6 * self.scale_factor))
