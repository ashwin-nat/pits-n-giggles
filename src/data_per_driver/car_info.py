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

from dataclasses import dataclass
from typing import Optional

from lib.f1_types import CarStatusData
from lib.fuel_rate_recommender import FuelRateRecommender
from src.png_logger import getLogger

# -------------------------------------- GLOBALS -----------------------------------------------------------------------

png_logger = getLogger()

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------

@dataclass
class CarInfo:
    """
    Class that models the car-related data for a race driver.

    Attributes:
        m_ers_perc (Optional[float]): The percentage of ERS battery remaining.
        m_drs_activated (Optional[bool]): Indicates whether the DRS is activated for the car.
        m_drs_allowed (Optional[bool]): Indicates whether DRS is allowed for the car.
        m_drs_distance (Optional[int]): The distance to the car in front for DRS activation.
        m_fl_wing_damage (Optional[int]): Left front wing damage.
        m_fr_wing_damage (Optional[int]): Right front wing damage.
        m_rear_wing_damage (Optional[int]): Rear wing damage.
        m_fuel_rate_recommender (FuelRateRecommender): Fuel usage rate recommender for the car.
    """
    def __init__(self, total_laps: int) -> None:
        self.m_ers_perc: Optional[float] = None
        self.m_drs_activated: Optional[bool] = None
        self.m_drs_allowed: Optional[bool] = None
        self.m_drs_distance: Optional[int] = None
        self.m_fl_wing_damage: Optional[int] = None
        self.m_fr_wing_damage: Optional[int] = None
        self.m_rear_wing_damage: Optional[int] = None
        self.m_fuel_rate_recommender: FuelRateRecommender = FuelRateRecommender([], total_laps=total_laps,
                                                                                min_fuel_kg=CarStatusData.MIN_FUEL_KG)
