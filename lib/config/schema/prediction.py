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

from enum import Enum
from typing import Any, ClassVar, Dict, Optional

from pydantic import BaseModel, Field

from .diff import ConfigDiffMixin

# -------------------------------------- CLASS  DEFINITIONS ------------------------------------------------------------

class HarvestPowerSmoothing(str, Enum):
    """Smoothing profile for the harvest power estimate, from most responsive to most stable."""
    VERY_RESPONSIVE = "Very responsive"
    RESPONSIVE = "Responsive"
    BALANCED = "Balanced"
    STABLE = "Stable"
    VERY_STABLE = "Very stable"

# Maps each smoothing profile to the linear-fit filter's rolling window size (in samples). At the
# ~60 Hz input cadence these span roughly 115 / 180 / 250 / 350 / 450 ms. Any window >= 2 is valid
# for the filter, so this scale can be tuned freely without touching lib/power_estimator.
_HARVEST_POWER_SMOOTHING_WINDOWS: Dict[HarvestPowerSmoothing, int] = {
    HarvestPowerSmoothing.VERY_RESPONSIVE: 7,
    HarvestPowerSmoothing.RESPONSIVE: 11,
    HarvestPowerSmoothing.BALANCED: 15,
    HarvestPowerSmoothing.STABLE: 21,
    HarvestPowerSmoothing.VERY_STABLE: 27,
}

class PredictionSettings(ConfigDiffMixin, BaseModel):
    ui_meta: ClassVar[Dict[str, Any]] = {
        "visible": True,
    }

    weather_aware_prediction: bool = Field(
        default=False,
        description="Enable weather-aware tyre wear prediction",
        json_schema_extra={
            "ui": {
                "type": "check_box",
                "visible": True,
                "ext_info": [
                    "EXPERIMENTAL: When enabled, tyre wear regression uses only laps from the \n"
                    "current weather group (dry or wet), ignoring earlier laps recorded under \n"
                    "different conditions. This improves accuracy after weather transitions but \n"
                    "may produce unstable predictions early in a new weather segment."
                ]
            }
        }
    )

    tyre_wear_window_size: Optional[int] = Field(
        default=None,
        ge=2,
        description="Sliding window size for tyre wear prediction (laps)",
        json_schema_extra={
            "ui": {
                "type": "text_box",
                "visible": True,
                "ext_info": [
                    "EXPERIMENTAL: Limits tyre wear regression to the N most recent racing laps. \n"
                    "Helps the model adapt quickly to changing conditions (e.g. dry to wet) \n"
                    "instead of averaging over the entire stint. \n"
                    "If interested, recommended values are 4-6 laps. \n"
                    "Leave empty to use all available data (default behaviour)."
                ]
            }
        }
    )

    harvest_power_smoothing: HarvestPowerSmoothing = Field(
        default=HarvestPowerSmoothing.BALANCED,
        description="Harvest power smoothing",
        json_schema_extra={
            "ui": {
                "type": "radio_buttons",
                "options": [e.value for e in HarvestPowerSmoothing],
                "visible": True,
                "ext_info": [
                    "The F1 games don't natively export the instantaneous harvest power, so \n"
                    "Pits n' Giggles estimates it from how fast the car's harvested energy is \n"
                    "climbing — the rate of change of cumulative energy over time (dE/dt).",
                    "Reading a rate of change off a live signal amplifies noise, so the result \n"
                    "is smoothed. More responsive reacts faster to sudden changes (e.g. \n"
                    "braking-zone harvesting) but looks noisier; more stable is smoother but \n"
                    "lags behind. Balanced is recommended for the default ~60 Hz update rate."
                ]
            }
        }
    )

    @property
    def harvest_power_window_size(self) -> int:
        """Rolling sample window for the harvest power filter, derived from the selected
        smoothing profile. Consumers construct the estimator with this value."""
        return _HARVEST_POWER_SMOOTHING_WINDOWS[self.harvest_power_smoothing]
