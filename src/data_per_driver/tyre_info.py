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

from lib.f1_types import VisualTyreCompound, ActualTyreCompound
from lib.tyre_wear_extrapolator import TyreWearPerLap
from typing import Dict, List, Any, Optional

class TyreSetInfo:
    """
    Class that models the data describing a tyre set.

    Attributes:
        m_actual_tyre_compound (ActualTyreCompound): The actual compound of the tyre.
        m_visual_tyre_compound (VisualTyreCompound): The visual compound of the tyre.
        m_tyre_set_id (int): The ID of the tyre set.
        m_tyre_age_laps (int): The age of the tyre in laps.
    """
    def __init__(self,
                    actual_tyre_compound: ActualTyreCompound,
                    visual_tyre_compound: VisualTyreCompound,
                    tyre_set_id: int,
                    tyre_age_laps: int):

        self.m_actual_tyre_compound = actual_tyre_compound
        self.m_visual_tyre_compound = visual_tyre_compound
        self.m_tyre_set_id = tyre_set_id
        self.m_tyre_age_laps = tyre_age_laps

    def toJSON(self) -> Dict[str, Any]:
        """Get the JSON representation of this object

        Returns:
            Dict[str, Any]: The JSON representation
        """
        return {
            'actual-tyre-compound': str(self.m_actual_tyre_compound),
            'visual-tyre-compound': str(self.m_visual_tyre_compound),
            'tyre-set-id': self.m_tyre_set_id,
            'tyre-age-laps': self.m_tyre_age_laps
        }

    def __repr__(self) -> str:
        """
        Returns a string representation of the object suitable for debugging.
        """
        return f"TyreSetInfo(actual_tyre_compound={str(self.m_actual_tyre_compound)}, " \
            f"visual_tyre_compound={str(self.m_visual_tyre_compound)}, " \
            f"tyre_set_id={self.m_tyre_set_id}, " \
            f"tyre_age_laps={self.m_tyre_age_laps})"

    def __str__(self) -> str:
        """
        Returns a string representation of the object suitable for end-users.
        """
        return f"Tyre Set ID: {self.m_tyre_set_id}, " \
            f"Actual Compound: {str(self.m_actual_tyre_compound)}, " \
            f"Visual Compound: {str(self.m_visual_tyre_compound)}, " \
            f"Tyre Age (laps): {self.m_tyre_age_laps}"

class TyreSetHistoryEntry:
    """
    Class that models the data stored per entry in the tyre set history list.

    Attributes:
        m_start_lap (int): The lap at which the tire set was fitted.
        m_fitted_index (int): The index representing the fitted tire set.
        m_tyre_set_key (Optional[str]): The key of the fitted tire set.
        m_end_lap (Optional[int]): The lap at which the tire set was removed.
                                        Must be set using the _computeTyreStintEndLaps method
        m_tyre_wear_history (List[TyreWearPerLap]): The list of tyre wears for the fitted tire set.
    """

    def __init__(self,
                    start_lap: int,
                    index: int,
                    tyre_set_key: Optional[str] = None,
                    initial_tyre_wear: Optional[TyreWearPerLap] = None):
        """Initialize the TyreSetHistoryEntry object. The m_end_lap attribute will be set to None

        Args:
            start_lap (int): The lap at which the tire set was fitted.
            index (int): The index representing the fitted tire set.
            tyre_set_key (Optional[str]): The key of the fitted tire set.
            initial_tyre_wear (TyreWearPerLap): The starting tyre wear for this set (can be non 0 in case of reuse)
        """
        self.m_start_lap : int                          = start_lap
        self.m_fitted_index : int                       = index
        self.m_tyre_set_key : Optional[str]             = tyre_set_key
        self.m_end_lap : int                            = None
        if initial_tyre_wear:
            self.m_tyre_wear_history : List[TyreWearPerLap] = [initial_tyre_wear]
        else:
            self.m_tyre_wear_history : List[TyreWearPerLap] = []

    def getTyreWearJSONList(self):
        """Dump this object into JSON

        Returns:
            List[Dict[str, Any]]: The JSON dump
        """

        return [entry.toJSON() for entry in self.m_tyre_wear_history]

    def toJSON(self, include_tyre_wear_history: Optional[bool] = True) -> Dict[str, Any]:
        """Dump this object into JSON

        Args:
            include_tyre_wear_history (Optional[bool]): Whether to include the tyre wear history. Defaults to False.

        Returns:
            Dict[str, Any]: The JSON dump
        """

        return {
            "start-lap": self.m_start_lap,
            "end-lap": self.m_end_lap,
            "stint-length": (self.m_end_lap+1 - self.m_start_lap) if self.m_end_lap else None,
            "fitted-index": self.m_fitted_index,
            "tyre-set-key": self.m_tyre_set_key,
            "tyre-wear-history": self.getTyreWearJSONList() if include_tyre_wear_history else None
        }

    def __repr__(self) -> str:
        """Return the string representation of this object

        Returns:
            str: string representation of this object
        """
        return  f"start_lap: {self.m_start_lap} end_lap: {self.m_end_lap} key: {self.m_tyre_set_key} " \
                f"tyre_wear_history_len: {len(self.m_tyre_wear_history)}"

    def __str__(self) -> str:
        """Return the string representation of this object

        Returns:
            str: string representation of this object
        """
        return self.__repr__()
