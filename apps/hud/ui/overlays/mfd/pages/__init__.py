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

from .base_page import MfdPageBase
from .collapsed.collapsed import CollapsedPage
from .fuel.fuel_page import FuelInfoPage
from .lap_times.lap_times import LapTimesPage
from .pace_comp.pace_comp import PaceCompPage
from .pit_rejoin.pit_rejoin_page import PitRejoinPredictionPage
from .standalone_host import StandalonePageHost
from .traffic_monitor.traffic_monitor_page import TrafficMonitorPage
from .tyre_sets.tyre_sets_page import TyreSetsPage
from .tyre_wear.tyre_wear_page import TyreInfoPage
from .weather.weather import WeatherForecastPage

# -------------------------------------- EXPORTS -----------------------------------------------------------------------

__all__ = [
    "MfdPageBase",
    "StandalonePageHost",
    "CollapsedPage",
    "FuelInfoPage",
    "LapTimesPage",
    "PitRejoinPredictionPage",
    "TyreSetsPage",
    "TyreInfoPage",
    "WeatherForecastPage",
    "PaceCompPage",
    "TrafficMonitorPage",
]
