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

from typing import List, Tuple, Optional, Dict, Any
try:
    from sklearn.linear_model import LinearRegression
except ImportError:
    print("scikit-learn is not installed. Installing...")
    import subprocess
    subprocess.check_call(["pip3", "install", "scikit-learn"])
    print("scikit-learn installation complete.")
    from sklearn.linear_model import LinearRegression
import numpy as np

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
        lap_number: int,
        fl_tyre_wear: float,
        fr_tyre_wear: float,
        rl_tyre_wear: float,
        rr_tyre_wear: float,
        is_racing_lap: bool = True,
        desc: Optional[str] = None):
        """
        Initialize a TyreWearPerLap object.

        Args:
            lap_number (int): Lap number.
            fl_tyre_wear (float): Front left tyre wear percentage.
            fr_tyre_wear (float): Front right tyre wear percentage.
            rl_tyre_wear (float): Rear left tyre wear percentage.
            rr_tyre_wear (float): Rear right tyre wear percentage.
            is_racing_lap (bool, optional): Whether it's a racing lap or not. Defaults to True.
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
            f"Lap {self.lap_number}: "
            f"FL {self.fl_tyre_wear}, "
            f"FR {self.fr_tyre_wear}, "
            f"RL {self.rl_tyre_wear}, "
            f"RR {self.rr_tyre_wear}, "
            f"Average {self.m_average}"
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

        # m_total_laps will be None in quali
        if self.m_total_laps is None:
            return False

        racing_data = [point for interval in self.m_intervals \
                       if all(point.is_racing_lap for point in interval) for point in interval]
        ret_status = (len(racing_data) > 1)
        if ret_status and (self.m_remaining_laps > 0):
            assert len(self.m_predicted_tyre_wear) > 0
        return ret_status

    def clear(self) -> None:
        """Clear the tyre wear extrapolator's data
        """

        self._initMembers([], total_laps=self.m_total_laps)

    def getTyreWearPrediction(self, lap_number: Optional[int] = None) -> TyreWearPerLap:
        """Get the tyre wear prediction for the specified lap.

        Args:
            lap_number (Optional[int], optional): The lap number. If None, returns the tyre wear prediction for the
                final lap

        Raises:
            IndexError: If the specified lap number is not available. Usually happens if the lap number is not within
                the range of available laps, or if data is not sufficient

        Returns:
            TyreWearPerLap: The object containing the tyre wear prediction for the specified lap
        """
        if lap_number is None:
            return self.m_predicted_tyre_wear[-1]
        else:
            for point in self.m_predicted_tyre_wear:
                if point.lap_number == lap_number:
                    return point

            raise IndexError("Lap number " + str(lap_number) + "not found. Max lap number is " +
                             str(self.m_predicted_tyre_wear[-1].lap_number))

    @property
    def predicted_tyre_wear(self) -> List[TyreWearPerLap]:
        """The list of predicted tyre wear

        Returns:
            List[TyreWearPerLap]: The list of objects representing the tyre wear per lap
        """
        return self.m_predicted_tyre_wear

    @property
    def total_laps(self) -> int:
        """The total number of laps in the race

        Returns:
            int: The total number of laps in the race
        """
        return self.m_total_laps

    def updateDataList(self, new_data: List[TyreWearPerLap]):
        """
        Update the extrapolator with new data during the race.

        Args:
            new_data (List[TyreWearPerLap]): New tyre wear data.
        """
        self.m_initial_data.extend(new_data)
        self.m_intervals = self._segmentData(self.m_initial_data)
        racing_data = [point for interval in self.m_intervals \
                       if all(point.is_racing_lap for point in interval) for point in interval]

        if racing_data:
            laps = np.array([point.lap_number for point in racing_data]).reshape(-1, 1)
            self.m_fl_regression = LinearRegression().fit(
                laps, np.array([point.fl_tyre_wear for point in racing_data])
            )

            self.m_fr_regression = LinearRegression().fit(
                laps, np.array([point.fr_tyre_wear for point in racing_data])
            )

            self.m_rl_regression = LinearRegression().fit(
                laps, np.array([point.rl_tyre_wear for point in racing_data])
            )

            self.m_rr_regression = LinearRegression().fit(
                laps, np.array([point.rr_tyre_wear for point in racing_data])
            )

            assert self.m_initial_data[-1].lap_number is not None
            assert self.m_total_laps is not None
            self.m_remaining_laps = self.m_total_laps - self.m_initial_data[-1].lap_number
            self._extrapolateTyreWear()

    def updateDataLap(self, new_data: TyreWearPerLap):
        """
        Update the extrapolator with new data during the race.

        Args:
            new_data (TyreWearPerLap): New tyre wear data.
        """

        self.updateDataList([new_data])

    def getNumSamples(self) -> int:
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
        self.m_fl_regression : LinearRegression = None
        self.m_fr_regression : LinearRegression = None
        self.m_rl_regression : LinearRegression = None
        self.m_rr_regression : LinearRegression = None

        # Can't init the data models if there is no data
        if len(self.m_initial_data) == 0:
            return

        # Combine all laps, excluding non-racing laps
        racing_data = [point for interval in self.m_intervals \
                       if all(point.is_racing_lap for point in interval) for point in interval]

        # Fit linear regression model for each tyre using racing data
        self.m_fl_regression = LinearRegression().fit(
            np.array([point.lap_number for point in racing_data]).reshape(-1, 1),
            np.array([point.fl_tyre_wear for point in racing_data])
        )
        self.m_fr_regression = LinearRegression().fit(
            np.array([point.lap_number for point in racing_data]).reshape(-1, 1),
            np.array([point.fr_tyre_wear for point in racing_data])
        )
        self.m_rl_regression = LinearRegression().fit(
            np.array([point.lap_number for point in racing_data]).reshape(-1, 1),
            np.array([point.rl_tyre_wear for point in racing_data])
        )
        self.m_rr_regression = LinearRegression().fit(
            np.array([point.lap_number for point in racing_data]).reshape(-1, 1),
            np.array([point.rr_tyre_wear for point in racing_data])
        )

        # Update the predicted tyre wear data structure
        self._extrapolateTyreWear()

    def _extrapolateTyreWear(self) -> List[TyreWearPerLap]:
        """Extrapolate the tyre wear for the remaining laps of the race

        Returns:
            List[TyreWearPerLap]: List of TyreWearPerLap objects containing predicted tyre wear
                    at the end of the each lap till the end of the race
        """

        # No more predictions to do. give the actual data
        if self.m_remaining_laps == 0:
            self.m_predicted_tyre_wear = [self.m_initial_data[-1]]

        else:
            assert self.m_fl_regression is not None
            assert self.m_fr_regression is not None
            assert self.m_rl_regression is not None
            assert self.m_rr_regression is not None

            self.m_predicted_tyre_wear: List[TyreWearPerLap] = []
            for lap in range(self.m_total_laps-self.m_remaining_laps+1, self.m_total_laps+1):
                fl_wear = self.m_fl_regression.predict([[lap]])[0]
                fr_wear = self.m_fr_regression.predict([[lap]])[0]
                rl_wear = self.m_rl_regression.predict([[lap]])[0]
                rr_wear = self.m_rr_regression.predict([[lap]])[0]

                self.m_predicted_tyre_wear.append(TyreWearPerLap(
                    lap_number=lap,
                    fl_tyre_wear=fl_wear,
                    fr_tyre_wear=fr_wear,
                    rl_tyre_wear=rl_wear,
                    rr_tyre_wear=rr_wear
                ))


    def _segmentData(self, data: List[TyreWearPerLap]) -> List[List[TyreWearPerLap]]:
        """
        Segment the data into intervals based on racing laps.

        Args:
            data (List[TyreWearPerLap]): List of TyreWearPerLap objects.

        Returns:
            List[List[TyreWearPerLap]]: Segmented intervals.
        """

        intervals = []
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

        for start_index, end_index in segment_indices:
            intervals.append(data[start_index:end_index+1])

        return intervals
