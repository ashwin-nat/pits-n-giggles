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
        self.lap_number = lap_number
        self.fl_tyre_wear = fl_tyre_wear
        self.fr_tyre_wear = fr_tyre_wear
        self.rl_tyre_wear = rl_tyre_wear
        self.rr_tyre_wear = rr_tyre_wear
        self.is_racing_lap = is_racing_lap

class TyreWearExtrapolator:

    def __init__(self, initial_data: List[TyreWearPerLap], total_laps: int):
        """
        Initialize a TyreWearExtrapolator object.

        Args:
            initial_data (List[TyreWearPerLap]): Initial tyre wear data.
            total_laps (int): Total number of laps in the race.
        """
        self.initial_data = initial_data
        self.intervals = self._segment_data(initial_data)
        self.total_laps = total_laps
        self.remaining_laps = total_laps - len(initial_data)
        self._performInitialComputations()

    def _segment_data(self, data: List[TyreWearPerLap]) -> List[List[TyreWearPerLap]]:
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

    def _performInitialComputations(self):
        # Combine all laps, excluding non-racing laps
        racing_data = [point for interval in self.intervals \
                       if all(point.is_racing_lap for point in interval) for point in interval]

        # Fit linear regression model for each tyre using racing data
        self.fl_regression = LinearRegression().fit(
            np.array([point.lap_number for point in racing_data]).reshape(-1, 1),
            np.array([point.fl_tyre_wear for point in racing_data])
        )

        self.fr_regression = LinearRegression().fit(
            np.array([point.lap_number for point in racing_data]).reshape(-1, 1),
            np.array([point.fr_tyre_wear for point in racing_data])
        )

        self.rl_regression = LinearRegression().fit(
            np.array([point.lap_number for point in racing_data]).reshape(-1, 1),
            np.array([point.rl_tyre_wear for point in racing_data])
        )

        self.rr_regression = LinearRegression().fit(
            np.array([point.lap_number for point in racing_data]).reshape(-1, 1),
            np.array([point.rr_tyre_wear for point in racing_data])
        )

    def update_data_list(self, new_data: List[TyreWearPerLap]):
        """
        Update the extrapolator with new data during the race.

        Args:
            new_data (List[TyreWearPerLap]): New tyre wear data.
        """
        self.initial_data.extend(new_data)
        self.intervals = self._segment_data(self.initial_data)
        racing_data = [point for interval in self.intervals \
                       if all(point.is_racing_lap for point in interval) for point in interval]

        if racing_data:
            laps = np.array([point.lap_number for point in racing_data]).reshape(-1, 1)
            self.fl_regression = LinearRegression().fit(
                laps, np.array([point.fl_tyre_wear for point in racing_data])
            )

            self.fr_regression = LinearRegression().fit(
                laps, np.array([point.fr_tyre_wear for point in racing_data])
            )

            self.rl_regression = LinearRegression().fit(
                laps, np.array([point.rl_tyre_wear for point in racing_data])
            )

            self.rr_regression = LinearRegression().fit(
                laps, np.array([point.rr_tyre_wear for point in racing_data])
            )

    def update_data_lap(self, new_data: TyreWearPerLap):
        """
        Update the extrapolator with new data during the race.

        Args:
            new_data (TyreWearPerLap): New tyre wear data.
        """
        self.update_data_list([new_data])


    def extrapolate_tyre_wear(self) -> List[TyreWearPerLap]:
        remaining_tyre_wear: List[TyreWearPerLap] = []

        for lap in range(1, min(self.remaining_laps, self.total_laps - len(self.initial_data)) + 1):
            fl_wear = self.fl_regression.predict([[self.initial_data[-1].lap_number + lap]])[0]
            fr_wear = self.fr_regression.predict([[self.initial_data[-1].lap_number + lap]])[0]
            rl_wear = self.rl_regression.predict([[self.initial_data[-1].lap_number + lap]])[0]
            rr_wear = self.rr_regression.predict([[self.initial_data[-1].lap_number + lap]])[0]

            remaining_tyre_wear.append(TyreWearPerLap(
                lap_number=self.initial_data[-1].lap_number + lap,
                fl_tyre_wear=fl_wear,
                fr_tyre_wear=fr_wear,
                rl_tyre_wear=rl_wear,
                rr_tyre_wear=rr_wear
            ))

        return remaining_tyre_wear

if __name__ == "__main__":
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
    TOTAL_LAPS = 20

    extrapolator = TyreWearExtrapolator(initial_data, TOTAL_LAPS)
    print("Extrapolated tyre wear for remaining laps:")
    remaining_tyre_wear = extrapolator.extrapolate_tyre_wear()
    for point in remaining_tyre_wear:
        print(f"Lap {point.lap_number}: FL {point.fl_tyre_wear}, FR {point.fr_tyre_wear}, RL {point.rl_tyre_wear}, RR {point.rr_tyre_wear}")

    print('-' * 50)
    # Simulate new data arriving during the race
    new_data = [
        TyreWearPerLap(16, 30, 31, 32, 33),
        TyreWearPerLap(17, 32, 33, 34, 35),
        TyreWearPerLap(18, 34, 35, 36, 37),
    ]
    extrapolator.update_data(new_data)

    remaining_tyre_wear = extrapolator.extrapolate_tyre_wear()

    print("Extrapolated tyre wear for remaining laps:")
    for point in remaining_tyre_wear:
        print(f"Lap {point.lap_number}: FL {point.fl_tyre_wear}, FR {point.fr_tyre_wear}, RL {point.rl_tyre_wear}, RR {point.rr_tyre_wear}")
