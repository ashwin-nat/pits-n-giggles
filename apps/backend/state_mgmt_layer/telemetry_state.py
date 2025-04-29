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

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple

from apps.backend.state_mgmt_layer.overtakes import GetOvertakesStatus
from lib.f1_types import PacketFinalClassificationData, PacketSessionData
from lib.inter_task_communicator import AsyncInterTaskCommunicator, ITCMessage
from lib.overtake_analyzer import OvertakeRecord
from lib.race_analyzer import getFastestTimesJson, getTyreStintRecordsDict

from .session_state import SessionInfo, SessionState

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------

# -------------------------------------- GLOBALS -----------------------------------------------------------------------

_session_state: Optional[SessionState] = None

# -------------------------------------- TELEMETRY PACKET HANDLERS -----------------------------------------------------

# TODO: Deprecate these. These are redundant, dont do much other than adding one more layer in the call stack

def processSessionStarted() -> None:
    """
    Reset the data structures when SESSION_STARTED has been received
    """
    clearDataStructures("session started")
    _session_state.setRaceOngoing()

def processSessionUpdate(packet: PacketSessionData) -> bool:
    """Update the data strctures with session data
    Args:
        packet (PacketSessionData): Session data packet

        bool - True if all data needs to be reset
    """

    _session_state.processSessionUpdate(packet)
    if should_clear := _session_state.m_session_info.processSessionUpdate(packet):
        clearDataStructures("session update")
    return should_clear

def processFinalClassificationUpdate(packet: PacketFinalClassificationData) -> Dict[str, Any]:
    """Update the data structures with the final classification information
        Returns a JSON object containing all drivers data

    Args:
        packet (PacketFinalClassificationData): The final classification update packet

    Returns:
        Dict[str, Any]: Driver data JSON
    """

    final_json = _session_state.processFinalClassificationUpdate(packet)
    _session_state.setRaceCompleted()
    final_json['custom-markers'] = _session_state.m_custom_markers_history.getJSONList()
    return final_json

async def processCustomMarkerCreate() -> None:
    """Update the data structures with custom marker information
    """

    if custom_marker_obj := _session_state.getInsertCustomMarkerEntryObj():
        await AsyncInterTaskCommunicator().send("frontend-update", ITCMessage(
            m_message_type=ITCMessage.MessageType.CUSTOM_MARKER,
            m_message=custom_marker_obj))

async def processTyreDeltaSound() -> None:
    """Send the tyre delta notification to the frontend
    """

    messages = _session_state.getTyreDeltaNotificationMessages()
    for message in messages:
        asyncio.create_task(AsyncInterTaskCommunicator().send(
            "frontend-update",
            ITCMessage(
                m_message_type=ITCMessage.MessageType.TYRE_DELTA_NOTIFICATION,
                m_message=message
            )
        ))

# -------------------------------------- UTILTIES ----------------------------------------------------------------------

def getSessionInfo() -> SessionInfo:
    """
    Returns a copy of the SessionInfo object

    Returns:
        SessionInfo: A copy of the SessionInfo object
    """
    return _session_state.m_session_info

def getDriverInfoJsonByIndex(index: int) -> Optional[Dict[str, Any]]:
    """Get the driver info JSON for the given index

    Args:
        index (int): Index of the driver

    Returns:
        Optional[Dict[str, Any]]: The driver info JSON
    """

    return _session_state.getDriverInfoJsonByIndex(index)

def getRaceInfo() -> Dict[str, Any]:
    """
    Returns the race information as a dictionary with string keys and any values.
    """

    final_json = _session_state.getRaceInfoJSON()
    if "records" not in final_json:
        final_json['records'] = {
            'fastest' : getFastestTimesJson(final_json),
            'tyre-stats' : getTyreStintRecordsDict(final_json),
        }
    return final_json

def isDriverIndexValid(index: int) -> bool:
    """Check if the given index is a valid driver index

    Args:
        index (int): Index of the driver

    Returns:
        bool: True if valid
    """

    return  (0 <= index < len(_session_state.m_driver_data)) and \
            (_session_state.m_driver_data[index] and _session_state.m_driver_data[index].is_valid)

def getEventInfoStr() -> Optional[str]:
    """Returns a string with the following format
            <event-type> _ <circuit> _

    Returns:
        Optional[str]: The event type string (ends with an underscore), or None if no data is available
    """

    if _session_state.m_session_info.m_track and _session_state.m_session_info.m_session_type:
        return f"{str(_session_state.m_session_info.m_session_type)}_{str(_session_state.m_session_info.m_track)}".replace(' ', '_') + '_'
    return None

def getOvertakeObj(overtaking_car_index: int, being_overtaken_index: int) -> Optional[OvertakeRecord]:
    """Returns an overtake object containing overtake information

    Args:
        overtaking_car_index (int): The index of the overtaking car
        being_overtaken_index (int): The index of the car being overtaken

    Returns:
        str: CSV-formatted string containing 4 values
            - Current Lap number of overtaking car
            - Name of driver of overtaking car
            - Current Lap number of car being overtaken
            - Name of driver of car being overtaken
    """
    if not _session_state.m_driver_data:
        return None
    overtaking_car_obj = _session_state._getObjectByIndex(overtaking_car_index, create=False)
    being_overtaken_car_obj = _session_state._getObjectByIndex(being_overtaken_index, create=False)
    if overtaking_car_obj is None or being_overtaken_car_obj is None:
        return None

    # Prepare data for CSV writing
    if overtaking_car_obj.m_driver_info.name is None or \
        overtaking_car_obj.m_lap_info.m_current_lap is None or \
            being_overtaken_car_obj.m_driver_info.name is None or \
                being_overtaken_car_obj.m_lap_info.m_current_lap is None:
        return None
    return OvertakeRecord(
        overtaking_driver_name=overtaking_car_obj.m_driver_info.name,
        overtaking_driver_lap=overtaking_car_obj.m_lap_info.m_current_lap,
        overtaken_driver_name=being_overtaken_car_obj.m_driver_info.name,
        overtaken_driver_lap=being_overtaken_car_obj.m_lap_info.m_current_lap,
    )

def getCustomMarkersJSON() -> List[Dict[str, Any]]:
    """Returns a list of dictionaries containing custom markers in JSON format.
    """

    return _session_state.m_custom_markers_history.getJSONList()

def isPositionHistorySupported() -> bool:
    """Returns whether the position history is supported for the given event type
        Position history is only supported in race events

    Returns:
        bool: True if the position history is supported, False otherwise
    """

    return _session_state.isPositionHistorySupported()

def clearDataStructures(reason: str) -> None:
    """Clears the data structures

    Args:
        reason (str): Why the data structures should be cleared

    """
    _session_state.clear(reason)

def getOvertakeJSON(driver_name: str=None) -> Tuple[GetOvertakesStatus, Dict[str, Any]]:
    """Get the JSON value containing key overtake information

    Arguments:
        driver_name (str) - Name of the driver if specific overtake info is required

    Returns:
        Tuple[GetOvertakesStatus, Dict]: Status, JSON value (may be empty)
    """

    return _session_state.getOvertakeJSON(driver_name)

def getOvertakeRecords() -> List[OvertakeRecord]:
    """Get the overtake records

    Returns:
        List[OvertakeRecord]: The list of overtake records
    """

    return _session_state.m_overtakes_history.getRecords()

def initSessionState(logger: logging.Logger, process_car_setups: bool) -> None:
    """Init the DriverData object

    Args:
        logger (logging.Logger): Logger
        process_car_setups (bool): Whether to process car setups packets
    """
    global _session_state
    _session_state = SessionState(
        logger,
        process_car_setups
    )

def getSessionStateRef() -> SessionState:
    """Get the SessionState object reference

    Returns:
        SessionState: The SessionState object reference
    """
    global _session_state
    return _session_state
