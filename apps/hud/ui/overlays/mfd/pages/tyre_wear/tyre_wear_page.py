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

from PySide6.QtQuick import QQuickItem

from apps.hud.common import get_ref_row
from apps.hud.ui.overlays.mfd.pages.base_page import MfdPageBase

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class TyreInfoPage(MfdPageBase):

    KEY = "tyre_info"
    QML_FILE: Path = Path(__file__).parent / "tyre_wear_page.qml"

    NUM_DECIMAL_PLACES = 2
    MED_WEAR = 50
    DANGER_WEAR = 75

    def __init__(self, overlay, logger: logging.Logger):
        super().__init__(overlay, logger)
        self._init_event_handlers()

    def _init_event_handlers(self):
        """Initialise event handlers."""
        @self.on_event("race_table_update")
        def _handle_race_table_update(data: Dict[str, Any]) -> None:
            """Update tyre wear information display."""
            page_item = self._page_item
            if not page_item:
                return

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
            page_item.setProperty("currentCompound", actual_tyre_comp)
            page_item.setProperty("currentCompoundVisual", visual_tyre_comp)

            # Update stats
            page_item.setProperty("tyreAge", tyre_age)

            # Calculate and display wear rate
            tyre_wear_rates: Dict[str, Any] = tyre_info.get('wear-prediction', {}).get('rate', {})
            if tyre_wear_rates:
                avg_rate = sum(tyre_wear_rates.values()) / len(tyre_wear_rates.values())
                page_item.setProperty("wearRate", avg_rate)
            else:
                page_item.setProperty("wearRate", 0.0)

            if telemetry_settings != "Public":
                page_item.setProperty("telemetryDisabled", True)
                return

            page_item.setProperty("telemetryDisabled", False)

            # Update wear table
            curr_lap_num = ref_row["lap-info"]["current-lap"]
            wear_prediction = tyre_info["wear-prediction"]
            predictions = None
            pit_lap = None

            if self._is_wear_prediction_supported(data):
                pit_lap = wear_prediction["selected-pit-stop-lap"]
                predictions = wear_prediction["predictions"]

            self._update_wear_table(curr_wear, curr_lap_num, predictions, pit_lap, page_item)

        @self.on_event("stream_overlay_update")
        def _handle_stream_overlay_update(data: Dict[str, Any]) -> None:
            """Update tyre wear information display."""
            page_item = self._page_item
            if not page_item:
                return
            tyre_sets_info = data["tyre-sets"]
            if not tyre_sets_info:
                return

            fresh_avlb_tyre_sets = [
                tyre_set
                for tyre_set in tyre_sets_info["tyre-set-data"]
                if tyre_set["available"] and not tyre_set["fitted"] and tyre_set['wear'] == 0
            ]
            groupings_by_comp = self._get_tyres_grouping_by_vis_comp(fresh_avlb_tyre_sets)
            self._update_available_tyres_display(groupings_by_comp, page_item)

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

    def _update_available_tyres_display(self, groupings_by_comp: Dict[str, Dict[str, Any]], page_item: QQuickItem) -> None:
        """Update the right side of top section with available fresh tyres.

        Args:
            groupings_by_comp (Dict[str, Dict[str, Any]]): Dictionary of tyre counts by visual compound.
            page_item (QQuickItem): The page item to update.
        """
        # Reset all counts to 0 first
        tyre_counts = {
            "Soft": 0,
            "Medium": 0,
            "Hard": 0,
            "Super Soft": 0,
            "Inters": 0,
            "Wet": 0
        }

        # Update counts for available tyres
        for visual_compound, stats in groupings_by_comp.items():
            count = stats['count']
            if visual_compound in tyre_counts:
                tyre_counts[visual_compound] = count

        page_item.setProperty("tyreCounts", tyre_counts)

    def _update_wear_table(self, curr_wear: Dict[str, float], curr_lap: int,
                          predictions: Optional[List[Dict]], pit_lap: Optional[int], page_item: QQuickItem) -> None:
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

        # Ensure we always have exactly 3 rows
        while len(rows_data) < 3:
            rows_data.append({
                'label': '',
                'fl': 0.0,
                'fr': 0.0,
                'rl': 0.0,
                'rr': 0.0,
            })

        # Update QML table data
        page_item.setProperty("wearTableData", rows_data[:3])

    def _find_closest_prediction(self, predictions: List[Dict], target_lap: int) -> Optional[Dict]:
        """Find the prediction closest to the target lap."""
        if not predictions:
            return None
        return min(predictions, key=lambda p: abs(p["lap-number"] - target_lap))

    def _is_wear_prediction_supported(self, data: Dict[str, Any]) -> bool:
        """Check if wear prediction is supported for this event."""
        event_type: str = data.get("event-type", "")
        return event_type and "Race" in event_type
