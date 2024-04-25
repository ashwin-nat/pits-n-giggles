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
import logging
from datetime import datetime
from enum import Enum
from threading import Lock
from typing import Optional, List, Tuple, Dict, Any, Generator
from tqdm import tqdm
from src.telemetry_manager import F1TelemetryManager
from lib.f1_types import *
from lib.packet_cap import F1PacketCapture
from lib.overtake_analyzer import OvertakeAnalyzer, OvertakeAnalyzerMode, OvertakeRecord
import src.telemetry_data as TelData
import lib.race_analyzer as RaceAnalyzer

# -------------------------------------- TYPE DEFINITIONS --------------------------------------------------------------

class PacketCaptureMode(Enum):
    """Enum representing packet capture modes."""
    DISABLED = 'disabled'
    ENABLED = 'enabled'
    ENABLED_WITH_AUTOSAVE = 'enabled-with-autosave'


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

class PacketCaptureTable:
    """Thread safe container for F1PacketCapture instance.
    """

    def __init__(self) -> None:
        """
        Initialize the object by creating a new F1PacketCapture instance and a Lock instance.
        """
        self.m_packet_capture = F1PacketCapture()
        self.m_lock = Lock()

    def add(self, packet: List[bytes]) -> None:
        """
        Add a packet to the packet list while acquiring a lock to ensure thread safety.

        Parameters:
            packet (List[bytes]): The packet to be added to the table.
        """
        with self.m_lock:
            self.m_packet_capture.add(packet)

    def getNumPackets(self) -> int:
        """
        Returns the number of packets captured by the packet capture object.
        """
        with self.m_lock:
            return self.m_packet_capture.getNumPackets()

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
            else:
                if self.m_overtakes_history[-1] == overtake_record:
                    logging.debug("not adding repeated overtake record " + str(overtake_record))
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
        for entry in self.m_custom_markers_history:
            yield entry

# -------------------------------------- GLOBALS -----------------------------------------------------------------------

g_packet_capture_table: PacketCaptureTable = PacketCaptureTable()
g_pkt_cap_mode: PacketCaptureMode = PacketCaptureMode.DISABLED
g_num_active_cars: int = 0
g_overtakes_history: OvertakesHistory = OvertakesHistory()
g_post_race_data_autosave: bool = False
g_directory_mapping: Dict[str, str] = {}
g_udp_custom_action_code: Optional[int] = None
g_player_recorded_events_history: CustomMarkersHistory = CustomMarkersHistory()

# -------------------------------------- INITIALIZATION ----------------------------------------------------------------

def initAutosaves(post_race_data_autosave: bool, udp_custom_action_code: Optional[int]):
    global g_post_race_data_autosave
    global g_udp_custom_action_code
    g_post_race_data_autosave = post_race_data_autosave
    g_udp_custom_action_code = udp_custom_action_code

def initDirectories():

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
            logging.info(f"Directory '{directory}' created.")

    global g_directory_mapping
    ts_prefix = datetime.now().strftime("%Y_%m_%d")
    g_directory_mapping['race-info'] = "data/" + ts_prefix + "/race-info/"
    g_directory_mapping['packet-captures'] = "data/" + ts_prefix + "/packet-captures/"

    for directory in g_directory_mapping.values():
        ensureDirectoryExists(directory)

def initPktCap(packet_capture_mode: PacketCaptureMode):
    """
    Initialize packet capture.

    Parameters:
    - packet_capture_mode (PacketCaptureMode): The mode for packet capture.

    Returns:
    None
    """

    global g_pkt_cap_mode
    g_pkt_cap_mode = packet_capture_mode

# -------------------------------------- UTILITIES ---------------------------------------------------------------------

def addRawPacket(packet: List[bytes]):
    """
    Add raw packet to the packet capture table.

    Parameters:
        - packet (List[bytes]): The raw packet data.
    """
    global g_packet_capture_table
    g_packet_capture_table.add(packet)

def getTimestampStr() -> str:
    """
    Get the current timestamp as a string formatted as year_month_day_hour_minute_second.

    Returns:
        str: A string representing the current timestamp.
    """
    return datetime.now().strftime("%Y_%m_%d_%H_%M_%S")

def dumpPktCapToFile(
        file_name: Optional[str] = None,
        clear_db: bool = False,
        reason: str = '') -> Tuple[PktSaveStatus, str, int, int]:
    """
    Dump packet capture data to a file.

    Parameters:
    - file_name (Optional[str]): The name of the file to save. Default is None.
    - clear_db (bool): Whether to clear the packet capture database. Default is False.
    - reason (str): Reason for dumping the packet capture data.

    Returns:
    Tuple[PktSaveStatus, str, int, int]: A tuple representing the
        save status,
        file name,
        number of packets, and
        number of bytes.
    """

    global g_pkt_cap_mode

    if g_pkt_cap_mode == PacketCaptureMode.DISABLED:
        return PktSaveStatus.DISABLED, None, 0, 0

    global g_packet_capture_table

    progress_bar = tqdm(
        total=g_packet_capture_table.getNumPackets(),
        desc='Saving Packets',
        unit='packet',
        mininterval=0.1
    )

    def progressBarUpdater(current_packets: int, total_packets: int, progress_bar: tqdm) -> None:
        """
        Updates the progress bar for the current packet out of the total packets.

        Args:
            current_packets (int): The current packet number.
            total_packets (int): The total number of packets.
            progress_bar (tqdm): The progress bar to be updated.
        """

        progress_bar.update(1)

    with g_packet_capture_table.m_lock:
        try:
            if not file_name:
                global g_directory_mapping
                file_name = g_directory_mapping['packet-captures'] + \
                            'capture_' + getTimestampStr() + \
                            '.' + F1PacketCapture.file_extension
            file_name, num_packets, num_bytes = g_packet_capture_table.m_packet_capture.dumpToFile(
                file_name=file_name,
                progress_update_callback=progressBarUpdater,
                progress_update_callback_arg=progress_bar)

            if clear_db:
                g_packet_capture_table.m_packet_capture.clear()
            if (file_name is not None) and (num_bytes > 0) and (num_packets > 0):
                logging.info(
                    f"Dumped raw telemetry data. "
                    f"File Name: {file_name}, "
                    f"Number of Packets: {num_packets}, "
                    f"Number of Bytes: {num_bytes}, "
                    f"Clear DB: {str(clear_db)}, "
                    f"Reason: {reason}"
                )
                return PktSaveStatus.SUCCESS, file_name, num_packets, num_bytes
            else:
                return PktSaveStatus.TABLE_EMPTY, None, 0, 0

        except Exception as e:
            # Log the exception
            logging.error(f"An error occurred while dumping telemetry data: {e}")

            # Return the appropriate status
            return PktSaveStatus.OS_ERROR, None, 0, 0

def getOvertakeJSON(driver_name: str=None) -> Tuple[GetOvertakesStatus, Dict[str, Any]]:
    """Get the JSON value containing key overtake information

    Arguments:
        driver_name (str) - Name of the driver if specific overtake info is required

    Returns:
        Tuple[GetOvertakesStatus, Dict]: Status, JSON value (may be empty)
    """
    _, _, _, _, _, _, _, _, final_classification_received = TelData.getGlobals()
    global g_overtakes_history
    with g_overtakes_history.m_lock:
        if not final_classification_received:
            if len(g_overtakes_history.m_overtakes_history) == 0:
                return GetOvertakesStatus.NO_DATA, {}
            else:
                return GetOvertakesStatus.RACE_ONGOING, OvertakeAnalyzer(
                    input_mode=OvertakeAnalyzerMode.INPUT_MODE_LIST_OVERTAKE_RECORDS,
                    input=g_overtakes_history.m_overtakes_history).toJSON(
                        driver_name=driver_name,
                        is_case_sensitive=True)
        else:
            return GetOvertakesStatus.RACE_COMPLETED, OvertakeAnalyzer(
                input_mode=OvertakeAnalyzerMode.INPUT_MODE_LIST_OVERTAKE_RECORDS,
                input=g_overtakes_history.m_overtakes_history).toJSON(
                    driver_name=driver_name,
                    is_case_sensitive=True)

def getCustomMarkersJSON() -> List[Dict[str, Any]]:
    """
    Return a list of dictionaries containing custom markers in JSON format.
    """

    global g_player_recorded_events_history
    return g_player_recorded_events_history.getJSONList()

def printOvertakeData(file_name: str=None):
    """Print the overtake data

    Args:
        file_name (str): Name of the csv file with the overtake data. If None, directly gets the data from the list
    """

    player_name = TelData.getPlayerName()
    if file_name:
        overtake_analyzer = OvertakeAnalyzer(
            input_mode=OvertakeAnalyzerMode.INPUT_MODE_FILE_CSV,
            input=file_name)
    else:
        global g_overtakes_history
        with g_overtakes_history.m_lock:
            overtake_analyzer = OvertakeAnalyzer(
                input_mode=OvertakeAnalyzerMode.INPUT_MODE_LIST_OVERTAKE_RECORDS,
                input=g_overtakes_history.m_overtakes_history)
    logging.info(overtake_analyzer.getFormattedString(driver_name=player_name, is_case_sensitive=True))

def writeDictToJsonFile(data_dict: Dict, file_name: str) -> None:
    """
    Write a dictionary containing JSON data to a file.

    Parameters:
    - data_dict (Dict): Dictionary containing JSON data.
    - file_name (str): File name to write the data to.
    """
    with open(file_name, 'w', encoding='utf-8') as json_file:
        json.dump(data_dict, json_file, indent=4, ensure_ascii=False, sort_keys=True)

def addFunStatsToFinalClassificationJson(final_json: Dict[str, Any]) -> None:
    """
    Add the fun stats to the final classification JSON.

    Arguments:
        final_json (Dict): Dictionary containing JSON data after final classification
    """

    global g_overtakes_history

    final_json['overtakes'] = {'records': [record.toJSON() for record in g_overtakes_history.m_overtakes_history]}

    with g_overtakes_history.m_lock:
        player_name = TelData.getPlayerName()
        overtake_analyzer = OvertakeAnalyzer(
            input_mode=OvertakeAnalyzerMode.INPUT_MODE_LIST_OVERTAKE_RECORDS,
            input=g_overtakes_history.m_overtakes_history)
        logging.info(overtake_analyzer.getFormattedString(driver_name=player_name, is_case_sensitive=True))
        # Add the new keys directly to the top level of final_json
        final_json['overtakes'].update(
            overtake_analyzer.toJSON(
                driver_name=player_name,
                is_case_sensitive=True))

    # Next, fastest lap and sector records
    final_json['records'] = {
        'fastest' : RaceAnalyzer.getFastestTimesJson(final_json),
        'tyre-stats' : RaceAnalyzer.getTyreStintRecordsDict(final_json)
    }


def postGameDumpToFile(final_json: Dict[str, Any]) -> None:
    """
    Write the contents of final_json, packet capture and player recorded events to a file.

    Arguments:
        final_json (Dict): Dictionary containing JSON data after final classification
    """

    global g_directory_mapping
    global g_overtakes_history
    global g_player_recorded_events_history

    event_str = TelData.getEventInfoStr()
    if not event_str:
        return

    # Capture the packets if required
    global g_pkt_cap_mode
    if g_pkt_cap_mode == PacketCaptureMode.ENABLED_WITH_AUTOSAVE:
        if not file_name:
            file_name = 'capture_' + event_str + getTimestampStr() + \
                F1PacketCapture.file_extension
            file_name = g_directory_mapping["packet-captures"] + file_name
        dumpPktCapToFile(file_name=file_name,reason='Final Classification')

    # Save the JSON data
    global g_post_race_data_autosave
    if g_post_race_data_autosave:
        # addFunStatsToFinalClassificationJson(final_json)

        # Add the markers as well
        final_json['custom-markers'] = []
        if g_player_recorded_events_history.getCount() > 0:
            for marker in g_player_recorded_events_history.getMarkers():
                final_json['custom-markers'].append(marker.toJSON())

        final_json_file_name = g_directory_mapping['race-info'] + 'race_info_' + \
                event_str + getTimestampStr() + '.json'
        writeDictToJsonFile(final_json, final_json_file_name)
        logging.info("Wrote race info to " + final_json_file_name)

# -------------------------------------- TELEMETRY PACKET HANDLERS -----------------------------------------------------

class F1TelemetryHandler:
    """
    Handles incoming F1 telemetry data. Handles the various types of incoming packets

    Attributes:
    - m_manager (F1TelemetryManager): The telemetry manager instance.
    - m_raw_packet_capture (PacketCaptureMode): The raw packet capture mode.
    """

    def __init__(self,
        port: int,
        raw_packet_capture: PacketCaptureMode = PacketCaptureMode.DISABLED,
        replay_server: bool = False) -> None:
        """
        Initialize F1TelemetryHandler.

        Parameters:
            - port (int): The port number for telemetry.
            - raw_packet_capture (PacketCaptureMode): The mode for raw packet capture
        """
        self.m_manager = F1TelemetryManager(port, replay_server)
        self.m_raw_packet_capture = raw_packet_capture

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

        if self.m_raw_packet_capture != PacketCaptureMode.DISABLED:
            self.m_manager.registerRawPacketCallback(F1TelemetryHandler.handleRawPacket)

    @staticmethod
    def handleRawPacket(packet: List[bytes]) -> None:
        """
        Handle raw telemetry packet.

        Parameters:
            acket (List[bytes]): The raw telemetry packet.
        """
        addRawPacket(packet)

    @staticmethod
    def handleSessionData(packet: PacketSessionData) -> None:
        """
        Handle session data telemetry packet.

        Parameters:
            packet (PacketSessionData): The session data telemetry packet.
        """

        if packet.m_sessionDuration == 0:
            logging.info("Session duration is 0. clearing data structures")
            TelData.processSessionStarted()

        elif TelData.processSessionUpdate(packet):
            logging.info("Session UID changed. clearing data structures")
            TelData.processSessionStarted()

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
        global g_num_active_cars

        # UDP Custom Event - Add marker player markers list
        if packet.m_eventStringCode == PacketEventData.EventPacketType.BUTTON_STATUS:
            if (g_udp_custom_action_code is not None) and \
                (packet.mEventDetails.isUDPActionPressed(g_udp_custom_action_code)):

                logging.debug('UDP action ' + str(g_udp_custom_action_code) + ' pressed')
                global g_player_recorded_events_history
                custom_marker_obj = TelData.getCustomMarkerEntryObj(add_to_queue=True)
                if custom_marker_obj:
                    g_player_recorded_events_history.insert(custom_marker_obj)
                    logging.debug('Player recorded event: ' + str(custom_marker_obj))
                else:
                    logging.error("Unable to generate player_recorded_event_str")

        # Fastest Lap - update data structures
        elif packet.m_eventStringCode == PacketEventData.EventPacketType.FASTEST_LAP:
            TelData.processFastestLapUpdate(packet)

        # Session Started - Empty data structures
        elif packet.m_eventStringCode == PacketEventData.EventPacketType.SESSION_STARTED:
            g_num_active_cars = 0
            TelData.processSessionStarted()
            # Clear the list regardless of event type
            with g_overtakes_history.m_lock:
                g_overtakes_history.m_overtakes_history.clear()
            g_player_recorded_events_history.clear()
            logging.info("Received SESSION_STARTED")

        # Retirement - Update data strucutres
        elif packet.m_eventStringCode == PacketEventData.EventPacketType.RETIREMENT:
            TelData.processRetirementEvent(packet)

        # Overtake - Update overtake records list
        elif packet.m_eventStringCode == PacketEventData.EventPacketType.OVERTAKE:
            overtake_obj = TelData.getOvertakeObj(packet.mEventDetails.overtakingVehicleIdx,
                                                        packet.mEventDetails.beingOvertakenVehicleIdx)
            if overtake_obj:
                g_overtakes_history.insert(overtake_obj)

    @staticmethod
    def handleParticipants(packet: PacketParticipantsData) -> None:
        """
        A static method to handle participants data packet.

        Arguments:
            - packet: PacketParticipantsData object
        """

        TelData.processParticipantsUpdate(packet)
        return

    @staticmethod
    def handleCarTelemetry(packet: PacketCarTelemetryData) -> None:
        """
        Handle car telemetry data and process the car telemetry update.

        Arguments
            packet - PacketCarTelemetryData object
        """

        TelData.processCarTelemetryUpdate(packet)
        return

    @staticmethod
    def handleCarStatus(packet: PacketCarStatusData) -> None:
        """
        Handle car status data and process the car status update.

        Arguments
            packet - PacketCarStatusData object
        """

        TelData.processCarStatusUpdate(packet)
        return

    @staticmethod
    def handleFinalClassification(packet: PacketFinalClassificationData) -> None:
        """
        Handle and process the final classification packet. This is sent out at the end of the event when the game
            displays the final classification table

        Arguments
            packet - PacketCarStatusData object
        """
        logging.info('Received Final Classification Packet.')
        final_json = TelData.processFinalClassificationUpdate(packet)

        # Perform the auto save stuff only for races
        _, _, event_type_str, _, _, _, _, _, _ = TelData.getGlobals()
        if event_type_str:
            unsupported_event_types = [
                SessionType.PRACTICE_1,
                SessionType.PRACTICE_2,
                SessionType.PRACTICE_3,
                SessionType.SHORT_PRACTICE,
                SessionType.TIME_TRIAL,
                SessionType.UNKNOWN
            ]
            is_event_supported = True
            for event_type in unsupported_event_types:
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
        return

    @staticmethod
    def handleSessionHistory(packet: PacketSessionHistoryData) -> None:
        """
        Handle and process the session history update.

        Arguments
            packet - PacketSessionHistoryData object
        """

        TelData.processSessionHistoryUpdate(packet)
        return

    @staticmethod
    def handleTyreSets(packet: PacketTyreSetsData) -> None:
        """
        Handle and process the tyre sets update.

        Arguments
            packet - PacketTyreSetsData object
        """

        TelData.processTyreSetsUpdate(packet)
        return
