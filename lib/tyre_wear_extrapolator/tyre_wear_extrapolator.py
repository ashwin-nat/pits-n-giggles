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

import logging
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

    def __init__(
        self,
        initial_data: List[TyreWearPerLap],
        total_laps: int,
        logger: Optional[logging.Logger] = None,
        name: Optional[str] = None,
        window_size: Optional[int] = None,
    ):
        """
        Initialize a TyreWearExtrapolator object.

        Args:
            initial_data (List[TyreWearPerLap]): Initial tyre wear data.
            total_laps (int): Total number of laps in the race.
            logger (Optional[logging.Logger], optional): Logger instance for extrapolator logs.
                If None, a null logger is used.
            name (Optional[str], optional): Name prefix for all extrapolator log lines.
            window_size (Optional[int], optional): Number of most recent racing laps to use
                for regression. Limits the regression to the last N racing laps so the model
                adapts to changing conditions (e.g., weather transitions) instead of averaging
                over the entire stint. None or 0 means use all available data (original behaviour).
        """

        if logger is None:
            logger = logging.getLogger("{__name__}.TyreWearExtrapolator")
            logger.addHandler(logging.NullHandler())
            logger.propagate = False
        self.m_logger = logger
        self.m_name = name if name else self.__class__.__name__
        self.m_window_size: Optional[int] = window_size

        self._initMembers(initial_data, total_laps)

    def _sanitize_regression(self, reg: SimpleLinearRegression) -> None:
        """
        Tyre wear cannot decrease over time.
        """
        if reg is None:
            return

        if reg.slope <= 0.0:
            reg.m = 0.0

    def _clamp_wear(self, predicted: float, current: float) -> float:
        """
        Enforce physical bounds on tyre wear.
        """
        predicted = max(0.0, predicted)
        return max(current, predicted)

    def _warning(self, message: str, *args) -> None:
        """Emit a warning with an extrapolator name prefix."""
        self.m_logger.warning("[%s] " + message, self.m_name, *args)

    def _enforce_tyre_monotonicity(self, prev: TyreWearPerLap, curr: TyreWearPerLap, attr: str, tyre: str) -> None:
        """Clamp one tyre wear attribute to be non-decreasing and log violations."""
        prev_wear = getattr(prev, attr)
        curr_wear = getattr(curr, attr)

        if curr_wear < prev_wear:
            self._warning(
                "Tyre wear monotonicity violated on lap %s for %s: %.3f < %.3f",
                curr.lap_number,
                tyre,
                curr_wear,
                prev_wear,
            )
            setattr(curr, attr, prev_wear)

    def _enforce_monotonicity(self) -> None:
        """
        Ensure predicted wear never decreases lap-to-lap.
        """
        tyre_specs = [
            ("fl_tyre_wear", "FL"),
            ("fr_tyre_wear", "FR"),
            ("rl_tyre_wear", "RL"),
            ("rr_tyre_wear", "RR"),
        ]
        for i in range(1, len(self.m_predicted_tyre_wear)):
            prev = self.m_predicted_tyre_wear[i - 1]
            curr = self.m_predicted_tyre_wear[i]
            for attr, tyre in tyre_specs:
                self._enforce_tyre_monotonicity(prev=prev, curr=curr, attr=attr, tyre=tyre)

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

    @property
    def name(self) -> str:
        return self.m_name

    @name.setter
    def name(self, value: str):
        self.m_name = value

    @property
    def fl_rate(self) -> float:
        """The tyre wear per lap of the front left"""
        return self.m_fl_regression.slope if self.m_fl_regression is not None else 0.0

    @property
    def fr_rate(self) -> float:
        """The tyre wear per lap of the front right"""
        return self.m_fr_regression.slope if self.m_fr_regression is not None else 0.0

    @property
    def rl_rate(self) -> float:
        """The tyre wear per lap of the rear left"""
        return self.m_rl_regression.slope if self.m_rl_regression is not None else 0.0

    @property
    def rr_rate(self) -> float:
        """The tyre wear per lap of the rear right"""
        return self.m_rr_regression.slope if self.m_rr_regression is not None else 0.0

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

    _MIN_WEATHER_SEGMENT_LAPS = 3

    def _filter_to_current_weather(self, racing_data: List[TyreWearPerLap]) -> List[TyreWearPerLap]:
        """Return only the racing laps from the current (most recent) weather group.

        If the current weather segment has fewer than ``_MIN_WEATHER_SEGMENT_LAPS``
        racing laps, all racing data is returned so the sliding window can handle
        the gradual transition.
        """
        if not racing_data:
            return racing_data

        current_group = self._weather_group(racing_data[-1].weather_id)
        if current_group is None:
            return racing_data  # No weather info → use all data

        # Walk backwards to find consecutive laps in the same weather group
        filtered: List[TyreWearPerLap] = []
        for lap in reversed(racing_data):
            if self._weather_group(lap.weather_id) == current_group:
                filtered.append(lap)
            else:
                break
        filtered.reverse()

        if len(filtered) >= self._MIN_WEATHER_SEGMENT_LAPS:
            return filtered

        # Fallback: not enough data for the new weather → use all data
        return racing_data

    def _performRegressions(self, racing_data: List[TyreWearPerLap]):
        """Perform linear regression for all 4 tyres wears

        Args:
            racing_data (List[TyreWearPerLap]): List of all TyreWearPerLap only for racing laps
        """

        # Filter to current weather segment first; fall back to all data
        # when the segment is too short for a stable regression.
        weather_filtered = self._filter_to_current_weather(racing_data)

        # Apply sliding window: when configured, use only the most recent racing
        # laps for the regression.  This lets the model adapt to changing track
        # conditions (e.g. dry→wet or wet→dry transitions) rather than averaging
        # over the entire stint where earlier data may reflect a completely
        # different wear rate.  With window_size=None/0 all data is used
        # (original behaviour).
        if self.m_window_size and len(weather_filtered) > self.m_window_size:
            regression_data = weather_filtered[-self.m_window_size:]
        else:
            regression_data = weather_filtered
        self.m_regression_sample_count = len(regression_data)

        # Use sequential indices (0, 1, 2, ...) instead of actual lap numbers.
        # This prevents gaps from SC periods or low-wear rain laps from
        # diluting the regression slope and producing too-low predictions.
        laps = list(range(len(regression_data)))
        fl_wear = [point.fl_tyre_wear for point in regression_data]
        fr_wear = [point.fr_tyre_wear for point in regression_data]
        rl_wear = [point.rl_tyre_wear for point in regression_data]
        rr_wear = [point.rr_tyre_wear for point in regression_data]

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

        # Enforce physical constraints
        self._sanitize_regression(self.m_fl_regression)
        self._sanitize_regression(self.m_fr_regression)
        self._sanitize_regression(self.m_rl_regression)
        self._sanitize_regression(self.m_rr_regression)

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
        self.m_regression_sample_count: int = 0

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
            # Predict using sequential racing-lap indices then map back to actual lap numbers.
            # The regression was fitted on indices 0..N-1 where N = number of (windowed)
            # data points fed into the regression.
            racing_index_start = self.m_regression_sample_count
            actual_lap_start = self.m_total_laps - self.m_remaining_laps + 1
            for i in range(self.m_remaining_laps):
                racing_index = racing_index_start + i
                actual_lap = actual_lap_start + i
                prev = self.m_predicted_tyre_wear[-1] if self.m_predicted_tyre_wear else self.m_initial_data[-1]

                fl_wear = self._clamp_wear(self.m_fl_regression.predict(racing_index), prev.fl_tyre_wear)
                fr_wear = self._clamp_wear(self.m_fr_regression.predict(racing_index), prev.fr_tyre_wear)
                rl_wear = self._clamp_wear(self.m_rl_regression.predict(racing_index), prev.rl_tyre_wear)
                rr_wear = self._clamp_wear(self.m_rr_regression.predict(racing_index), prev.rr_tyre_wear)

                # Add the predicted tyre wear for the current lap
                predicted_tyre = TyreWearPerLap(
                    fl_tyre_wear=fl_wear,
                    fr_tyre_wear=fr_wear,
                    rl_tyre_wear=rl_wear,
                    rr_tyre_wear=rr_wear,
                    lap_number=actual_lap,
                )
                self.m_predicted_tyre_wear.append(predicted_tyre)
        self._enforce_monotonicity()

    # Weather grouping: Dry (Clear=0, LightCloud=1, Overcast=2) vs Wet (LightRain=3, HeavyRain=4, Storm=5, Thunderstorm=6)
    _DRY_WEATHER_IDS = frozenset({0, 1, 2})

    @staticmethod
    def _weather_group(weather_id: Optional[int]) -> Optional[str]:
        """Map a weather enum value to a coarse group ('dry' or 'wet').

        Returns None when the weather_id is unknown so that legacy data
        without weather information never triggers a segment break.
        """
        if weather_id is None:
            return None
        return "dry" if weather_id in TyreWearExtrapolator._DRY_WEATHER_IDS else "wet"

    def _segmentData(self, data: List[TyreWearPerLap]) -> List[List[TyreWearPerLap]]:
        """
        Segment the data into intervals based on racing mode and weather group.

        A new segment is started whenever the `is_racing_lap` flag changes OR
        the weather group (dry / wet) changes.  This isolates continuous runs
        under the same racing conditions.

        Args:
            data (List[TyreWearPerLap]): List of TyreWearPerLap objects.

        Returns:
            List[List[TyreWearPerLap]]: Segmented intervals, where each interval contains
            laps with the same `is_racing_lap` flag and weather group.
        """

        segment_indices : List[Tuple[int, int]] = []  # Stores (start_index, end_index) of each segment
        is_racing_mode = None                         # Tracks current segment's mode (True/False)
        weather_group = None                          # Tracks current segment's weather group
        curr_start_index = None                       # Start index of the current segment

        for i, point in enumerate(data):
            point_weather_group = self._weather_group(point.weather_id)
            if is_racing_mode is None:
                # This is the first point — initialize the first segment
                is_racing_mode = point.is_racing_lap
                weather_group = point_weather_group
                curr_start_index = i
            else:
                # A new weather group of None (legacy data) never forces a break
                weather_changed = (
                    point_weather_group is not None
                    and weather_group is not None
                    and point_weather_group != weather_group
                )
                if is_racing_mode != point.is_racing_lap or weather_changed:
                    # Close the previous segment
                    segment_indices.append((curr_start_index, i - 1))

                    # Start a new segment
                    curr_start_index = i
                    is_racing_mode = point.is_racing_lap
                    weather_group = point_weather_group
                elif point_weather_group is not None:
                    # Keep tracking the latest known weather group
                    weather_group = point_weather_group

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
