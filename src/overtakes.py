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

import copy
from typing import List
from enum import Enum, auto
from lib.overtake_analyzer import OvertakeRecord
from src.png_logger import getLogger

# -------------------------------------- GLOBALS -----------------------------------------------------------------------

png_logger = getLogger()

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------

class GetOvertakesStatus(Enum):
    """
    Enum representing the possible statuses of overtakes in a race.

    Attributes:
        RACE_COMPLETED: Indicates that the race is completed.
        RACE_ONGOING: Indicates that the race is still ongoing.
        NO_DATA: Indicates that no overtakes data is available.
        INVALID_INDEX: Indicates that the overtakes data has an invalid index.
    """

    RACE_COMPLETED = auto()
    """Indicates that the race has been completed."""

    RACE_ONGOING = auto()
    """Indicates that the race is still ongoing."""

    NO_DATA = auto()
    """Indicates that there is no data available for overtakes."""

    INVALID_INDEX = auto()
    """Indicates that the overtakes data has an invalid index."""

    def __str__(self) -> str:
        """Return the string representation of the enum member's name."""
        return self.name

class OvertakesHistory:
    """Class representing the history of all overtakes
    """

    def __init__(self):
        """Initialise the overtakes history tracker
        """

        self.m_overtakes_history: List[OvertakeRecord] = []

    def insert(self, overtake_record: OvertakeRecord) -> None:
        """Insert the overtake into the history table. THREAD SAFE

        Args:
            overtake_record (OvertakeRecord): The overtake object
        """

        if len(self.m_overtakes_history) == 0:
            overtake_record.m_row_id = 0
            self.m_overtakes_history.append(overtake_record)
        elif self.m_overtakes_history[-1] == overtake_record:
            png_logger.debug("not adding repeated overtake record %s", str(overtake_record))
        else:
            overtake_record.m_row_id = len(self.m_overtakes_history)
            self.m_overtakes_history.append(overtake_record)

    def clear(self) -> None:
        """Clear the overtakes history tracker
        """

        self.m_overtakes_history.clear()

    def getRecords(self) -> List[OvertakeRecord]:
        """Get the overtake records

        Returns:
            List[OvertakeRecord]: The list of overtake records
        """

        return copy.deepcopy(self.m_overtakes_history)
