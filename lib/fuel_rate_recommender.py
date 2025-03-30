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
    """Class representing the fuel rate recommender.

    Attributes:
        m_fuel_remaining_history (List[FuelRemainingPerLap]): List of fuel remaining per lap.
        m_total_laps (int): Total number of laps in the race.
        m_min_fuel_kg (float): Minimum fuel required in the car
    """

    def __init__(self, fuel_remaining_history: List[FuelRemainingPerLap], total_laps: int, min_fuel_kg: float) -> None:
        """
        Initialize a FuelRateRecommender object.

        Args:
            fuel_remaining_history (List[FuelRemainingPerLap]): List of fuel remaining per lap.
            total_laps (int): Total number of laps in the race.
            min_fuel_kg (float): Minimum fuel required in the car
        """

        self.m_fuel_remaining_history: List[FuelRemainingPerLap] = fuel_remaining_history
        self.m_total_laps: int = total_laps
        self.m_min_fuel_kg: float = min_fuel_kg

        # Pre-computed values
        self.m_curr_fuel_rate: Optional[float] = None
        self.m_target_fuel_rate: Optional[float] = None
        self.m_target_next_lap_fuel_usage: Optional[float] = None
        self.m_surplus_laps: Optional[float] = None
        self.m_safety_car_fuel_rate: Optional[float] = None
        self.m_fuel_used_last_lap: Optional[float] = None
        self.m_predicted_final_fuel: Dict[int, float] = {}  # Keyed by expected safety car laps

        self._recompute()

    def isDataSufficient(self) -> bool:
        """Check if the amount of data available for extrapolation is sufficient.

        Returns:
            bool: True if sufficient
        """
        # We need 2 data points since we also include 0th lap data point
        return (len(self.m_fuel_remaining_history) >= 2) and (self.m_total_laps is not None)

    def clear(self) -> None:
        """Clear the fuel rate recommender's data
        """
        self.m_fuel_remaining_history.clear()
        self._reset_computed_values()

    def _reset_computed_values(self) -> None:
        """Reset all pre-computed values
        """
        self.m_curr_fuel_rate = None
        self.m_target_fuel_rate = None
        self.m_target_next_lap_fuel_usage = None
        self.m_surplus_laps = None
        self.m_safety_car_fuel_rate = None
        self.m_fuel_used_last_lap = None
        self.m_predicted_final_fuel = {}

    @property
    def curr_fuel_rate(self) -> Optional[float]:
        """Get the current fuel rate

        Returns:
            Optional[float]: Current fuel rate
        """
        return self.m_curr_fuel_rate

    @property
    def target_fuel_rate(self) -> Optional[float]:
        """Get the target fuel rate

        Returns:
            Optional[float]: Target fuel rate
        """
        return self.m_target_fuel_rate

    @property
    def target_next_lap_fuel_usage(self) -> Optional[float]:
        """Get the target fuel usage for the next lap

        Returns:
            Optional[float]: Target fuel usage for next lap. None if not available
        """
        return self.m_target_next_lap_fuel_usage

    @property
    def surplus_laps(self) -> Optional[float]:
        """Get the number of surplus laps worth of fuel the car has

        Returns:
            Optional[float]: The surplus laps count (can be positive, negative, fractional)
        """
        return self.m_surplus_laps

    @property
    def safety_car_fuel_rate(self) -> Optional[float]:
        """Get the average fuel rate during safety car periods

        Returns:
            Optional[float]: Average safety car fuel rate. None if not available
        """
        return self.m_safety_car_fuel_rate

    @property
    def fuel_used_last_lap(self) -> Optional[float]:
        """Get the fuel used in the last lap

        Returns:
            Optional[float]: Fuel used in the last lap. None if not available
        """
        return self.m_fuel_used_last_lap

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
        should_recompute = self.m_total_laps != value
        self.m_total_laps = value
        if should_recompute:
            self._recompute()

    def add(self, fuel_remaining: float, lap_number: int, is_racing_lap: bool = True, desc: Optional[str] = None) -> None:
        """Add a new fuel remaining per lap

        Args:
            fuel_remaining (float): Fuel remaining in tank in kg.
            lap_number (int): Lap number
            is_racing_lap (bool, optional): Indicates if the lap is a racing lap. Defaults to True.
            desc (Optional[str], optional): Description. Defaults to None.
        """
        self.m_fuel_remaining_history.append(
            FuelRemainingPerLap(lap_number, fuel_remaining, is_racing_lap, desc)
        )
        self._recompute()

    def predict_final_fuel(self, expected_safety_car_laps: int = 0) -> Optional[float]:
        """Get the predicted final fuel remaining

        Args:
            expected_safety_car_laps (int, optional): Expected number of safety car laps. Defaults to 0.

        Returns:
            Optional[float]: Predicted final fuel remaining, None if not enough data
        """
        return self.m_predicted_final_fuel.get(expected_safety_car_laps)

    def _compute_last_lap_fuel_usage(self) -> None:
        """Compute fuel used in the last lap"""

        if len(self.m_fuel_remaining_history) >= 2:
            self.m_fuel_used_last_lap = (self.m_fuel_remaining_history[-2].m_fuel_remaining -
                                        self.m_fuel_remaining_history[-1].m_fuel_remaining)

    def _compute_racing_fuel_rate(self, racing_laps: List[FuelRemainingPerLap]) -> None:
        """Compute average fuel rate for racing laps

        Args:
            racing_laps (List[FuelRemainingPerLap]): List of racing laps
        """
        if len(racing_laps) <= 1:
            return

        # Sort by lap number to ensure correct order
        racing_laps.sort(key=lambda x: x.m_lap_number)

        # Use the most recent racing lap and the first racing lap for calculation
        last_racing_lap = racing_laps[-1]
        first_racing_lap = racing_laps[0]

        fuel_used = first_racing_lap.m_fuel_remaining - last_racing_lap.m_fuel_remaining
        laps_completed = last_racing_lap.m_lap_number - first_racing_lap.m_lap_number

        if laps_completed > 0:
            self.m_curr_fuel_rate = fuel_used / laps_completed

    def _compute_safety_car_fuel_rate(self, safety_car_laps: List[FuelRemainingPerLap]) -> None:
        """Compute average fuel rate for safety car laps

        Args:
            safety_car_laps (List[FuelRemainingPerLap]): List of safety car laps
        """
        if len(safety_car_laps) > 1:
            # Sort by lap number to ensure correct order
            safety_car_laps.sort(key=lambda x: x.m_lap_number)

            # Calculate total fuel used during safety car periods
            total_fuel_used = safety_car_laps[0].m_fuel_remaining - safety_car_laps[-1].m_fuel_remaining
            total_sc_laps = safety_car_laps[-1].m_lap_number - safety_car_laps[0].m_lap_number

            if total_sc_laps > 0:
                self.m_safety_car_fuel_rate = total_fuel_used / total_sc_laps
        # If no safety car laps data but we have racing data, estimate safety car fuel rate
        elif self.m_curr_fuel_rate is not None:
            # Safety car typically uses about 60-70% of racing fuel
            self.m_safety_car_fuel_rate = self.m_curr_fuel_rate * 0.65

    def _compute_target_values(self, current_fuel: float, laps_left: int) -> None:
        """Compute target fuel rate and related values

        Args:
            current_fuel (float): Current fuel level
            laps_left (int): Number of laps left
        """
        if laps_left <= 0:
            return

        self.m_target_fuel_rate = (current_fuel - self.m_min_fuel_kg) / laps_left

        # Calculate surplus/deficit laps
        if self.m_curr_fuel_rate is not None and self.m_curr_fuel_rate > 0:
            available_fuel = current_fuel - self.m_min_fuel_kg
            laps_at_current_rate = available_fuel / self.m_curr_fuel_rate
            self.m_surplus_laps = laps_at_current_rate - laps_left

        # Calculate target fuel usage for next lap
        if self.m_curr_fuel_rate is not None and self.m_target_fuel_rate is not None:
            fuel_rate_difference = self.m_curr_fuel_rate - self.m_target_fuel_rate
            adjustment_factor = 0.5
            self.m_target_next_lap_fuel_usage = self.m_target_fuel_rate - (fuel_rate_difference * adjustment_factor)
        elif self.m_target_fuel_rate is not None:
            self.m_target_next_lap_fuel_usage = self.m_target_fuel_rate

    def _compute_fuel_predictions(self, current_fuel: float, laps_left: int) -> None:
        """Compute predictions for different safety car scenarios

        Args:
            current_fuel (float): Current fuel level
            laps_left (int): Number of laps left
        """
        if self.m_curr_fuel_rate is None:
            return

        max_sc_laps_to_compute = min(6, laps_left + 1)  # Compute for 0 to min(5, laps_left)

        for sc_laps in range(max_sc_laps_to_compute):
            racing_laps_left = laps_left - sc_laps

            racing_fuel_usage = racing_laps_left * self.m_curr_fuel_rate
            safety_car_fuel_usage = sc_laps * (self.m_safety_car_fuel_rate or 0)

            self.m_predicted_final_fuel[sc_laps] = current_fuel - racing_fuel_usage - safety_car_fuel_usage

    def _recompute(self) -> None:
        """Recompute all values for fuel predictions."""
        self._reset_computed_values()

        if not self.isDataSufficient():
            return

        # Compute fuel used in last lap
        self._compute_last_lap_fuel_usage()

        # Split laps by type
        racing_laps = [lap for lap in self.m_fuel_remaining_history if lap.m_is_racing_lap]
        safety_car_laps = [lap for lap in self.m_fuel_remaining_history if not lap.m_is_racing_lap]

        # Compute fuel rates
        self._compute_racing_fuel_rate(racing_laps)
        self._compute_safety_car_fuel_rate(safety_car_laps)

        # Get current fuel and laps left
        current_fuel = self.m_fuel_remaining_history[-1].m_fuel_remaining
        laps_left = self.m_total_laps - self.m_fuel_remaining_history[-1].m_lap_number

        # Compute target values
        self._compute_target_values(current_fuel, laps_left)

        # Compute fuel predictions
        self._compute_fuel_predictions(current_fuel, laps_left)
