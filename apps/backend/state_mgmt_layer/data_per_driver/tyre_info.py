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

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

import json
from dataclasses import InitVar, dataclass, field
from logging import Logger
from typing import Any, Dict, List, Optional

from lib.f1_types import (ActualTyreCompound, PacketTyreSetsData,
                          VisualTyreCompound)
from lib.tyre_wear_extrapolator import TyreWearExtrapolator, TyreWearPerLap

# -------------------------------------- GLOBALS -----------------------------------------------------------------------

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------
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

class TyreSetHistoryManager:
    """Class that manages the info per tyre set usage
    """

    def __init__(self, logger: Logger):
        """Init the manager object

        Args:
            logger (Optional[Logger]): Logger
        """

        self.m_history: List[TyreSetHistoryEntry] = []
        self.m_logger = logger

    @property
    def length(self) -> int:
        """Get the length of the history collection

        Returns:
            int: Number of items in history
        """

        return len(self.m_history)

    def add(self, entry: TyreSetHistoryEntry) -> None:
        """Add given item to the history collection

        Args:
            entry (TyreSetHistoryEntry): Item to be added to the history collection
        """

        self.m_history.append(entry)

    def addTyreWear(self, tyre_wear_info: TyreWearPerLap) -> None:
        """Append tyre wear info for the specified tyre wear history item at the given index

        Args:
            tyre_wear_info (TyreWearPerLap): Tyre wear of latest lap
        """

        if not self.m_history:
            raise IndexError("Tyre history is empty, cannot add tyre wear info")
        self.m_history[-1].m_tyre_wear_history.append(tyre_wear_info)

    def overwriteLatestTyreWear(self, tyre_wear_info: TyreWearPerLap) -> None:
        """Overwrite tyre wear info for the specified tyre wear history item at the given index

        Args:
            tyre_wear_info (TyreWearPerLap): Tyre wear of latest lap
        """
        if not self.m_history:
            raise IndexError("Tyre history is empty, cannot overwrite tyre wear info")
        self.m_history[-1].m_tyre_wear_history[-1] = tyre_wear_info

    def remove(self, laps: List[int]) -> None:
        """Remove the specified laps from the tyre set history

        Args:
            laps (List[int]): List of lap numbers to be removed
        """

        if self.m_history:
            last_entry = self.m_history[-1]

            # Remove the last lap from tyre wear history if it matches any in the removal list
            if last_entry.m_tyre_wear_history:
                last_lap = last_entry.m_tyre_wear_history[-1].lap_number
                if last_lap in laps:
                    last_entry.m_tyre_wear_history.pop()

            # Remove the entire tyre set if its start lap is in the removal list
            if last_entry.m_start_lap in laps:
                self.m_history.pop()

    def _computeTyreStintEndLaps(self, final_lap_num: int) -> None:
        """
        Compute the end lap number for each tyre stint

        Args:
            final_lap_num(int): The lap number of the final/current lap
        """

        # Don't do any of this if we have no tyre stint history. Can happen if player has telemetry disabled
        if not self.length:
            return

        for i in range(len(self.m_history) - 1):
            current_stint = self.m_history[i]
            next_stint = self.m_history[i + 1]
            current_stint.m_end_lap = next_stint.m_start_lap - 1

        # For the last tyre stint, get end lap num from session history
        self.m_history[-1].m_end_lap = final_lap_num

        # If the first stint has garbage data, remove it (this happens if the user customizes the strat before race)
        if self.m_history[0].m_end_lap < self.m_history[0].m_start_lap:
            garbage_obj = self.m_history.pop(0)
            self.m_logger.debug("Removed garbage tyre stint history record.\n %s",
                             json.dumps(garbage_obj.toJSON(include_tyre_wear_history=False), indent=4))

    def getEntries(self) -> List[TyreSetHistoryEntry]:
        """Get all entries in the tyre set history collection

        Returns:
            List[TyreSetHistoryEntry]: The list of all history entries
        """
        return self.m_history

    def getEntry(self, index: int) -> Optional[TyreSetHistoryEntry]:
        """Get the entry in the tyre set history collection at the specified index

        Args:
            index (int): History item index

        Returns:
            Optional[TyreSetHistoryEntry]: History item (may be None)
        """

        return self.m_history[index]

    def getLastEntry(self) -> Optional[TyreSetHistoryEntry]:
        """Get the entry in the tyre set history collection at the specified index

        Returns:
            Optional[TyreSetHistoryEntry]: History item (may be None)
        """

        return self.getEntry(index=-1)

    def toJSON(self, include_wear_history: bool, tyre_sets_packet: PacketTyreSetsData, final_lap_num: int) -> List[Dict[str, Any]]:
        """Get the JSON representation of the tyre set history

        Args:
            include_wear_history (bool): Whether tyre wear per lap should be included under each tyre set
            tyre_sets_packet (PacketTyreSetsData): The most recent tyre sets packet data copy
            final_lap_num (int): Final lap num

        Returns:
            List[Dict[str, Any]]: List of tyre stint history entries in JSON
        """

        self._computeTyreStintEndLaps(final_lap_num)
        tyre_set_history = []
        for entry in self.m_history:
            is_index_valid = 0 < entry.m_fitted_index < len(tyre_sets_packet.m_tyreSetData)
            entry_json = entry.toJSON(include_wear_history)
            entry_json['tyre-set-data'] = \
                tyre_sets_packet.m_tyreSetData[entry.m_fitted_index].toJSON() if is_index_valid else None

            if include_wear_history:
                entry_json['tyre-wear-history'] = entry.getTyreWearJSONList()
                # Overwrite the tyre sets wear to actual recent float value
                if (len(entry_json['tyre-wear-history']) > 0) and (entry_json['tyre-set-data']):
                    entry_json['tyre-set-data']['wear'] = entry_json['tyre-wear-history'][-1]['average']
            tyre_set_history.append(entry_json)

        return tyre_set_history

@dataclass(slots=True)
class TyreInfo:
    """
    Class that models the tire information for a race driver.

    Attributes:
        total_laps (int): The total number of laps in the race
        tyre_age (Optional[int]): The age of the driver's current set of tires.
        tyre_vis_compound (Optional[VisualTyreCompound]): The visual type of tire compound being used.
        tyre_act_compound (Optional[ActualTyreCompound]): The actual type of tire compound being used.
        tyre_wear (Optional[TyreWearPerLap]): The level of wear on the driver's tires per lap.
        tyre_surface_temp (Optional[float]): The surface temperature of the driver's tires.
        tyre_inner_temp (Optional[float]): The inner temperature of the driver's tires.
        tyre_life_remaining_laps (Optional[int]): The number of laps the tires are expected to last.
        m_tyre_set_history_manager (TyreSetHistoryManager): Manages the history of tire sets used.
        m_tyre_wear_extrapolator (TyreWearExtrapolator): Predicts the tire wear for upcoming laps.
    """
    total_laps: InitVar[int]
    logger: InitVar[Logger]

    tyre_age: Optional[int] = None
    tyre_vis_compound: Optional[VisualTyreCompound] = None
    tyre_act_compound: Optional[ActualTyreCompound] = None
    tyre_wear: Optional[TyreWearPerLap] = None
    tyre_surface_temp: Optional[float] = None
    tyre_inner_temp: Optional[float] = None
    tyre_life_remaining_laps: Optional[int] = None

    m_tyre_set_history_manager: "TyreSetHistoryManager" = field(init=False)
    m_tyre_wear_extrapolator: "TyreWearExtrapolator" = field(init=False)

    m_logger: Logger = field(init=False, repr=False)

    def __post_init__(self, total_laps: int, logger: Logger):
        """Init the utility objects and store logger"""
        self.m_logger = logger
        self.m_tyre_set_history_manager = TyreSetHistoryManager(self.m_logger)
        self.m_tyre_wear_extrapolator = TyreWearExtrapolator([], total_laps=total_laps)
