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

from typing import List, Tuple

# ------------------------- CLASS DEFINITIONS --------------------------------------------------------------------------

class SimpleLinearRegression:
    """A simple linear regression class to perform linear regression using least squares method."""

    def __init__(self):
        self.m = 0.0  # Slope
        self.c = 0.0  # Intercept
        self.r2 = 0.0  # R-squared

    def fit(self, x: List[int], y: List[float]) -> None:
        """Fit a simple linear regression model using least squares method

        Args:
            x (List[int]): List of x values
            y (List[float]): List of y values
        """
        if not x or not y:
            raise ValueError("Both x and y must be non-empty lists.")
        if len(x) != len(y):
            raise ValueError("x and y must be of the same length.")

        self.m, self.c = self._compute_m_c(x, y)
        self.r2 = self.score(x, y)

    def predict(self, x: int) -> float:
        """Predict the y value for a given x value using the simple linear regression model."""
        if not isinstance(x, int):
            raise ValueError(f"Expected x to be an int, got {type(x)} instead.")
        return self.m * x + self.c

    def score(self, x: List[int], y: List[float]) -> float:
        """Compute R² (coefficient of determination) for given data.

        Args:
            x (List[int]): Input x values.
            y (List[float]): Actual y values.

        Returns:
            float: R² score (1.0 = perfect fit, 0.0 = no explanatory power).
        """
        if len(x) != len(y) or not x:
            raise ValueError("x and y must be non-empty and of equal length.")

        mean_y = sum(y) / len(y)
        y_pred = [self.predict(xi) for xi in x]

        ss_res = sum((y[i] - y_pred[i]) ** 2 for i in range(len(y)))
        ss_tot = sum((y[i] - mean_y) ** 2 for i in range(len(y)))

        if ss_tot == 0:
            return 1.0 if ss_res == 0 else 0.0  # Edge case: all y values are the same

        return 1 - (ss_res / ss_tot)

    def _compute_m_c(self, x, y) -> Tuple[int, int]:
        """Compute the slope and intercept for a simple linear regression model."""

        if len(x) == 1:  # Special case when there's only one point
            m = 0  # No slope with only one point, or assume a default value
            c = y[0]  # The intercept is just the first y value (starting wear)
        else:
            # Calculate the slope and intercept normally for more than one point
            mean_x = sum(x) / len(x)
            mean_y = sum(y) / len(y)

            numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(len(x)))
            denominator = sum((x[i] - mean_x) ** 2 for i in range(len(x)))

            m = numerator / denominator if denominator != 0 else 0
            c = mean_y - m * mean_x  # Intercept

        return m, c