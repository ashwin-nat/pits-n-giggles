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
from PySide6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel,
                               QVBoxLayout, QWidget)
from PySide6.QtGui import QFont, QPixmap

from lib.assets_loader import load_tyre_icons_dict
from apps.hud.ui.overlays.mfd.pages.base_page import BasePage

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class TyreDeltaPage(BasePage):
    """Tyre Delta page showing tyre set predictions and compound mappings."""

    KEY = "tyre_delta"

    FONT_FACE = "Formula1 Display"
    MONO_FONT_FACE = "B612 Mono"
    FONT_SIZE_VALUE = 16
    FONT_SIZE_UNIT = 9
    FONT_SIZE_LABEL = 8
    FONT_SIZE_COMPOUND = 10

    ICON_SIZE = 40

    # Color scheme (matching fuel_page style)
    COLOR_BG = "#1a1a1a"
    COLOR_PRIMARY = "#00ff88"
    COLOR_WARNING = "#ffaa00"
    COLOR_DANGER = "#ff4444"
    COLOR_TEXT = "#e0e0e0"
    COLOR_TEXT_DIM = "#808080"
    COLOR_BORDER = "#333333"

    # Tyre compounds that may be present
    ALL_COMPOUNDS = ["Super Soft", "Soft", "Medium", "Hard", "Inters", "Wet"]
    SLICK_COMPOUNDS = ["Super Soft", "Soft", "Medium", "Hard"]

    def __init__(self, parent: QWidget, logger: logging.Logger, scale_factor: float):
        """Initialise the tyre delta prediction page.

        Args:
            parent (QWidget): Parent widget
            logger (logging.Logger): Logger
            scale_factor (float): Scale factor
        """
        super().__init__(parent, logger, f"{super().KEY}.{self.KEY}", scale_factor, title="TYRE DELTA")
        self.scale_factor = scale_factor
        self._init_icons()
        self._build_ui()
        self._init_event_handlers()
        self.logger.debug(f"{self.overlay_id} | Tyre delta page initialized")

    def _init_icons(self):
        """Load tyre icons."""
        self.logger.debug(f"{self.overlay_id} | Loading tyre icons")
        self.tyre_icons = load_tyre_icons_dict(
            debug_log_printer=self.logger.debug,
            error_log_printer=self.logger.error
        )

    def _build_ui(self):
        """Build the UI with reserved space for all compounds."""
        content_widget = QWidget()
        main_layout = QVBoxLayout(content_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # --- UPPER SECTION: TYRE STATS GRID (up to 6 cards) ---
        stats_label = QLabel("BEST AVAILABLE SETS")
        stats_label.setFont(QFont(self.FONT_FACE, self.font_size_label))
        stats_label.setStyleSheet(f"color: {self.COLOR_TEXT_DIM};")
        stats_label.setAlignment(Qt.AlignLeft)
        main_layout.addWidget(stats_label)

        self.stats_grid = QGridLayout()
        self.stats_grid.setSpacing(8)
        self.stats_grid.setContentsMargins(0, 0, 0, 0)

        # Create exactly 6 blank cards (2 rows x 3 cols) - reserve space
        self.tyre_cards = []
        for idx in range(6):
            card = self._create_tyre_card("")
            row = idx // 3
            col = idx % 3
            self.stats_grid.addWidget(card, row, col)
            self.tyre_cards.append(card)

        main_layout.addLayout(self.stats_grid)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet(f"background-color: {self.COLOR_BORDER};")
        separator.setFixedHeight(2)
        main_layout.addWidget(separator)

        # --- LOWER SECTION: ACTUAL COMPOUND MAPPINGS (2x2 Grid) ---
        mapping_label = QLabel("ACTUAL COMPOUNDS")
        mapping_label.setFont(QFont(self.FONT_FACE, self.font_size_label))
        mapping_label.setStyleSheet(f"color: {self.COLOR_TEXT_DIM};")
        mapping_label.setAlignment(Qt.AlignLeft)
        main_layout.addWidget(mapping_label)

        self.mapping_grid = QGridLayout()
        self.mapping_grid.setSpacing(8)
        self.mapping_grid.setContentsMargins(0, 0, 0, 0)

        # Create 2x2 grid for slick compounds
        self.mapping_labels = {}
        for idx, compound in enumerate(self.SLICK_COMPOUNDS):
            mapping_widget = self._create_mapping_widget(compound)
            row = idx // 2
            col = idx % 2
            self.mapping_grid.addWidget(mapping_widget, row, col)
            self.mapping_labels[compound] = mapping_widget

        main_layout.addLayout(self.mapping_grid)

        main_layout.addStretch()
        self.page_layout.addWidget(content_widget)

    def _create_tyre_card(self, compound: str) -> QFrame:
        """Create a compact card for displaying tyre delta.

        Args:
            compound: The tyre compound name (or empty string for blank card)

        Returns:
            QFrame: The styled card widget
        """
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {self.COLOR_BG};
                border: 1px solid {self.COLOR_BORDER};
                border-radius: 6px;
            }}
        """)
        card.setFixedHeight(70)  # Fixed height for all cards

        layout = QHBoxLayout(card)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)

        # Icon on the left
        icon_label = QLabel()
        icon_label.setFixedSize(self.scaled_icon_size, self.scaled_icon_size)
        icon_label.setScaledContents(True)
        layout.addWidget(icon_label)

        # Delta stats on the right
        delta_layout = QVBoxLayout()
        delta_layout.setSpacing(0)
        delta_layout.setContentsMargins(0, 0, 0, 0)
        delta_layout.setAlignment(Qt.AlignCenter)

        # Delta value (big, bright)
        delta_value = QLabel("---")
        delta_value.setFont(QFont(self.MONO_FONT_FACE, self.font_size_value))
        delta_value.setStyleSheet(f"color: {self.COLOR_TEXT_DIM}; border: none;")
        delta_value.setAlignment(Qt.AlignCenter)
        delta_layout.addWidget(delta_value)

        # Delta unit (small, dim)
        delta_unit = QLabel("s/lap")
        delta_unit.setFont(QFont(self.FONT_FACE, self.font_size_unit))
        delta_unit.setStyleSheet(f"color: {self.COLOR_TEXT_DIM}; border: none;")
        delta_unit.setAlignment(Qt.AlignCenter)
        delta_layout.addWidget(delta_unit)

        layout.addLayout(delta_layout)
        layout.addStretch()

        # Store references
        card.icon_label = icon_label
        card.delta_value = delta_value
        card.compound = None  # Will be set when populated

        return card

    def _create_mapping_widget(self, visual_compound: str) -> QWidget:
        """Create a compact widget showing visual to actual compound mapping.

        Args:
            visual_compound: The visual compound name

        Returns:
            QWidget: The mapping display widget
        """
        widget = QFrame()
        widget.setStyleSheet(f"""
            QFrame {{
                background-color: {self.COLOR_BG};
                border: 1px solid {self.COLOR_BORDER};
                border-radius: 4px;
            }}
        """)

        layout = QHBoxLayout(widget)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)

        # Visual compound with small icon
        icon_label = QLabel()
        icon_size = self.scaled_icon_size // 2
        icon_label.setFixedSize(icon_size, icon_size)
        icon_label.setScaledContents(True)
        if visual_compound in self.tyre_icons:
            icon_label.setPixmap(
                self.tyre_icons[visual_compound].pixmap(icon_size, icon_size)
            )
        layout.addWidget(icon_label)

        visual_label = QLabel(visual_compound)
        visual_label.setFont(QFont(self.FONT_FACE, self.font_size_compound))
        visual_label.setStyleSheet(f"color: {self.COLOR_TEXT}; border: none;")
        layout.addWidget(visual_label)

        # Arrow
        arrow_label = QLabel("→")
        arrow_label.setFont(QFont(self.FONT_FACE, self.font_size_compound))
        arrow_label.setStyleSheet(f"color: {self.COLOR_TEXT_DIM}; border: none;")
        layout.addWidget(arrow_label)

        # Actual compound
        actual_label = QLabel("---")
        actual_label.setFont(QFont(self.MONO_FONT_FACE, self.font_size_compound))
        actual_label.setStyleSheet(f"color: {self.COLOR_PRIMARY}; border: none;")
        layout.addWidget(actual_label)

        layout.addStretch()

        widget.actual_label = actual_label
        return widget

    def _init_event_handlers(self):
        """Initialize event handlers."""
        @self.on_event("stream_overlay_update")
        def _handle_stream_overlay_update(data: Dict[str, Any]):
            """Update the page with new data."""
            self.logger.debug(f"{self.overlay_id} | Received stream overlay update")

            tyre_sets_info = data.get("tyre-sets")
            if not tyre_sets_info:
                self._show_no_data()
                return

            tyre_set_data = tyre_sets_info.get("tyre-set-data", [])
            if not tyre_set_data:
                self._show_no_data()
                return

            # Update tyre stats cards
            self._update_tyre_stats(tyre_set_data)

            # Update compound mappings
            self._update_compound_mappings(tyre_set_data)

    def _update_tyre_stats(self, tyre_set_data: List[Dict[str, Any]]):
        """Update the tyre statistics cards.

        Args:
            tyre_set_data: List of tyre set information
        """
        # First, clear all cards
        for card in self.tyre_cards:
            self._clear_card(card)

        # Find best sets for each compound in order
        available_sets = []
        for compound in self.ALL_COMPOUNDS:
            best_set = self._find_best_avlb_set_of_comp(tyre_set_data, compound)
            if best_set:
                available_sets.append((compound, best_set))

        # Populate cards with available data
        for idx, (compound, best_set) in enumerate(available_sets):
            if idx >= 6:  # Safety check - only 6 cards available
                break

            card = self.tyre_cards[idx]
            card.compound = compound

            # Set icon
            if compound in self.tyre_icons:
                card.icon_label.setPixmap(
                    self.tyre_icons[compound].pixmap(self.scaled_icon_size, self.scaled_icon_size)
                )

            # Lap delta (convert from ms to seconds)
            delta_ms = best_set.get("lap-delta-time")
            if delta_ms is not None:
                delta_s = delta_ms / 1000.0  # Convert ms to seconds
                sign = "+" if delta_s > 0 else ""
                color = self._get_delta_color(delta_s)
                card.delta_value.setText(f"{sign}{delta_s:.3f}")
                card.delta_value.setStyleSheet(f"color: {color}; border: none;")
            else:
                card.delta_value.setText("---")
                card.delta_value.setStyleSheet(f"color: {self.COLOR_TEXT_DIM}; border: none;")

    def _clear_card(self, card: QFrame):
        """Clear a card to blank state.

        Args:
            card: The card to clear
        """
        card.compound = None
        card.icon_label.clear()
        card.delta_value.setText("---")
        card.delta_value.setStyleSheet(f"color: {self.COLOR_TEXT_DIM}; border: none;")

    def _update_compound_mappings(self, tyre_set_data: List[Dict[str, Any]]):
        """Update the actual compound mappings.

        Args:
            tyre_set_data: List of tyre set information
        """
        for visual_comp in self.SLICK_COMPOUNDS:
            widget = self.mapping_labels[visual_comp]
            actual_comp = self._get_actual_comp_for_visual_comp(tyre_set_data, visual_comp)

            if actual_comp:
                widget.actual_label.setText(actual_comp)
                widget.actual_label.setStyleSheet(f"color: {self.COLOR_PRIMARY};")
            else:
                widget.actual_label.setText("---")
                widget.actual_label.setStyleSheet(f"color: {self.COLOR_TEXT_DIM};")

    def _find_best_avlb_set_of_comp(self,
        tyre_sets_data: List[Dict[str, Any]],
        compound: str
    ) -> Optional[Dict[str, Any]]:
        """Return the available set of this compound with the lowest wear.

        Args:
            tyre_sets_data: List of all tyre sets
            compound: The compound to search for

        Returns:
            The best available tyre set, or None if none available
        """
        available_sets = [
            tyre_set for tyre_set in tyre_sets_data
            if tyre_set.get("visual-tyre-compound") == compound
            and tyre_set.get("available", False)
        ]

        return min(available_sets, key=lambda s: s.get("wear", 100), default=None)

    def _get_actual_comp_for_visual_comp(self,
                                         tyre_sets_data: List[Dict[str, Any]],
                                         visual_comp: str) -> Optional[str]:
        """Return the actual compound for a given visual compound.

        Args:
            tyre_sets_data: The tyre sets data
            visual_comp: The visual compound to find the actual compound for

        Returns:
            The actual compound string, or None if not found
        """
        tyre_set = next(
            (ts for ts in tyre_sets_data if ts.get("visual-tyre-compound") == visual_comp),
            None
        )
        return tyre_set.get("actual-tyre-compound") if tyre_set else None

    def _get_delta_color(self, delta: float) -> str:
        """Get color for delta time display.

        Args:
            delta: The delta time value

        Returns:
            Color string
        """
        if delta < -0.5:
            return self.COLOR_PRIMARY  # Much faster
        elif delta < 0:
            return self.COLOR_TEXT  # Slightly faster
        elif delta < 0.5:
            return self.COLOR_WARNING  # Slightly slower
        else:
            return self.COLOR_DANGER  # Much slower

    def _show_no_data(self):
        """Show placeholder state when no data available."""
        for card in self.tyre_cards:
            self._clear_card(card)

        for widget in self.mapping_labels.values():
            widget.actual_label.setText("---")
            widget.actual_label.setStyleSheet(f"color: {self.COLOR_TEXT_DIM};")

    @property
    def font_size_value(self) -> int:
        """Get scaled value font size."""
        return int(self.FONT_SIZE_VALUE * self.scale_factor)

    @property
    def font_size_label(self) -> int:
        """Get scaled label font size."""
        return int(self.FONT_SIZE_LABEL * self.scale_factor)

    @property
    def font_size_unit(self) -> int:
        """Get scaled unit font size."""
        return int(self.FONT_SIZE_UNIT * self.scale_factor)

    @property
    def font_size_compound(self) -> int:
        """Get scaled compound font size."""
        return int(self.FONT_SIZE_COMPOUND * self.scale_factor)

    @property
    def scaled_icon_size(self) -> int:
        """Get scaled icon size."""
        return int(self.ICON_SIZE * self.scale_factor)
