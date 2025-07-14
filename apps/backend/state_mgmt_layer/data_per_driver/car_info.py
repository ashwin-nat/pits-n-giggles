# MIT License
#
# Copyright (c) [2024] [Ashwin Natarajan]
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

from dataclasses import dataclass, field
from typing import Optional

from lib.f1_types import CarStatusData
from lib.fuel_rate_recommender import FuelRateRecommender

# -------------------------------------- GLOBALS -----------------------------------------------------------------------

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------

@dataclass(slots=True)
class CarInfo:
    """
    Class that models the car-related data for a race driver.
    """
    total_laps: int = field(repr=False)  # 👈 Must come first

    m_ers_perc: Optional[float] = None
    m_drs_activated: Optional[bool] = None
    m_drs_allowed: Optional[bool] = None
    m_drs_distance: Optional[int] = None
    m_fl_wing_damage: Optional[int] = None
    m_fr_wing_damage: Optional[int] = None
    m_rear_wing_damage: Optional[int] = None

    m_fuel_rate_recommender: "FuelRateRecommender" = field(init=False)

    def __post_init__(self):
        self.m_fuel_rate_recommender = FuelRateRecommender(
            [],
            total_laps=self.total_laps,
            min_fuel_kg=CarStatusData.MIN_FUEL_KG
        )
