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

from enum import Enum
from typing import Any, Dict

class WarningPenaltyEntry:
    """
    Class that captures one warning/penalty entry
    """
    class EntryType(Enum):
        """
        Enum representing the type of warning/penalty entry
        """
        CORNER_CUTTING_WARNING = 0
        DT_PENALTY = 1
        SG_PENALTY = 2
        OTHER_WARNING = 3
        TIME_PENALTY = 4

        @staticmethod
        def isValid(entry_type_code: int) -> bool:
            """
            Check if the entry type is valid

            Args:
                entry_type_code (int): The entry type code to check

            Returns:
                bool: True if the entry type is valid
            """

            if isinstance(entry_type_code, WarningPenaltyEntry.EntryType):
                return True  # It's already an instance of EntryType
            return any(entry_type_code == member.value for member in  WarningPenaltyEntry.EntryType)

        def __str__(self) -> str:
            """
            Get the name of the entry type

            Returns:
                str: The name of the entry type
            """
            return self.name.replace('_', ' ').title()

    def __init__(self,
                    entry_type: EntryType,
                    old_value: int,
                    new_value: int,
                    lap_num: int,
                    sector_number: int,
                    distance_from_start: float,
                    lap_progress_percent: float) -> None:

        """
        Init the warning/penalty entry

        Args:
            entry_type (EntryType): The entry type
            old_value (int): The old value of the entry
            new_value (int): The new value of the entry
            lap_number (int): The lap number
            sector_number (int): The sector number
            distance_from_start (float): The distance from start
            lap_progress_percent (float): The lap progress percent
        """

        assert old_value != new_value
        self.m_entry_type: WarningPenaltyEntry.EntryType = entry_type
        self.m_old_value: int = old_value
        self.m_new_value: int = new_value
        self.m_lap_number: int = lap_num
        self.m_sector_number: int = sector_number
        self.m_distance_from_start: float = distance_from_start
        self.m_lap_progress_percent: float = lap_progress_percent

    def toJSON(self) -> Dict[str, Any]:
        """
        Dump this object into JSON

        Returns:
            Dict[str, Any]: The JSON dump
        """
        return {
            "entry-type" : str(self.m_entry_type),
            "old-value" : self.m_old_value,
            "new-value" : self.m_new_value,
            "lap-number" : self.m_lap_number,
            "sector-number" : str(self.m_sector_number),
            "distance-from-start" : self.m_distance_from_start,
            "lap-progress-percent" : self.m_lap_progress_percent
        }

    def __repr__(self) -> str:
        """Return the string representation of this object

        Returns:
            str: string representation of this object
        """
        return  f"entry_type: {self.m_entry_type} " \
                f"new_value: {self.m_new_value} " \
                f"lap: {self.m_lap_number} " \
                f"sector: {self.m_sector_number}"

    def __str__(self) -> str:
        """Return the string representation of this object

        Returns:
            str: string representation of this object
        """
        return self.__repr__()
