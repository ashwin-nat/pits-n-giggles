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

from typing import List, Optional, Dict, Any

class FuelRemainingPerLap:
    """Class representing the fuel usage per lap.

    Attributes:
        m_lap_number (int): Lap number.
        m_fuel_usage (float): Fuel usage.
        m_is_racing_lap (bool, optional): Indicates if the lap is a racing lap. Defaults to True.
        m_desc (Optional[str], optional): Description. Defaults to None.
    """
    def __init__(self,
        lap_number: int,
        fuel_remaining: float,
        is_racing_lap: bool = True,
        desc: Optional[str] = None) -> None:
        """
        Initialize a FuelUsagePerLap object.

        Args:
            lap_number (int): Lap number.
            fuel_remaining (float): Fuel remaining in tank in kg.
            is_racing_lap (bool, optional): Indicates if the lap is a racing lap. Defaults to True.
            desc (Optional[str], optional): Description. Defaults to None.
        """

        self.m_lap_number: int = lap_number
        self.m_fuel_remaining: float = fuel_remaining
        self.m_is_racing_lap: bool = is_racing_lap
        self.m_desc: Optional[str] = desc

    def toJSON(self) -> Dict[str, Any]:
        """Convert the object to JSON format.

        Returns:
            Dict[str, Any]: JSON representation of the object.
        """
        return {
            "lap-number": self.m_lap_number,
            "fuel-usage": self.m_fuel_remaining,
            "is-racing-lap": self.m_is_racing_lap,
            "desc": self.m_desc
        }

class FuelRateRecommender:
    """Class representing the fuel rate extrapolator.

    Attributes:
        m_fuel_usage_history (List[FuelUsagePerLap]): List of fuel usage per lap.
        m_total_laps (int): Total number of laps in the race.
        m_min_fuel_kg (float): Minimum fuel required in the car
    """

    def __init__(self, fuel_remaining_history: List[FuelRemainingPerLap], total_laps: int, min_fuel_kg: float) -> None:
        """
        Initialize a FuelRateExtrapolator object.

        Args:
            fuel_remaining_history (List[FuelUsagePerLap]): List of fuel remaining per lap.
            total_laps (int): Total number of laps in the race.
            min_fuel_kg (float): Minimum fuel required in the car
        """

        self.m_fuel_remaining_history: List[FuelRemainingPerLap] = fuel_remaining_history
        self.m_total_laps: int = total_laps
        self.m_min_fuel_kg: float = min_fuel_kg

        self.m_curr_fuel_rate: Optional[float] = None
        self.m_target_fuel_rate: Optional[float] = None

        self._recompute()

    def isDataSufficient(self) -> bool:
        """Check if the amount of data available for extrapolation is sufficient.

        Returns:
            bool: True if sufficient
        """

        # We need 2 data points since we also include 0th lap data point
        return (len(self.m_fuel_remaining_history) >= 2) and (self.m_total_laps is not None)

    def clear(self) -> None:
        """Clear the fuel rate extrapolator's data
        """

        self.m_fuel_remaining_history.clear()

    @property
    def curr_fuel_rate(self) -> float:
        """Get the current fuel rate

        Returns:
            float: Current fuel rate
        """

        return self.m_curr_fuel_rate

    @property
    def target_fuel_rate(self) -> float:
        """Get the target fuel rate

        Returns:
            float: Target fuel rate
        """

        return self.m_target_fuel_rate

    @property
    def fuel_used_last_lap(self) -> Optional[float]:
        """Get the fuel used in the last lap

        Returns:
            float: Fuel used in the last lap. None if not available
        """

        if len(self.m_fuel_remaining_history) >= 2:
            return self.m_fuel_remaining_history[-2].m_fuel_remaining - \
                self.m_fuel_remaining_history[-1].m_fuel_remaining
        return None

    @property
    def total_laps(self) -> int:
        """Get the total number of laps in the race

        Returns:
            int: The total number of laps in the race
        """
        return self.m_total_laps

    @total_laps.setter
    def total_laps(self, value: int):
        """Set the total number of laps in the race

        Args:
            value (int): The total number of laps in the race
        """
        should_recompute = self.m_total_laps is None
        self.m_total_laps = value
        if should_recompute:
            self._recompute()

    def add(self, fuel_remaining: float, lap_number: int) -> None:
        """Add a new fuel usage per lap

        Args:
            fuel_remaining (float): Fuel remaining in tank in kg.
            lap_number (int): Lap number
        """

        self.m_fuel_remaining_history.append(FuelRemainingPerLap(lap_number, fuel_remaining))
        self._recompute()

    def _recompute(self) -> None:
        """Recompute the current and target fuel rate
        """

    def _recompute(self) -> None:
        """Recompute the current and target fuel rate."""

        if not self.isDataSufficient():
            return

        # Calculate the current fuel rate based on the last two laps
        if len(self.m_fuel_remaining_history) > 1:
            last_lap_fuel = self.m_fuel_remaining_history[-1].m_fuel_remaining
            second_last_lap_fuel = self.m_fuel_remaining_history[-2].m_fuel_remaining
            self.m_curr_fuel_rate = second_last_lap_fuel - last_lap_fuel

        # Estimate remaining fuel after all laps
        current_fuel = self.m_fuel_remaining_history[-1].m_fuel_remaining
        laps_left = self.m_total_laps - self.m_fuel_remaining_history[-1].m_lap_number

        # Calculate target fuel rate to meet the minimum fuel requirement at the end
        if laps_left > 0:
            self.m_target_fuel_rate = (current_fuel - self.m_min_fuel_kg) / laps_left
        else:
            self.m_target_fuel_rate = None