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

from typing import Any, Dict, List, Optional, Tuple

class SimpleLinearRegression:
    """A simple linear regression class to perform linear regression using least squares method."""

    def __init__(self):
        self.m = 0.0  # Slope
        self.c = 0.0  # Intercept

    def fit(self, x: List[int], y: List[float]) -> None:
        """Fit a simple linear regression model using least squares method

        Args:
            x (List[int]): List of x values
            y (List[float]): List of y values
        """
        if not x or not y:
            raise ValueError("Both x and y must be non-empty lists.")

        if len(x) == 1:  # Special case when there's only one point
            self.m = 0  # No slope with only one point, or assume a default value
            self.c = y[0]  # The intercept is just the first y value (starting wear)
        else:
            # Calculate the slope and intercept normally for more than one point
            mean_x = sum(x) / len(x)
            mean_y = sum(y) / len(y)

            numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(len(x)))
            denominator = sum((x[i] - mean_x) ** 2 for i in range(len(x)))

            self.m = numerator / denominator if denominator != 0 else 0
            self.c = mean_y - self.m * mean_x  # Intercept

    def predict(self, x: int) -> float:
        """Predict the y value for a given x value using the simple linear regression model."""
        if not isinstance(x, int):
            raise ValueError(f"Expected x to be an int, got {type(x)} instead.")
        return self.m * x + self.c

class TyreWearPerLap:
    """Class representing the tyre wear percentage per lap.

    Attributtes:
        lap_number (int): Lap number.
        fl_tyre_wear (float): Front left tyre wear percentage.
        fr_tyre_wear (float): Front right tyre wear percentage.
        rl_tyre_wear (float): Rear left tyre wear percentage.
        rr_tyre_wear (float): Rear right tyre wear percentage.
        is_racing_lap (bool): Whether it's a racing lap or not. (non SC/VSC lap)
    """
    def __init__(self,
        fl_tyre_wear: float,
        fr_tyre_wear: float,
        rl_tyre_wear: float,
        rr_tyre_wear: float,
        lap_number: Optional[int] = None,
        is_racing_lap: Optional[bool] = True,
        desc: Optional[str] = None):
        """
        Initialize a TyreWearPerLap object.

        Args:
            fl_tyre_wear (float): Front left tyre wear percentage.
            fr_tyre_wear (float): Front right tyre wear percentage.
            rl_tyre_wear (float): Rear left tyre wear percentage.
            rr_tyre_wear (float): Rear right tyre wear percentage.
            lap_number (int, optional): Lap number. Defaults to None.
            is_racing_lap (bool, optional): Whether it's a racing lap or not. Defaults to True.
            desc (str, optional): Description of the lap. Defaults to None.
        """
        self.lap_number: int        = lap_number
        self.fl_tyre_wear: float    = fl_tyre_wear
        self.fr_tyre_wear: float    = fr_tyre_wear
        self.rl_tyre_wear: float    = rl_tyre_wear
        self.rr_tyre_wear: float    = rr_tyre_wear
        self.is_racing_lap: bool    = is_racing_lap
        self.m_desc: Optional[str]  = desc

    def __str__(self) -> str:
        """
        Returns a string representation of the TyreWearPerLap object.
        """
        return (
            f"Lap {str(self.lap_number)}: "
            f"FL {self.fl_tyre_wear}, "
            f"FR {self.fr_tyre_wear}, "
            f"RL {self.rl_tyre_wear}, "
            f"RR {self.rr_tyre_wear}, "
            f"Average {self.m_average}, "
            f"Desc: {str(self.m_desc)}"
        )

    @property
    def m_average(self) -> float:
        """
        Return the average tyre wear by calculating the sum of all tyre wears and dividing by 4.
        """
        return (self.fl_tyre_wear + self.fr_tyre_wear + self.rl_tyre_wear + self.rr_tyre_wear) / 4.0

    def toJSON(self) -> Dict[str, Any]:
        """
        Return a dictionary representing the object in JSON format.

        Returns:
            Dict[str, Any]: The JSON representation of the object.
        """

        return {
            "lap-number": self.lap_number,
            "front-left-wear": self.fl_tyre_wear,
            "front-right-wear": self.fr_tyre_wear,
            "rear-left-wear": self.rl_tyre_wear,
            "rear-right-wear": self.rr_tyre_wear,
            "average" : self.m_average,
            "desc" : self.m_desc
        }

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

        racing_data = [point for interval in self.m_intervals \
                       if all(point.is_racing_lap for point in interval) for point in interval]
        ret_status = (len(racing_data) > 1)
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

        # This happens in quali
        if self.m_total_laps is None:
            return

        # Recompute the segments
        self.m_intervals = self._segmentData(self.m_initial_data)
        racing_data = [point for interval in self.m_intervals \
                           if all(point.is_racing_lap for point in interval) for point in interval]

        # Recompute the regression models
        if racing_data:
            self._performRegressions(racing_data)

    def _updateDataList(self, new_data: List[TyreWearPerLap]):
        """
        Update the extrapolator with new data during the race.

        Args:
            new_data (List[TyreWearPerLap]): New tyre wear data.
        """

        self.m_initial_data.extend(new_data)
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
        assert self.m_fl_regression is not None
        assert self.m_fr_regression is not None
        assert self.m_rl_regression is not None
        assert self.m_rr_regression is not None

        return len(self.m_initial_data)

    def _initMembers(self, initial_data: List[TyreWearPerLap], total_laps: int) -> None:
        """Initialise the member variables. Can be called multiple times to reuse the extrapolator object

        Args:
            initial_data (List[TyreWearPerLap]): List of TyreWearPerLap data points. Can be empty
            total_laps (int): The total number of laps in this race (None in quali)
        """

        self.m_initial_data : List[TyreWearPerLap] = initial_data
        self.m_intervals : List[List[TyreWearPerLap]] = self._segmentData(initial_data)
        self.m_total_laps : int = total_laps
        if self.m_initial_data:
            self.m_remaining_laps : int = total_laps - self.m_initial_data[-1].lap_number
        else:
            self.m_remaining_laps : int = total_laps
        self.m_predicted_tyre_wear: List[TyreWearPerLap] = []
        self.m_fl_regression : SimpleLinearRegression = None
        self.m_fr_regression : SimpleLinearRegression = None
        self.m_rl_regression : SimpleLinearRegression = None
        self.m_rr_regression : SimpleLinearRegression = None

        # Can't init the data models if there is no data
        if not self.m_initial_data:
            return

        # Combine all laps, excluding non-racing laps
        racing_data = [point for interval in self.m_intervals \
                           if all(point.is_racing_lap for point in interval) for point in interval]
        self._performRegressions(racing_data)

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
        Segment the data into intervals based on racing laps.

        Args:
            data (List[TyreWearPerLap]): List of TyreWearPerLap objects.

        Returns:
            List[List[TyreWearPerLap]]: Segmented intervals.
        """

        segment_indices : List[Tuple[int, int]] = []
        is_racing_mode = None
        curr_start_index = None

        for i, point in enumerate(data):
            if is_racing_mode is None:
                is_racing_mode = point.is_racing_lap
                curr_start_index = i
            elif is_racing_mode != point.is_racing_lap:
                segment_indices.append((curr_start_index, i-1))
                curr_start_index = i
                is_racing_mode = point.is_racing_lap
        segment_indices.append((curr_start_index, len(data)-1))

        return [
            data[start_index : end_index + 1]
            for start_index, end_index in segment_indices
        ]
