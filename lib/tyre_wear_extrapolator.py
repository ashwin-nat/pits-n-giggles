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

class LapDataPoint:
    def __init__(self, lap_number: int, fl_tyre_wear: float, fr_tyre_wear: float, rl_tyre_wear: float, rr_tyre_wear: float, is_racing_lap: bool = True):
        """
        Initialize a LapDataPoint object.

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

# class TyreWearExtrapolatorPerSegment:

#     def __init__(self, segment_data: List[LapDataPoint]):
#         """
#         Initialize a TyreWearExtrapolatorPerSegment object.

#         Args:
#             segment_data (List[LapDataPoint]): Segment data.
#         """
#         self.segment_data = segment_data
#         self._performIntialComputations()

#         self.fl_regression =

class TyreWearExtrapolator:
    def __init__(self, initial_data: List[LapDataPoint], total_laps : int):
        """
        Initialize a TyreWearExtrapolator object.

        Args:
            initial_data (List[LapDataPoint]): Initial tyre wear data.
        """
        self.initial_data = initial_data
        self.intervals = self._segment_data(initial_data)
        # self.models_per_segment : List[TyreWearExtrapolatorPerSegment] = []


        self.remaining_laps = total_laps - len(initial_data)
        self._performIntialComputations()

    def _segment_data(self, data: List[LapDataPoint]) -> List[List[LapDataPoint]]:
        """
        Segment the data into intervals based on racing laps.

        Args:
            data (List[LapDataPoint]): List of LapDataPoint objects.

        Returns:
            List[List[LapDataPoint]]: Segmented intervals.
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

    def _performIntialComputations(self):
        # Combine all laps, excluding non-racing laps
        racing_data = [point for interval in self.intervals if all(point.is_racing_lap for point in interval) for point in interval]

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



    def extrapolate_tyre_wear(self) -> List[LapDataPoint]:

        remaining_tyre_wear : List[LapDataPoint] = []

        for lap in range(1, self.remaining_laps + 1):
            fl_wear = self.fl_regression.predict([[15 + lap]])[0]  # Predict for lap 16 and onwards
            fr_wear = self.fr_regression.predict([[15 + lap]])[0]
            rl_wear = self.rl_regression.predict([[15 + lap]])[0]
            rr_wear = self.rr_regression.predict([[15 + lap]])[0]

            remaining_tyre_wear.append(LapDataPoint(
                lap_number=len(self.initial_data) + lap,
                fl_tyre_wear=fl_wear,
                fr_tyre_wear=fr_wear,
                rl_tyre_wear=rl_wear,
                rr_tyre_wear=rr_wear
            ))

        return remaining_tyre_wear



# Example usage
initial_data = [
    LapDataPoint(1, 10, 11, 12, 13),
    LapDataPoint(2, 12, 13, 14, 15),
    LapDataPoint(3, 15, 16, 17, 18),
    LapDataPoint(4, 18, 19, 20, 21),
    LapDataPoint(5, 20, 21, 22, 23),
    LapDataPoint(6, 22, 23, 24, 25, is_racing_lap=False),  # Safety car lap
    LapDataPoint(7, 22, 23, 24, 25, is_racing_lap=False),  # Safety car lap
    LapDataPoint(8, 22, 23, 24, 25, is_racing_lap=False),  # Safety car lap
    LapDataPoint(9, 23, 24, 25, 26),
    LapDataPoint(10, 24, 25, 26, 27),
    LapDataPoint(11, 25, 26, 27, 28),
    LapDataPoint(12, 26, 27, 28, 29),
    LapDataPoint(13, 27, 28, 29, 30),
    LapDataPoint(14, 28, 29, 30, 31),
    LapDataPoint(15, 29, 30, 31, 32)
]  # Sample initial tyre wear data for the first 15 laps
TOTAL_LAPS = 20

extrapolator = TyreWearExtrapolator(initial_data, TOTAL_LAPS)
remaining_tyre_wear = extrapolator.extrapolate_tyre_wear()

print("Extrapolated tyre wear for remaining laps:")
for point in remaining_tyre_wear:
    print(f"Lap {point.lap_number}: FL {point.fl_tyre_wear}, FR {point.fr_tyre_wear}, RL {point.rl_tyre_wear}, RR {point.rr_tyre_wear}")
