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
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from PySide6.QtQuick import QQuickItem

from apps.hud.ui.overlays.mfd.pages.base_page import MfdPageBase

if TYPE_CHECKING:
    from apps.hud.ui.overlays.mfd.mfd import MfdOverlay

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class TyreSetsPage(MfdPageBase):

    KEY = "tyre_sets"
    QML_FILE: Path = Path(__file__).parent / "tyre_sets_page.qml"

    ALL_COMPOUNDS = ["Super Soft", "Soft", "Medium", "Hard", "Inters", "Wet"]
    SLICK_COMPOUNDS = ["Super Soft", "Soft", "Medium", "Hard"]

    def __init__(self, overlay: "MfdOverlay", logger: logging.Logger):
        super().__init__(overlay, logger)
        self._init_event_handlers()

    def _init_event_handlers(self):
        @self.on_event("stream_overlay_update")
        def _handle_stream_overlay_update(data: Dict[str, Any]):
            page_item = self.overlay.current_page_item
            if not page_item:
                return

            tyre_sets_info = data.get("tyre-sets")
            if not tyre_sets_info:
                self._show_no_data(page_item)
                return

            tyre_set_data = tyre_sets_info.get("tyre-set-data", [])
            if not tyre_set_data:
                self._show_no_data(page_item)
                return

            best_sets = self._prepare_best_sets(tyre_set_data)
            compound_mappings = self._prepare_compound_mappings(tyre_set_data)

            page_item.setProperty("bestSets", best_sets)
            page_item.setProperty("compoundMappings", compound_mappings)

    def _prepare_best_sets(self, tyre_set_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare best available set for each compound type.

        Args:
            tyre_set_data: Raw tyre set data

        Returns:
            List of dicts with compound, deltaMs, and deltaS for each unique compound
        """
        best_sets = []

        # For each compound in order, find the best available set
        for compound in self.ALL_COMPOUNDS:
            best_set = self._find_best_avlb_set_of_comp(tyre_set_data, compound)
            if best_set:
                delta_ms = best_set.get("lap-delta-time")
                best_sets.append({
                    "compound": compound,
                    "deltaMs": delta_ms if delta_ms is not None else None,
                    "deltaS": delta_ms / 1000.0 if delta_ms is not None else None
                })

        return best_sets

    def _prepare_compound_mappings(self, tyre_set_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare visual to actual compound mappings for slicks.

        Args:
            tyre_set_data: Raw tyre set data

        Returns:
            List of dicts with visualCompound and actualCompound
        """
        mappings = []

        for visual_compound in self.SLICK_COMPOUNDS:
            actual_compound = self._get_actual_comp_for_visual_comp(tyre_set_data, visual_compound)
            if actual_compound:
                mappings.append({
                    "visualCompound": visual_compound,
                    "actualCompound": actual_compound
                })

        return mappings

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

    def _show_no_data(self, page_item: QQuickItem):
        """Show placeholder state when no data available."""
        page_item.setProperty("bestSets", [])
        page_item.setProperty("compoundMappings", [])
