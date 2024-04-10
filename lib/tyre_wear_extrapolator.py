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

from typing import List, Tuple
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
        is_racing_lap: bool = True):
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
        self.lap_number     = lap_number
        self.fl_tyre_wear   = fl_tyre_wear
        self.fr_tyre_wear   = fr_tyre_wear
        self.rl_tyre_wear   = rl_tyre_wear
        self.rr_tyre_wear   = rr_tyre_wear
        self.is_racing_lap  = is_racing_lap

    def __str__(self) -> str:
        """
        Returns a string representation of the TyreWearPerLap object.
        """
        return (
            f"Lap {self.lap_number}: "
            f"FL {self.fl_tyre_wear}, "
            f"FR {self.fr_tyre_wear}, "
            f"RL {self.rl_tyre_wear}, "
            f"RR {self.rr_tyre_wear}"
        )

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
        self.m_initial_data : List[TyreWearPerLap] = initial_data
        self.m_intervals : List[List[TyreWearPerLap]] = self._segmentData(initial_data)
        self.total_laps : int = total_laps
        self.remaining_laps : int = total_laps - len(initial_data)
        self.m_predicted_tyre_wear: List[TyreWearPerLap] = []
        self.m_fl_regression : LinearRegression = None
        self.m_fr_regression : LinearRegression = None
        self.m_rl_regression : LinearRegression = None
        self.m_rr_regression : LinearRegression = None
        self._performInitialComputations()

    def isDataSufficient(self) -> bool:
        """Check if the amount of data available for extrapolation is sufficient.

        Returns:
            bool: True if sufficient
        """

        racing_data = [point for interval in self.m_intervals \
                       if all(point.is_racing_lap for point in interval) for point in interval]
        ret_status = (len(racing_data) > 1)
        if ret_status:
            assert len(self.m_predicted_tyre_wear) > 0
        return ret_status

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

            self.m_predicted_tyre_wear = self._extrapolateTyreWear()

    def updateDataLap(self, new_data: TyreWearPerLap):
        """
        Update the extrapolator with new data during the race.

        Args:
            new_data (TyreWearPerLap): New tyre wear data.
        """

        self.updateDataList([new_data])

    def _extrapolateTyreWear(self) -> List[TyreWearPerLap]:
        """Extrapolate the tyre wear for the remaining laps of the race

        Returns:
            List[TyreWearPerLap]: List of TyreWearPerLap objects containing predicted tyre wear
                    at the end of the each lap till the end of the race
        """

        assert self.m_fl_regression is not None
        assert self.m_fr_regression is not None
        assert self.m_rl_regression is not None
        assert self.m_rr_regression is not None

        remaining_tyre_wear: List[TyreWearPerLap] = []
        for lap in range(1, min(self.remaining_laps, self.total_laps - len(self.m_initial_data)) + 1):
            fl_wear = self.m_fl_regression.predict([[self.m_initial_data[-1].lap_number + lap]])[0]
            fr_wear = self.m_fr_regression.predict([[self.m_initial_data[-1].lap_number + lap]])[0]
            rl_wear = self.m_rl_regression.predict([[self.m_initial_data[-1].lap_number + lap]])[0]
            rr_wear = self.m_rr_regression.predict([[self.m_initial_data[-1].lap_number + lap]])[0]

            remaining_tyre_wear.append(TyreWearPerLap(
                lap_number=self.m_initial_data[-1].lap_number + lap,
                fl_tyre_wear=fl_wear,
                fr_tyre_wear=fr_wear,
                rl_tyre_wear=rl_wear,
                rr_tyre_wear=rr_wear
            ))

        return remaining_tyre_wear

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

    def _performInitialComputations(self) -> None:
        """Initialise the regression models for each tyre
        """
        # TODO: remove this function

        # Can't init the data models if the
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
        self.m_predicted_tyre_wear = self._extrapolateTyreWear()


if __name__ == "__main__":

    # Empty extrapolator
    TOTAL_LAPS = 20
    empty_extrapolator = TyreWearExtrapolator([], TOTAL_LAPS)
    print("empty object")
    empty_extrapolator.updateDataLap(TyreWearPerLap(1, 2, 2, 2, 2, is_racing_lap=True))
    print("After 1 lap. is sufficient: " + str(empty_extrapolator.isDataSufficient()))
    empty_extrapolator.updateDataLap(TyreWearPerLap(2, 4, 4, 4, 4, is_racing_lap=True))
    empty_remaining_tyre_wear = empty_extrapolator.m_predicted_tyre_wear
    for point in empty_remaining_tyre_wear:
        print(str(point))
    print('-' * 50)

    # Example usage
    initial_data = [
        TyreWearPerLap(1, 10, 11, 12, 13),
        TyreWearPerLap(2, 12, 13, 14, 15),
        TyreWearPerLap(3, 15, 16, 17, 18),
        TyreWearPerLap(4, 18, 19, 20, 21),
        TyreWearPerLap(5, 20, 21, 22, 23),
        TyreWearPerLap(6, 22, 23, 24, 25, is_racing_lap=False),  # Safety car lap
        TyreWearPerLap(7, 22, 23, 24, 25, is_racing_lap=False),  # Safety car lap
        TyreWearPerLap(8, 22, 23, 24, 25, is_racing_lap=False),  # Safety car lap
        TyreWearPerLap(9, 23, 24, 25, 26),
        TyreWearPerLap(10, 24, 25, 26, 27),
        TyreWearPerLap(11, 25, 26, 27, 28),
        TyreWearPerLap(12, 26, 27, 28, 29),
        TyreWearPerLap(13, 27, 28, 29, 30),
        TyreWearPerLap(14, 28, 29, 30, 31),
        TyreWearPerLap(15, 29, 30, 31, 32)
    ]  # Sample initial tyre wear data for the first 15 laps

    extrapolator = TyreWearExtrapolator(initial_data, TOTAL_LAPS)
    print("Predictions based on initial data")
    print("Extrapolated tyre wear for remaining laps:")
    # remaining_tyre_wear = extrapolator.extrapolateTyreWear()
    remaining_tyre_wear = extrapolator.m_predicted_tyre_wear
    for point in remaining_tyre_wear:
        # print(f"Lap {point.lap_number}: FL {point.fl_tyre_wear}, FR {point.fr_tyre_wear}, RL {point.rl_tyre_wear}, RR {point.rr_tyre_wear}")
        print(str(point))

    print('-' * 50)
    # Simulate new data arriving during the race
    # new_data = [
    #     TyreWearPerLap(16, 30, 31, 32, 33),
    #     TyreWearPerLap(17, 32, 33, 34, 35),
    #     TyreWearPerLap(18, 34, 35, 36, 37),
    # ]
    # extrapolator.updateDataList(new_data)

    # remaining_tyre_wear = extrapolator.extrapolateTyreWear()

    # print("Extrapolated tyre wear for remaining laps:")
    # for point in remaining_tyre_wear:
    #     print(f"Lap {point.lap_number}: FL {point.fl_tyre_wear}, FR {point.fr_tyre_wear}, RL {point.rl_tyre_wear}, RR {point.rr_tyre_wear}")

    new_data = [
        TyreWearPerLap(16, 30, 31, 32, 33, is_racing_lap=False),
        TyreWearPerLap(17, 32, 33, 34, 35, is_racing_lap=False),
        TyreWearPerLap(18, 34, 35, 36, 37, is_racing_lap=False),
    ]

    for lap_data in new_data:
        extrapolator.updateDataLap(lap_data)
        # remaining_tyre_wear = extrapolator.extrapolateTyreWear()
        remaining_tyre_wear = extrapolator.m_predicted_tyre_wear
        print("Last lap number: " + str(lap_data.lap_number))
        print("Extrapolated tyre wear for remaining laps:")
        for point in remaining_tyre_wear:
            # print(f"Lap {point.lap_number}: FL {point.fl_tyre_wear}, FR {point.fr_tyre_wear}, RL {point.rl_tyre_wear}, RR {point.rr_tyre_wear}")
            print(str(point))
        print('-' * 50)

    zero_lap_extrapolator = TyreWearExtrapolator([], 0)
    print("is sufficient = " + str(zero_lap_extrapolator.isDataSufficient()))
