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
import csv
import logging
from datetime import datetime
from enum import Enum
from threading import Lock
from typing import Optional, List, Tuple, Dict, Any
from collections import namedtuple

try:
    from tqdm import tqdm
except ImportError:
    print("tqdm is not installed. Installing...")
    import subprocess
    subprocess.check_call(["pip3", "install", "tqdm"])
    print("tqdm installation complete.")
    from tqdm import tqdm

from src.telemetry_manager import F12023TelemetryManager
from lib.f1_types import *
from lib.packet_cap import F1PacketCapture
from lib.overtake_analyzer import OvertakeAnalyzer, OvertakeAnalyzerMode
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

    def __init__(self):

        self.m_overtakes_history = []
        self.m_lock = Lock()

# -------------------------------------- GLOBALS -----------------------------------------------------------------------

g_packet_capture_table = PacketCaptureTable()
g_pkt_cap_mode = PacketCaptureMode.DISABLED
g_num_active_cars = 0
g_overtakes_history = OvertakesHistory()
g_post_race_data_autosave = False
g_directory_mapping = {}
g_udp_custom_action_code = None
g_player_recorded_events_history = []

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
    g_directory_mapping['player-markers'] = "data/" + ts_prefix + "/player-markers/"

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
                            '.' + g_packet_capture_table.file_extension
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

def getOvertakeJSON(driver_name: str=None) -> Tuple[GetOvertakesStatus, Dict]:
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
                    input_mode=OvertakeAnalyzerMode.INPUT_MODE_LIST,
                    input=g_overtakes_history.m_overtakes_history).toJSON(
                        driver_name=driver_name,
                        is_case_sensitive=True)
        else:
            return GetOvertakesStatus.RACE_COMPLETED, OvertakeAnalyzer(
                input_mode=OvertakeAnalyzerMode.INPUT_MODE_LIST,
                input=g_overtakes_history.m_overtakes_history).toJSON(
                    driver_name=driver_name,
                    is_case_sensitive=True)

def printOvertakeData(file_name: str=None):
    """Print the overtake data

    Args:
        file_name (str): Name of the csv file with the overtake data. If None, directly gets the data from the list
    """

    player_name = TelData.getPlayerName()
    if file_name:
        overtake_analyzer = OvertakeAnalyzer(
            input_mode=OvertakeAnalyzerMode.INPUT_MODE_FILE,
            input=file_name)
    else:
        global g_overtakes_history
        with g_overtakes_history.m_lock:
            overtake_analyzer = OvertakeAnalyzer(
                input_mode=OvertakeAnalyzerMode.INPUT_MODE_LIST,
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

def writeToCsvFile(g_custom_player_markers: List[str], custom_marker_file_name: str):
    """
    Write the given custom player markers to a CSV file.

    Args:
        g_custom_player_markers (list): The list of custom player markers to be written to the CSV file.
        custom_marker_file_name (str): The name of the CSV file to write the markers to.
    """

    with open(custom_marker_file_name, 'w', encoding='utf-8') as file:
        for marker in g_custom_player_markers:
            file.write(marker + '\n')

def addFunStatsToFinalClassificationJson(final_json: Dict[str, Any]) -> None:
    """
    Add the fun stats to the final classification JSON.

    Arguments:
        final_json (Dict): Dictionary containing JSON data after final classification
    """

    global g_overtakes_history

    # First, overtake stats
    final_json['overtakes'] = {
        'records' : g_overtakes_history.m_overtakes_history
    }

    with g_overtakes_history.m_lock:
        player_name = TelData.getPlayerName()
        overtake_analyzer = OvertakeAnalyzer(
            input_mode=OvertakeAnalyzerMode.INPUT_MODE_LIST,
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
        addFunStatsToFinalClassificationJson(final_json)
        final_json_file_name = g_directory_mapping['race-info'] + 'race_info_' + \
                event_str + getTimestampStr() + '.json'
        writeDictToJsonFile(final_json, final_json_file_name)
        logging.info("Wrote race info to " + final_json_file_name)

    # Save the custom player recorded markers
    global g_player_recorded_events_history
    if len(g_player_recorded_events_history) > 0:
        custom_marker_file_name = g_directory_mapping['race-info'] + 'custom_player_markers_' + \
                event_str + getTimestampStr() + '.csv'
        writeToCsvFile(g_player_recorded_events_history, custom_marker_file_name)
        logging.info(
            f"Wrote {len(g_player_recorded_events_history)} custom player markers to {custom_marker_file_name}")

# -------------------------------------- TELEMETRY PACKET HANDLERS -----------------------------------------------------

class F12023TelemetryHandler:
    """
    Handles incoming F1 2023 telemetry data. Handles the various types of incoming packets

    Attributes:
    - m_manager (F12023TelemetryManager): The telemetry manager instance.
    - m_raw_packet_capture (PacketCaptureMode): The raw packet capture mode.
    """

    def __init__(self,
        port: int,
        raw_packet_capture: PacketCaptureMode = PacketCaptureMode.DISABLED,
        replay_server: bool = False) -> None:
        """
        Initialize F12023TelemetryHandler.

        Parameters:
            - port (int): The port number for telemetry.
            - raw_packet_capture (PacketCaptureMode): The mode for raw packet capture
        """
        self.m_manager = F12023TelemetryManager(port, replay_server)
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

        self.m_manager.registerCallback(F1PacketType.SESSION, F12023TelemetryHandler.handleSessionData)
        self.m_manager.registerCallback(F1PacketType.LAP_DATA, F12023TelemetryHandler.handleLapData)
        self.m_manager.registerCallback(F1PacketType.EVENT, F12023TelemetryHandler.handleEvent)
        self.m_manager.registerCallback(F1PacketType.PARTICIPANTS, F12023TelemetryHandler.handleParticipants)
        self.m_manager.registerCallback(F1PacketType.CAR_TELEMETRY, F12023TelemetryHandler.handleCarTelemetry)
        self.m_manager.registerCallback(F1PacketType.CAR_STATUS, F12023TelemetryHandler.handleCarStatus)
        self.m_manager.registerCallback(F1PacketType.FINAL_CLASSIFICATION, F12023TelemetryHandler.handleFinalClassification)
        self.m_manager.registerCallback(F1PacketType.CAR_DAMAGE, F12023TelemetryHandler.handleCarDamage)
        self.m_manager.registerCallback(F1PacketType.SESSION_HISTORY, F12023TelemetryHandler.handleSessionHistory)
        self.m_manager.registerCallback(F1PacketType.TYRE_SETS, F12023TelemetryHandler.handleTyreSets)

        if self.m_raw_packet_capture != PacketCaptureMode.DISABLED:
            self.m_manager.registerRawPacketCallback(F12023TelemetryHandler.handleRawPacket)

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

        # TODO: clean up order of operations
        if packet.m_sessionDuration == 0:
            logging.info("Session duration is 0. clearing data structures")
            TelData.processSessionStarted()

        if TelData.processSessionUpdate(packet):
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
                player_recorded_event_str = TelData.getPlayerRecordedEventCsvStr(add_to_queue=True)
                if player_recorded_event_str:
                    g_player_recorded_events_history.append(player_recorded_event_str)
                    logging.debug('Player recorded event: ' + player_recorded_event_str)
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
            overtake_csv_str = TelData.getOvertakeString(packet.mEventDetails.overtakingVehicleIdx,
                                                        packet.mEventDetails.beingOvertakenVehicleIdx)
            if overtake_csv_str:
                with g_overtakes_history.m_lock:
                    # Experimental input sanitizer
                    if len(g_overtakes_history.m_overtakes_history) > 0 and \
                        g_overtakes_history.m_overtakes_history[-1] == overtake_csv_str:
                        logging.debug("not adding repeated overtake string " + overtake_csv_str)
                    else:
                        g_overtakes_history.m_overtakes_history.append(overtake_csv_str)

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
