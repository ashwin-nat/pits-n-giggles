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

from apps.hud.ui.overlays.pu.pu import PuOverlay

from .base_page import MfdPageBase
from .collapsed import CollapsedPage
from .fuel import FuelInfoPage
from .lap_times import LapTimesPage
from .pace_comp.pace_comp import PaceCompPage
from .pit_rejoin import PitRejoinPredictionPage
from .standalone_base import StandalonePageOverlay
from .traffic_monitor import TrafficMonitorPage
from .tyre_sets import TyreSetsPage
from .tyre_wear import TyreInfoPage
from .weather import WeatherForecastPage

# -------------------------------------- EXPORTS -----------------------------------------------------------------------

__all__ = [
    "MfdPageBase",
    "StandalonePageOverlay",
    "CollapsedPage",
    "FuelInfoPage",
    "LapTimesPage",
    "PitRejoinPredictionPage",
    "TyreSetsPage",
    "TyreInfoPage",
    "WeatherForecastPage",
    "PaceCompPage",
    "TrafficMonitorPage",
    "PuOverlay",
]
