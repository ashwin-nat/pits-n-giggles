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

    def __str__(self) -> str:
        """Return a string representation of the object."""
        lap_type = "Racing" if self.m_is_racing_lap else "Safety Car"
        return f"Lap {self.m_lap_number}: {self.m_fuel_remaining:.2f}kg ({lap_type})"

class FuelRateRecommender:
    """Class representing the fuel rate recommender with discontinuity handling."""
    """
    ALGORITHM EXPLANATION:

    1. Data Storage:
    - Maintains history of fuel readings with lap number, fuel remaining, and lap type

    2. Fuel Rate Calculation:
    - Groups racing laps into consecutive segments to handle safety car interruptions
    - Calculates fuel usage within each segment separately
    - Derives overall rate from total fuel used across segments divided by racing lap count

    3. Target Calculation:
    - Computes target fuel rate to finish with minimum required fuel
    - Determines surplus/deficit laps based on current consumption
    - Calculates adaptive target for next lap

    4. Prediction:
    - Projects final fuel level using current racing fuel rate
    - Assumes all remaining laps are racing laps

    5. Recomputation:
    - Refreshes all calculations when new data is added
    - Sequence: last lap usage → racing rate → current state → targets → predictions
    """

    def __init__(self, fuel_remaining_history: List[FuelRemainingPerLap], total_laps: int, min_fuel_kg: float) -> None:
        self.m_fuel_remaining_history: List[FuelRemainingPerLap] = fuel_remaining_history
        self.m_total_laps: int = total_laps
        self.m_min_fuel_kg: float = min_fuel_kg

        # Pre-computed values
        self.m_curr_fuel_rate: Optional[float] = None
        self.m_target_fuel_rate: Optional[float] = None
        self.m_target_next_lap_fuel_usage: Optional[float] = None
        self.m_surplus_laps: Optional[float] = None
        self.m_fuel_used_last_lap: Optional[float] = None
        self.m_predicted_final_fuel: Dict[int, float] = {}

        self._recompute()

    def isDataSufficient(self) -> bool:
        """Check if the amount of data available for extrapolation is sufficient.

        Returns:
            bool: True if sufficient
        """
        racing_laps = [lap for lap in self.m_fuel_remaining_history if lap.m_is_racing_lap]
        return len(racing_laps) >= 2 and self.m_total_laps is not None

    def clear(self) -> None:
        """Clear the fuel rate recommender's data
        """
        self.m_fuel_remaining_history.clear()
        self.m_total_laps = None
        self._clearComputedValues()

    def _clearComputedValues(self) -> None:
        """Clear the computed values
        """
        self.m_curr_fuel_rate = None
        self.m_target_fuel_rate = None
        self.m_target_next_lap_fuel_usage = None
        self.m_surplus_laps = None
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

    def predict_final_fuel(self) -> Optional[float]:
        """Get the predicted final fuel remaining"""
        return self.m_predicted_final_fuel.get(0)

    def _compute_racing_fuel_rate(self, racing_laps: List[FuelRemainingPerLap]) -> None:
        """Compute average fuel rate using ONLY racing laps, handling discontinuities"""
        if len(racing_laps) <= 1:
            return

        # Sort by lap number
        racing_laps.sort(key=lambda x: x.m_lap_number)

        # Find consecutive racing lap segments
        consecutive_segments = []
        current_segment = [racing_laps[0]]

        for i in range(1, len(racing_laps)):
            # Check if laps are consecutive
            if racing_laps[i].m_lap_number == racing_laps[i-1].m_lap_number + 1:
                current_segment.append(racing_laps[i])
            else:
                # Non-consecutive laps indicate a discontinuity (safety car period)
                if len(current_segment) > 1:
                    consecutive_segments.append(current_segment)
                current_segment = [racing_laps[i]]

        # Add the last segment if it has more than one lap
        if len(current_segment) > 1:
            consecutive_segments.append(current_segment)

        # Calculate fuel rate from all consecutive segments
        total_fuel_used = 0
        total_racing_laps = 0

        for segment in consecutive_segments:
            segment_fuel_used = segment[0].m_fuel_remaining - segment[-1].m_fuel_remaining
            segment_laps = segment[-1].m_lap_number - segment[0].m_lap_number
            total_fuel_used += segment_fuel_used
            total_racing_laps += segment_laps

        # If we have valid segments, calculate the rate
        if total_racing_laps > 0:
            self.m_curr_fuel_rate = total_fuel_used / total_racing_laps

    def _compute_last_lap_fuel_usage(self) -> None:
        """Compute fuel used in the last lap"""
        if len(self.m_fuel_remaining_history) >= 2:
            self.m_fuel_used_last_lap = (self.m_fuel_remaining_history[-2].m_fuel_remaining -
                                         self.m_fuel_remaining_history[-1].m_fuel_remaining)

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

        # Calculate target fuel usage for next lap (restored from original)
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

        # Only make one prediction - assuming all remaining laps are racing laps
        self.m_predicted_final_fuel[0] = current_fuel - (laps_left * self.m_curr_fuel_rate)

    def _recompute(self) -> None:
        """Recompute all values for fuel predictions."""
        # Reset computed values
        self._clearComputedValues()

        if not self.isDataSufficient():
            return

        # Compute fuel used in last lap
        self._compute_last_lap_fuel_usage()

        # Only use racing laps for calculations
        racing_laps = [lap for lap in self.m_fuel_remaining_history if lap.m_is_racing_lap]
        self._compute_racing_fuel_rate(racing_laps)

        # Get current fuel and laps left
        current_fuel = self.m_fuel_remaining_history[-1].m_fuel_remaining
        laps_left = self.m_total_laps - self.m_fuel_remaining_history[-1].m_lap_number

        # Compute target values
        self._compute_target_values(current_fuel, laps_left)

        # Compute fuel predictions
        self._compute_fuel_predictions(current_fuel, laps_left)

    def __str__(self) -> str:
        """String representation with predictions"""
        if not self.isDataSufficient():
            return "Insufficient data for predictions"

        current_lap = self.m_fuel_remaining_history[-1].m_lap_number
        current_fuel = self.m_fuel_remaining_history[-1].m_fuel_remaining
        predicted_fuel = self.predict_final_fuel()

        result = [
            f"Current lap: {current_lap if current_lap is not None else 'None'}/"
            f"{self.m_total_laps if self.m_total_laps is not None else 'None'}",

            f"Current fuel: {current_fuel:.2f} kg" if current_fuel is not None else "Current fuel: None",

            f"Racing fuel rate: {self.m_curr_fuel_rate:.3f} kg/lap"
            if self.m_curr_fuel_rate is not None else "Racing fuel rate: None",

            f"Target fuel rate: {self.m_target_fuel_rate:.3f} kg/lap"
            if self.m_target_fuel_rate is not None else "Target fuel rate: None",

            f"Predicted final fuel: {predicted_fuel:.2f} kg"
            if predicted_fuel is not None else "Predicted final fuel: None",
        ]

        if self.m_surplus_laps is not None:
            result.append(f"Fuel {'surplus' if self.m_surplus_laps >= 0 else 'deficit'}: {abs(self.m_surplus_laps):.2f} laps")

        return "\n".join(result)
