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

from collections import deque
from typing import Deque, Generic, Iterator, Optional, TypeVar

# -------------------------------------- TYPES -------------------------------------------------------------------------

T = TypeVar("T")

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

class RollingHistory(Generic[T]):
    """
    Fixed-size rolling history of values.

    Maintains the last `maxlen` values pushed into the history.
    When the capacity is exceeded, the oldest values are discarded
    automatically.

    This class is intentionally simple:
    - No timestamps
    - No derived statistics
    - No internal locking (caller manages concurrency)

    Typical use cases:
    - Telemetry smoothing
    - Change detection
    - Short-term trend analysis
    """

    def __init__(self, maxlen: int) -> None:
        """
        Create a new rolling history.

        Args:
            maxlen: Maximum number of values to retain.

        Raises:
            ValueError: If maxlen is not greater than zero.
        """
        if maxlen <= 0:
            raise ValueError("maxlen must be greater than zero")

        self._data: Deque[T] = deque(maxlen=maxlen)

    def push(self, value: T) -> None:
        """
        Add a new value to the history.

        If the history is already full, the oldest value is discarded.
        """
        self._data.append(value)

    @property
    def latest(self) -> Optional[T]:
        """
        Return the most recently added value.

        Returns:
            The latest value, or None if the history is empty.
        """
        return self._data[-1] if self._data else None

    def values(self) -> list[T]:
        """
        Return all stored values in chronological order.

        Returns:
            A list of values from oldest to newest.
        """
        return list(self._data)

    def clear(self) -> None:
        """Remove all stored values."""
        self._data.clear()

    def __len__(self) -> int:
        """Return the number of stored values."""
        return len(self._data)

    def __iter__(self) -> Iterator[T]:
        """Iterate over values from oldest to newest."""
        return iter(self._data)

    def __bool__(self) -> bool:
        """
        Return True if at least one value exists.

        Enables:
            if history:
                ...
        """
        return bool(self._data)
