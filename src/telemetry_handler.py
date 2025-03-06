"""
MIT License

Copyright (c) 2024 Ashwin Natarajan

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

import os
import json
from datetime import datetime
from enum import Enum
from threading import Lock
import threading
from typing import Optional, List, Tuple, Dict, Any, Generator
from lib.f1_types import F1PacketType, PacketSessionData, PacketLapData, \
    PacketEventData, PacketParticipantsData, PacketCarTelemetryData, PacketCarStatusData, \
    PacketFinalClassificationData, PacketCarDamageData, PacketSessionHistoryData, PacketMotionData, \
    PacketTyreSetsData, PacketCarSetupData, PacketTimeTrialData, SessionType23, SessionType24
from lib.overtake_analyzer import OvertakeAnalyzer, OvertakeAnalyzerMode, OvertakeRecord
import lib.race_analyzer as RaceAnalyzer
from lib.packet_forwarder import UDPForwarder
from lib.button_debouncer import ButtonDebouncer
from lib.inter_thread_communicator import InterThreadCommunicator
import src.telemetry_data as TelData
from src.telemetry_manager import F1TelemetryManager
from src.png_logger import getLogger

# -------------------------------------- TYPE DEFINITIONS --------------------------------------------------------------


class PktSaveStatus(Enum):
    """Enum representing packet save status."""
    SUCCESS = 0
    DISABLED = 1
    TABLE_EMPTY = 2
    OS_ERROR = 3
    OTHER = 4

    def __str__(self):
        return self.name

class GetOvertakesStatus(Enum):

    RACE_COMPLETED = 0
    RACE_ONGOING = 1
    NO_DATA = 2
    INVALID_INDEX = 3

    def __str__(self):
        return self.name

class OvertakesHistory:
    """Class representing the history of all overtakes
    """

    def __init__(self):
        """Initialise the overtakes history tracker
        """

        self.m_overtakes_history: List[OvertakeRecord] = []
        self.m_lock: Lock = Lock()

    def insert(self, overtake_record: OvertakeRecord) -> None:
        """Insert the overtake into the history table. THREAD SAFE

        Args:
            overtake_record (OvertakeRecord): The overtake object
        """
        with self.m_lock:
            if len(self.m_overtakes_history) == 0:
                overtake_record.m_row_id = 0
                self.m_overtakes_history.append(overtake_record)
            elif self.m_overtakes_history[-1] == overtake_record:
                png_logger.debug("not adding repeated overtake record %s", str(overtake_record))
            else:
                overtake_record.m_row_id = len(self.m_overtakes_history)
                self.m_overtakes_history.append(overtake_record)

class CustomMarkersHistory:
    """Class representing the data points for a player's custom marker
    """

    def __init__(self):
        """Initialise the custom marker history tracker
        """

        self.m_custom_markers_history: List[TelData.CustomMarkerEntry] = []
        self.m_lock: Lock = Lock()

    def insert(self, custom_marker_entry: TelData.CustomMarkerEntry) -> None:
        """Insert the custom marker into the history table. THREAD SAFE

        Args:
            custom_marker_entry (TelData.CustomMarkerEntry): The marker object
        """

        with self.m_lock:
            self.m_custom_markers_history.append(custom_marker_entry)

    def clear(self) -> None:
        """Clear the history table. THREAD SAFE
        """

        with self.m_lock:
            self.m_custom_markers_history.clear()

    def getCount(self) -> int:
        """Get the number of markers in the history table. THREAD SAFE

        Returns:
            int: The count value
        """

        with self.m_lock:
            return len(self.m_custom_markers_history)

    def getJSONList(self) -> List[Dict[str, Any]]:
        """Get the list of JSON objects representing the marker objects. THREAD SAFE

        Returns:
            List[Dict[str, Any]]: The JSON list
        """

        with self.m_lock:
            return [entry.toJSON() for entry in self.m_custom_markers_history]

    def getMarkers(self) -> Generator[TelData.CustomMarkerEntry, None, None]:
        """
        Generate markers from the history table.

        Yields:
        - Tuple[float, bytes]: A tuple containing timestamp (float) and data (bytes) for each packet.
        """
        yield from self.m_custom_markers_history

# -------------------------------------- GLOBALS -----------------------------------------------------------------------

g_overtakes_history: OvertakesHistory = OvertakesHistory()
g_post_race_data_autosave: bool = False
g_directory_mapping: Dict[str, str] = {}
g_udp_custom_action_code: Optional[int] = None
g_udp_tyre_delta_action_code: Optional[int] = None
g_process_car_setup: Optional[bool] = None
g_completed_session_uid_set: set[int] = set()
g_button_debouncer = ButtonDebouncer()
png_logger = getLogger()

# -------------------------------------- INITIALIZATION ----------------------------------------------------------------

def initTelemetryGlobals(
    post_race_data_autosave: bool,
    udp_custom_action_code: Optional[int],
    udp_tyre_delta_action_code: Optional[int],
    process_car_setup: bool) -> None:
    """Initialise the autosave settings

    Args:
        post_race_data_autosave (bool): Save JSON file after race
        udp_custom_action_code (Optional[int]): UDP action code to set marker
        udp_tyre_delta_action_code (Optional[int]): UDP action code to play tyre delta sound
        process_car_setup (bool): Whether to process car setup data
    """

    global g_post_race_data_autosave
    global g_udp_custom_action_code
    global g_udp_tyre_delta_action_code
    global g_process_car_setup
    g_post_race_data_autosave = post_race_data_autosave
    g_udp_custom_action_code = udp_custom_action_code
    g_udp_tyre_delta_action_code = udp_tyre_delta_action_code
    g_process_car_setup = process_car_setup

def initDirectories() -> None:
    """
    Initialize the necessary directories for storing race information
    This function creates a directory structure based on the current date if it does not already exist.

    Returns:
        None
    """
    def ensureDirectoryExists(directory: str) -> None:
        """
        Ensure that the specified directory exists. If it doesn't, create it along with any missing parent directories.

        Parameters:
        - directory (str): The path of the directory to be checked or created.

        Returns:
        - None
        """
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            png_logger.info("Directory '%s' created.", directory)

    global g_directory_mapping
    ts_prefix = datetime.now().strftime("%Y_%m_%d")
    g_directory_mapping['race-info'] = f"data/{ts_prefix}/race-info/"

    for directory in g_directory_mapping.values():
        ensureDirectoryExists(directory)

def initForwarder(forwarding_targets: List[Tuple[str, int]]) -> None:
    """Init the forwarding thread, if targets are defined

    Args:
        forwarding_targets (List[Tuple[str, int]]): Forwarding Targets list
    """

    # Spawn the thread only if targets are defined
    if forwarding_targets:
        forwarding_thread = threading.Thread(target=udpForwardingThread,
                                    args=(forwarding_targets,))
        forwarding_thread.daemon = True
        forwarding_thread.start()


# -------------------------------------- THREADS -----------------------------------------------------------------------

def udpForwardingThread(forwarding_targets: List[Tuple[str, int]]) -> None:
    """Thread that forwards all UDP packets to specified targets

    Args:
        forwarding_targets (List[Tuple[str, int]]): List of tuple of target
            Each tuple is a pair of IP addr/hostname (str), port number (int)
    """

    udp_forwarder = UDPForwarder(forwarding_targets)
    png_logger.info(f"Initialised forwarder. Targets={forwarding_targets}")
    while True:
        packet = InterThreadCommunicator().receiveWaitIndefinite("packet-forward")
        assert packet is not None

        udp_forwarder.forward(packet)

# -------------------------------------- UTILITIES ---------------------------------------------------------------------

def getTimestampStr() -> str:
    """
    Get the current timestamp as a string formatted as year_month_day_hour_minute_second.

    Returns:
        str: A string representing the current timestamp.
    """
    return datetime.now().strftime("%Y_%m_%d_%H_%M_%S")

def getOvertakeJSON(driver_name: str=None) -> Tuple[GetOvertakesStatus, Dict[str, Any]]:
    """Get the JSON value containing key overtake information

    Arguments:
        driver_name (str) - Name of the driver if specific overtake info is required

    Returns:
        Tuple[GetOvertakesStatus, Dict]: Status, JSON value (may be empty)
    """
    final_classification_received = bool(TelData.getGlobals().m_packet_final_classification)
    global g_overtakes_history
    with g_overtakes_history.m_lock:
        if not final_classification_received:
            if len(g_overtakes_history.m_overtakes_history) == 0:
                return GetOvertakesStatus.NO_DATA, {}
            return GetOvertakesStatus.RACE_ONGOING, OvertakeAnalyzer(
                input_mode=OvertakeAnalyzerMode.INPUT_MODE_LIST_OVERTAKE_RECORDS,
                input_data=g_overtakes_history.m_overtakes_history).toJSON(
                    driver_name=driver_name,
                    is_case_sensitive=True)
        return GetOvertakesStatus.RACE_COMPLETED, OvertakeAnalyzer(
            input_mode=OvertakeAnalyzerMode.INPUT_MODE_LIST_OVERTAKE_RECORDS,
            input_data=g_overtakes_history.m_overtakes_history).toJSON(
                driver_name=driver_name,
                is_case_sensitive=True)


def writeDictToJsonFile(data_dict: Dict, file_name: str) -> None:
    """
    Write a dictionary containing JSON data to a file.

    Parameters:
    - data_dict (Dict): Dictionary containing JSON data.
    - file_name (str): File name to write the data to.
    """
    with open(file_name, 'w', encoding='utf-8') as json_file:
        json.dump(data_dict, json_file, indent=4, ensure_ascii=False, sort_keys=True)

def postGameDumpToFile(final_json: Dict[str, Any]) -> None:
    """
    Write the contents of final_json and player recorded events to a file.

    Arguments:
        final_json (Dict): Dictionary containing JSON data after final classification
    """

    global g_directory_mapping
    global g_overtakes_history

    event_str = TelData.getEventInfoStr()
    if not event_str:
        return

    # Save the JSON data
    global g_post_race_data_autosave
    if g_post_race_data_autosave:
        # Add the overtakes as well
        with g_overtakes_history.m_lock:
            final_json['overtakes'] = {
                'records': [record.toJSON() for record in g_overtakes_history.m_overtakes_history]
            }

        # Next, fastest lap and sector records
        final_json['records'] = {
            'fastest' : RaceAnalyzer.getFastestTimesJson(final_json),
            'tyre-stats' : RaceAnalyzer.getTyreStintRecordsDict(final_json)
        }

        final_json_file_name = g_directory_mapping['race-info'] + 'race_info_' + \
                event_str + getTimestampStr() + '.json'
        writeDictToJsonFile(final_json, final_json_file_name)
        png_logger.info("Wrote race info to %s", final_json_file_name)
    else:
        png_logger.debug("Not saving post race data")

def clearAllDataStructures() -> None:
    """
    Clear all data structures.
    """

    global g_overtakes_history

    TelData.processSessionStarted()
    with g_overtakes_history.m_lock:
        g_overtakes_history.m_overtakes_history.clear()
    g_completed_session_uid_set.clear()

# -------------------------------------- TELEMETRY PACKET HANDLERS -----------------------------------------------------

class F1TelemetryHandler:
    """
    Handles incoming F1 telemetry data. Handles the various types of incoming packets

    Attributes:
    - m_manager (F1TelemetryManager): The telemetry manager instance.
    """

    def __init__(self,
        port: int,
        forwarding_targets: List[Tuple[str, int]],
        replay_server: bool = False) -> None:
        """
        Initialize F1TelemetryHandler.

        Parameters:
            - port (int): The port number for telemetry.
            - replay_server: bool: If true, init in replay mode (TCP)
        """
        self.m_manager = F1TelemetryManager(port, replay_server)
        self.m_should_forward = bool(forwarding_targets)

    def run(self):
        """
        Run the telemetry handler.

        Returns:
        None
        """
        self.registerCallbacks()
        self.m_manager.run()

    def registerCallbacks(self) -> None:
        """
        Register callback functions for different types of telemetry packets.
        """

        self.m_manager.registerCallback(F1PacketType.SESSION, F1TelemetryHandler.handleSessionData)
        self.m_manager.registerCallback(F1PacketType.LAP_DATA, F1TelemetryHandler.handleLapData)
        self.m_manager.registerCallback(F1PacketType.EVENT, F1TelemetryHandler.handleEvent)
        self.m_manager.registerCallback(F1PacketType.PARTICIPANTS, F1TelemetryHandler.handleParticipants)
        self.m_manager.registerCallback(F1PacketType.CAR_TELEMETRY, F1TelemetryHandler.handleCarTelemetry)
        self.m_manager.registerCallback(F1PacketType.CAR_STATUS, F1TelemetryHandler.handleCarStatus)
        self.m_manager.registerCallback(F1PacketType.FINAL_CLASSIFICATION, F1TelemetryHandler.handleFinalClassification)
        self.m_manager.registerCallback(F1PacketType.CAR_DAMAGE, F1TelemetryHandler.handleCarDamage)
        self.m_manager.registerCallback(F1PacketType.SESSION_HISTORY, F1TelemetryHandler.handleSessionHistory)
        self.m_manager.registerCallback(F1PacketType.TYRE_SETS, F1TelemetryHandler.handleTyreSets)
        self.m_manager.registerCallback(F1PacketType.MOTION, F1TelemetryHandler.handleMotion)
        self.m_manager.registerCallback(F1PacketType.CAR_SETUPS, F1TelemetryHandler.handleCarSetups)
        self.m_manager.registerCallback(F1PacketType.TIME_TRIAL, F1TelemetryHandler.handleTimeTrialData)

        if self.m_should_forward:
            self.m_manager.registerRawPacketCallback(F1TelemetryHandler.handleRawPacket)

    @staticmethod
    def handleRawPacket(packet: List[bytes]) -> None:
        """
        Handle raw telemetry packet.

        Parameters:
            packet (List[bytes]): The raw telemetry packet.
        """

        InterThreadCommunicator().send("packet-forward", packet)

    @staticmethod
    def handleSessionData(packet: PacketSessionData) -> None:
        """
        Handle session data telemetry packet.

        Parameters:
            packet (PacketSessionData): The session data telemetry packet.
        """

        if packet.m_sessionDuration == 0:
            png_logger.info("Session duration is 0. clearing data structures")
            clearAllDataStructures()

        elif TelData.processSessionUpdate(packet):
            png_logger.info("Session UID changed. clearing data structures")
            clearAllDataStructures()

    @staticmethod
    def handleLapData(packet: PacketLapData) -> None:
        """
        Handle lap data telemetry packet.

        Parameters:
            packet (PacketLapData): The lap data telemetry packet.
        """

        TelData.processLapDataUpdate(packet)

    @staticmethod
    def handleEvent(packet: PacketEventData) -> None:
        """Handle the Event packet

        Args:
            packet (PacketEventData): The parsed object containing the event data packet's contents
        """
        global g_overtakes_history
        global g_button_debouncer

        # UDP Custom Event - Add marker player markers list
        if packet.m_eventCode == PacketEventData.EventPacketType.BUTTON_STATUS:
            if (g_udp_custom_action_code is not None) and \
                (packet.mEventDetails.isUDPActionPressed(g_udp_custom_action_code)) and \
                (g_button_debouncer.onButtonPress(g_udp_custom_action_code)):

                png_logger.debug('UDP action %d pressed', g_udp_custom_action_code)
                TelData.processCustomMarkerCreate()

            if (g_udp_tyre_delta_action_code is not None) and \
                (packet.mEventDetails.isUDPActionPressed(g_udp_tyre_delta_action_code)) and \
                (g_button_debouncer.onButtonPress(g_udp_tyre_delta_action_code)):

                png_logger.debug('UDP action %d pressed', g_udp_tyre_delta_action_code)
                TelData.processTyreDeltaSound()

        # Fastest Lap - update data structures
        elif packet.m_eventCode == PacketEventData.EventPacketType.FASTEST_LAP:
            TelData.processFastestLapUpdate(packet)

        # Session Started - Empty data structures
        elif packet.m_eventCode == PacketEventData.EventPacketType.SESSION_STARTED:
            clearAllDataStructures()

        # Retirement - Update data strucutres
        elif packet.m_eventCode == PacketEventData.EventPacketType.RETIREMENT:
            TelData.processRetirementEvent(packet)

        # Overtake - Update overtake records list
        elif packet.m_eventCode == PacketEventData.EventPacketType.OVERTAKE:
            overtake_obj = TelData.getOvertakeObj(packet.mEventDetails.overtakingVehicleIdx,
                                                        packet.mEventDetails.beingOvertakenVehicleIdx)
            if overtake_obj:
                g_overtakes_history.insert(overtake_obj)

        # Collision - Update collision records list
        elif packet.m_eventCode == PacketEventData.EventPacketType.COLLISION:
            TelData.processCollisionsEvent(packet.mEventDetails)

    @staticmethod
    def handleParticipants(packet: PacketParticipantsData) -> None:
        """
        A static method to handle participants data packet.

        Arguments:
            - packet: PacketParticipantsData object
        """

        TelData.processParticipantsUpdate(packet)

    @staticmethod
    def handleCarTelemetry(packet: PacketCarTelemetryData) -> None:
        """
        Handle car telemetry data and process the car telemetry update.

        Arguments
            packet - PacketCarTelemetryData object
        """

        TelData.processCarTelemetryUpdate(packet)

    @staticmethod
    def handleCarStatus(packet: PacketCarStatusData) -> None:
        """
        Handle car status data and process the car status update.

        Arguments
            packet - PacketCarStatusData object
        """

        TelData.processCarStatusUpdate(packet)

    @staticmethod
    def handleFinalClassification(packet: PacketFinalClassificationData) -> None:
        """
        Handle and process the final classification packet. This is sent out at the end of the event when the game
            displays the final classification table

        Arguments
            packet - PacketCarStatusData object
        """
        global g_completed_session_uid_set
        if packet.m_header.m_sessionUID in g_completed_session_uid_set:
            png_logger.debug('Session UID %d final classification already processed.', packet.m_header.m_sessionUID)
            return
        png_logger.info('Received Final Classification Packet.')
        final_json = TelData.processFinalClassificationUpdate(packet)
        g_completed_session_uid_set.add(packet.m_header.m_sessionUID)

        # Perform the auto save stuff only for races
        event_type_str = str(TelData.getGlobals().m_session_type)
        if event_type_str:
            is_event_supported = True
            if packet.m_header.m_gameYear == 23:
                unsupported_event_types_f1_23 = [
                    SessionType23.PRACTICE_1,
                    SessionType23.PRACTICE_2,
                    SessionType23.PRACTICE_3,
                    SessionType23.SHORT_PRACTICE,
                    SessionType23.TIME_TRIAL,
                    SessionType23.UNKNOWN
                ]
                for event_type in unsupported_event_types_f1_23:
                    if str(event_type) in event_type_str:
                        is_event_supported = False
                        break
            else:
                unsupported_event_types_f1_24 = [
                    SessionType24.PRACTICE_1,
                    SessionType24.PRACTICE_2,
                    SessionType24.PRACTICE_3,
                    SessionType24.SHORT_PRACTICE,
                    SessionType24.TIME_TRIAL,
                    SessionType24.UNKNOWN
                ]
                for event_type in unsupported_event_types_f1_24:
                    if str(event_type) in event_type_str:
                        is_event_supported = False
                        break
            if is_event_supported:
                postGameDumpToFile(final_json)

    @staticmethod
    def handleCarDamage(packet: PacketCarDamageData) -> None:
        """
        Handle car damage data and process the car damage update.

        Arguments
            packet - PacketCarDamageData object
        """

        TelData.processCarDamageUpdate(packet)

    @staticmethod
    def handleSessionHistory(packet: PacketSessionHistoryData) -> None:
        """
        Handle and process the session history update.

        Arguments
            packet - PacketSessionHistoryData object
        """

        TelData.processSessionHistoryUpdate(packet)

    @staticmethod
    def handleTyreSets(packet: PacketTyreSetsData) -> None:
        """
        Handle and process the tyre sets update.

        Arguments
            packet - PacketTyreSetsData object
        """

        TelData.processTyreSetsUpdate(packet)

    @staticmethod
    def handleMotion(packet: PacketMotionData) -> None:
        """
        Handle and process the motion data update.

        Arguments
            packet - PacketMotionData object
        """

        TelData.processMotionUpdate(packet)

    @staticmethod
    def handleCarSetups(packet: PacketCarSetupData) -> None:
        """
        Handle and process the car setup data update.

        Arguments
            packet - PacketCarSetupData object
        """

        global g_process_car_setup
        if g_process_car_setup:
            TelData.processCarSetupsUpdate(packet)

    @staticmethod
    def handleTimeTrialData(packet: PacketTimeTrialData) -> None:
        """
        Handle and process the time trial data update.

        Arguments
            packet - PacketTimeTrialData object
        """

        TelData.processTimeTrialUpdate(packet)
