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

# ------------------------- IMPORTS ------------------------------------------------------------------------------------

from typing import List, Optional, Tuple

from .simple_linear_regression import SimpleLinearRegression
from .tyre_wear_per_lap import TyreWearPerLap

# ------------------------- CLASS DEFINITIONS --------------------------------------------------------------------------

class TyreWearExtrapolatorPerSegment:
    """Class representing the tyre wear.

    Attributes:
        initial_data (List[TyreWearPerLap]): Initial tyre wear data.
        total_laps (int): Total number of laps in the race.
    """
    def __init__(self, initial_data: List[TyreWearPerLap], total_laps: int):
        """
        Initialize a TyreWearExtrapolatorConfig object.

        Args:
            initial_data (List[TyreWearPerLap]): Initial tyre wear data.
            total_laps (int): Total number of laps in the race.
        """
        self.initial_data = initial_data
        self.total_laps = total_laps

class TyreWearExtrapolator:
    """The tyre wear extrapolator object.

    Attributes:
        m_predicted_tyre_wear (List[TyreWearPerLap]): List of predicted tyre wear per lap. Will be updated whenever
            new data points are added
    """

    def __init__(self, initial_data: List[TyreWearPerLap], total_laps: int):
        """
        Initialize a TyreWearExtrapolator object.

        Args:
            initial_data (List[TyreWearPerLap]): Initial tyre wear data.
            total_laps (int): Total number of laps in the race.
        """

        self._initMembers(initial_data, total_laps)

    def isDataSufficient(self) -> bool:
        """Check if the amount of data available for extrapolation is sufficient.

        Returns:
            bool: True if sufficient
        """

        # m_total_laps, m_remaining_laps will be None in quali, FP. End of race, return insufficient data
        if (self.m_total_laps is None) or (self.m_remaining_laps is None) or (self.m_remaining_laps <= 0):
            return False

        ret_status = len(self.m_racing_data) > 1
        if ret_status:
            assert len(self.m_predicted_tyre_wear) > 0
        return ret_status

    def clear(self) -> None:
        """Clear the tyre wear extrapolator's data
        """

        self._initMembers([], total_laps=self.m_total_laps)

    def getTyreWearPrediction(self, lap_number: Optional[int] = None) -> Optional[TyreWearPerLap]:
        """Get the tyre wear prediction for the specified lap.

        Args:
            lap_number (Optional[int], optional): The lap number. If None, returns the tyre wear prediction for the
                final lap

        Returns:
            Optional[TyreWearPerLap]: The object containing the tyre wear prediction for the specified lap.
                None if the specified lap number is not available
        """
        if lap_number is None:
            return self.m_predicted_tyre_wear[-1]
        return next((point for point in self.m_predicted_tyre_wear if point.lap_number == lap_number), None)

    @property
    def predicted_tyre_wear(self) -> List[TyreWearPerLap]:
        """Generate predicted tyre wear objects

        Returns:
            List[TyreWearPerLap]: The list of object representing the tyre wear per lap
        """
        return self.m_predicted_tyre_wear

    @property
    def total_laps(self) -> int:
        """The total number of laps in the race

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
        if value != self.m_total_laps:
            self.m_total_laps = value
            self._recompute()

    @property
    def remaining_laps(self) -> int:
        """The number of laps remaining in the race

        Returns:
            int: The number of laps remaining in the race
        """
        return self.m_remaining_laps

    def _recompute(self) -> None:
        """Recompute the tyre wear extrapolator
        """

        # This happens in quali/FP
        if self.m_total_laps is None:
            return

        self.m_intervals = self._segmentData(self.m_initial_data)

        # Cache racing data for efficient access
        self.m_racing_data = []
        # Flatten only those intervals where all laps are racing laps
        self._recomputeRacingLapsData()

        if self.m_racing_data:
            self._performRegressions(self.m_racing_data)

    def _updateDataList(self, new_data: List[TyreWearPerLap]):
        """
        Update the extrapolator with new data during the race.

        Args:
            new_data (List[TyreWearPerLap]): New tyre wear data.
        """

        self.m_initial_data.extend(new_data)

        # Recompute intervals and racing data cache
        self.m_intervals = self._segmentData(self.m_initial_data)
        self._recomputeRacingLapsData()
        self._recompute()

    def _performRegressions(self, racing_data: List[TyreWearPerLap]):
        """Perform linear regression for all 4 tyres wears

        Args:
            racing_data (List[TyreWearPerLap]): List of all TyreWearPerLap only for racing laps
        """

        laps = [point.lap_number for point in racing_data]
        fl_wear = [point.fl_tyre_wear for point in racing_data]
        fr_wear = [point.fr_tyre_wear for point in racing_data]
        rl_wear = [point.rl_tyre_wear for point in racing_data]
        rr_wear = [point.rr_tyre_wear for point in racing_data]

        # Initialize the simple linear regression models for each tyre
        self.m_fl_regression = SimpleLinearRegression()
        self.m_fr_regression = SimpleLinearRegression()
        self.m_rl_regression = SimpleLinearRegression()
        self.m_rr_regression = SimpleLinearRegression()

        # Fit each model
        self.m_fl_regression.fit(laps, fl_wear)
        self.m_fr_regression.fit(laps, fr_wear)
        self.m_rl_regression.fit(laps, rl_wear)
        self.m_rr_regression.fit(laps, rr_wear)

        assert self.m_initial_data[-1].lap_number is not None
        assert self.m_total_laps is not None
        self.m_remaining_laps = self.m_total_laps - self.m_initial_data[-1].lap_number
        self._extrapolateTyreWear()

    def add(self, new_data: TyreWearPerLap) -> None:
        """
        Update the extrapolator with new data during the race.

        Args:
            new_data (TyreWearPerLap): New tyre wear data.
        """

        self._updateDataList([new_data])

    def remove(self, laps: List[int]) -> None:
        """Remove the given list of laps from the extrapolator

        Args:
            laps (List[int]): Laps to be removed
        """

        # Remove the laps from the data
        self.m_initial_data = [
            entry for entry in self.m_initial_data
            if entry.lap_number not in laps
        ]
        self._recompute()

    @property
    def num_samples(self) -> int:
        """
        Get the number of samples from the regression models and ensure they are equal before returning the number of samples from the front left regression model.
        """

        return len(self.m_racing_data)

    def _initMembers(self, initial_data: List[TyreWearPerLap], total_laps: int) -> None:
        """Initialise the member variables. Can be called multiple times to reuse the extrapolator object

        Args:
            initial_data (List[TyreWearPerLap]): List of TyreWearPerLap data points. Can be empty
            total_laps (int): The total number of laps in this race (None in quali)
        """

        self.m_initial_data: List[TyreWearPerLap] = initial_data
        self.m_intervals: List[List[TyreWearPerLap]] = self._segmentData(initial_data)
        self.m_total_laps: int = total_laps

        if self.m_initial_data:
            self.m_remaining_laps: int = total_laps - self.m_initial_data[-1].lap_number
        else:
            self.m_remaining_laps: int = total_laps

        self.m_predicted_tyre_wear: List[TyreWearPerLap] = []
        self.m_fl_regression: SimpleLinearRegression = None
        self.m_fr_regression: SimpleLinearRegression = None
        self.m_rl_regression: SimpleLinearRegression = None
        self.m_rr_regression: SimpleLinearRegression = None

        # Cache racing data for efficient access
        self._recomputeRacingLapsData()

        if not self.m_racing_data:
            return

        self._performRegressions(self.m_racing_data)

    def _extrapolateTyreWear(self) -> None:
        """Extrapolate the tyre wear for the remaining laps of the race and stores in m_predicted_tyre_wear
        """

        # No more predictions to do. give the actual data
        if self.m_remaining_laps == 0:
            self.m_predicted_tyre_wear = [self.m_initial_data[-1]]
        else:
            assert self.m_fl_regression is not None
            assert self.m_fr_regression is not None
            assert self.m_rl_regression is not None
            assert self.m_rr_regression is not None

            self.m_predicted_tyre_wear = []
            for lap in range(self.m_total_laps - self.m_remaining_laps + 1, self.m_total_laps + 1):
                fl_wear = self.m_fl_regression.predict(lap)
                fr_wear = self.m_fr_regression.predict(lap)
                rl_wear = self.m_rl_regression.predict(lap)
                rr_wear = self.m_rr_regression.predict(lap)

                # Add the predicted tyre wear for the current lap
                predicted_tyre = TyreWearPerLap(
                    fl_tyre_wear=fl_wear,
                    fr_tyre_wear=fr_wear,
                    rl_tyre_wear=rl_wear,
                    rr_tyre_wear=rr_wear,
                    lap_number=lap,
                )
                self.m_predicted_tyre_wear.append(predicted_tyre)

    def _segmentData(self, data: List[TyreWearPerLap]) -> List[List[TyreWearPerLap]]:
        """
        Segment the data into intervals based on racing mode.

        A new segment is started whenever the `is_racing_lap` flag changes.
        This helps us isolate continuous runs of either racing laps or non-racing laps.

        Args:
            data (List[TyreWearPerLap]): List of TyreWearPerLap objects.

        Returns:
            List[List[TyreWearPerLap]]: Segmented intervals, where each interval contains
            laps with the same `is_racing_lap` flag.
        """

        segment_indices : List[Tuple[int, int]] = []  # Stores (start_index, end_index) of each segment
        is_racing_mode = None                         # Tracks current segment's mode (True/False)
        curr_start_index = None                       # Start index of the current segment

        for i, point in enumerate(data):
            if is_racing_mode is None:
                # This is the first point — initialize the first segment
                is_racing_mode = point.is_racing_lap
                curr_start_index = i
            elif is_racing_mode != point.is_racing_lap:
                # Detected a switch in mode (racing <-> non-racing)
                # Close the previous segment
                segment_indices.append((curr_start_index, i - 1))

                # Start a new segment
                curr_start_index = i
                is_racing_mode = point.is_racing_lap

        # Add the final segment (either first and only, or the tail)
        segment_indices.append((curr_start_index, len(data) - 1))

        # Slice and return the segments
        return [
            data[start_index : end_index + 1]
            for start_index, end_index in segment_indices
        ]

    def _recomputeRacingLapsData(self) -> None:
        """Recompute the racing data cache for efficient access"""
        self.m_racing_data = []
        for interval in self.m_intervals:
            if all(point.is_racing_lap for point in interval):
                self.m_racing_data.extend(interval)
