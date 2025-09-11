# MIT License
#
# Copyright (c) [2025] [Ashwin Natarajan]
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

from typing import List

from .messages import RaceControlMessage

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class DriverRaceControlManager:
    """
    Manager for race control messages specific to a single driver.

    Attributes:
        driver_index (int): Unique identifier of the driver.
        messages (List[RaceControlMessage]): References to messages involving this driver.
    """

    def __init__(self, driver_index: int) -> None:
        self.driver_index: int = driver_index
        self.messages: List[RaceControlMessage] = []

    def add_message(self, message: RaceControlMessage) -> None:
        """Register a message reference if the driver is involved."""
        self.messages.append(message)

    def clear(self) -> None:
        """Clear all stored messages for this driver."""
        self.messages.clear()
