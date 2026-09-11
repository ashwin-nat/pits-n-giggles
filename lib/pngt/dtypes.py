# MIT License
#
# Copyright (c) [2026] [Ashwin Natarajan]
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

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

from enum import Enum

import numpy as np

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class SensorDtype(Enum):
    """NumPy dtype a sensor's telemetry values are stored as in a lap's .npz file."""
    FLOAT32 = "float32"
    INT8 = "int8"
    INT16 = "int16"
    INT64 = "int64"

# -------------------------------------- CONSTANTS ----------------------------------------------------------------------

_NUMPY_DTYPES = {
    SensorDtype.FLOAT32: np.float32,
    SensorDtype.INT8: np.int8,
    SensorDtype.INT16: np.int16,
    SensorDtype.INT64: np.int64,
}

_MISSING_VALUES = {
    SensorDtype.FLOAT32: np.nan,
    SensorDtype.INT8: -1,
    SensorDtype.INT16: -1,
    SensorDtype.INT64: -1,
}

# -------------------------------------- FUNCTIONS ----------------------------------------------------------------------

def numpy_dtype(dtype: SensorDtype) -> np.dtype:
    """Returns the NumPy dtype used to store this sensor's values in a lap's .npz file."""
    return np.dtype(_NUMPY_DTYPES[dtype])

def missing_value(dtype: SensorDtype):
    """Returns the sentinel value used to mark a missing sample for this dtype (nan for
    float32, -1 for integer dtypes)."""
    return _MISSING_VALUES[dtype]
