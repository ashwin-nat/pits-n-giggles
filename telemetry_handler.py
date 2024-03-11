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

from telemetry_manager import F12023TelemetryManager
from f1_types import *
from packet_cap import F1PacketCapture
from overtake_analyzer import OvertakeAnalyzer, OvertakeAnalyzerMode
import telemetry_data as TelData
from threading import Lock
from enum import Enum
from typing import Optional, List, Tuple, Dict
from datetime import datetime
import os
import logging
import json

class PacketCaptureMode(Enum):
    """Enum representing packet capture modes."""
    DISABLED = 'disabled'
    ENABLED = 'enabled'
    ENABLED_WITH_AUTOSAVE = 'enabled-with-autosave'

g_packet_capture_table = F1PacketCapture()
g_packet_capture_table_lock = Lock()
g_pkt_cap_mode = PacketCaptureMode.DISABLED
g_num_active_cars = 0
g_overtakes_history = []
g_overtakes_table_lock = Lock()
g_post_race_data_autosave = False
g_directory_mapping = {}

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

def initAutosaves(post_race_data_autosave: bool):
    global g_overtakes_history
    global g_overtakes_table_lock
    global g_post_race_data_autosave
    g_overtakes_history = []
    g_overtakes_table_lock = Lock()
    g_post_race_data_autosave = post_race_data_autosave

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

def addRawPacket(packet: List[bytes]):
    """
    Add raw packet to the packet capture table.

    Parameters:
    - packet (List[bytes]): The raw packet data.

    Returns:
    None
    """
    global g_packet_capture_table
    global g_packet_capture_table_lock
    with g_packet_capture_table_lock:
        g_packet_capture_table.add(packet)

def getTimestampStr() -> str:
    return datetime.now().strftime("%Y_%m_%d_%H_%M_%S")

def dumpPktCapToFile(file_name: Optional[str] = None, clear_db: bool = False, reason: str = '') -> Tuple[PktSaveStatus, str, int, int]:
    """
    Dump packet capture data to a file.

    Parameters:
    - file_name (Optional[str]): The name of the file to save. Default is None.
    - clear_db (bool): Whether to clear the packet capture database. Default is False.
    - reason (str): Reason for dumping the packet capture data.

    Returns:
    Tuple[PktSaveStatus, str, int, int]: A tuple representing the save status, file name, number of packets, and number of bytes.
    """
    global g_pkt_cap_mode

    if g_pkt_cap_mode == PacketCaptureMode.DISABLED:
        return PktSaveStatus.DISABLED, None, 0, 0

    global g_packet_capture_table
    global g_packet_capture_table_lock

    with g_packet_capture_table_lock:
        try:
            if not file_name:
                global g_directory_mapping
                file_name = g_directory_mapping['packet-captures'] + \
                            'capture_' + getTimestampStr() + \
                            '.' + g_packet_capture_table.file_extension
            file_name, num_packets, num_bytes = g_packet_capture_table.dumpToFile(file_name)
            if clear_db:
                g_packet_capture_table.clear()
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
    global g_overtakes_table_lock
    with g_overtakes_table_lock:
        if not final_classification_received:
            if len(g_overtakes_history) == 0:
                return GetOvertakesStatus.NO_DATA, {}
            else:
                return GetOvertakesStatus.RACE_ONGOING, OvertakeAnalyzer(
                    input_mode=OvertakeAnalyzerMode.INPUT_MODE_LIST,
                    input=g_overtakes_history).toJSON(
                        driver_name=driver_name,
                        is_case_sensitive=True)
        else:
            return GetOvertakesStatus.RACE_COMPLETED, OvertakeAnalyzer(
                input_mode=OvertakeAnalyzerMode.INPUT_MODE_LIST,
                input=g_overtakes_history).toJSON(
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
        global g_overtakes_table_lock
        with g_overtakes_table_lock:
            overtake_analyzer = OvertakeAnalyzer(
                input_mode=OvertakeAnalyzerMode.INPUT_MODE_LIST,
                input=g_overtakes_history)
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

class F12023TelemetryHandler:
    """
    Handles incoming F1 2023 telemetry data. Handles the various types of incoming packets

    Attributes:
    - m_manager (F12023TelemetryManager): The telemetry manager instance.
    - m_raw_packet_capture (PacketCaptureMode): The raw packet capture mode.
    """

    def __init__(self, port: int, raw_packet_capture: PacketCaptureMode = PacketCaptureMode.DISABLED,
                 replay_server: bool = False) -> None:
        """
        Initialize F12023TelemetryHandler.

        Parameters:
        - port (int): The port number for telemetry.
        - raw_packet_capture (PacketCaptureMode): The mode for raw packet capture. Default is PacketCaptureMode.DISABLED.

        Returns:
        None
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

        Returns:
        None
        """

        # self.m_manager.registerCallback(F1PacketType.MOTION, F12023TelemetryHandler.handleMotion)
        self.m_manager.registerCallback(F1PacketType.SESSION, F12023TelemetryHandler.handleSessionData)
        self.m_manager.registerCallback(F1PacketType.LAP_DATA, F12023TelemetryHandler.handleLapData)
        self.m_manager.registerCallback(F1PacketType.EVENT, F12023TelemetryHandler.handleEvent)
        self.m_manager.registerCallback(F1PacketType.PARTICIPANTS, F12023TelemetryHandler.handleParticipants)
        # self.m_manager.registerCallback(F1PacketType.CAR_SETUPS, F12023TelemetryHandler.handleCarSetups)
        self.m_manager.registerCallback(F1PacketType.CAR_TELEMETRY, F12023TelemetryHandler.handleCarTelemetry)
        self.m_manager.registerCallback(F1PacketType.CAR_STATUS, F12023TelemetryHandler.handleCarStatus)
        self.m_manager.registerCallback(F1PacketType.FINAL_CLASSIFICATION, F12023TelemetryHandler.handleFinalClassification)
        # self.m_manager.registerCallback(F1PacketType.LOBBY_INFO, F12023TelemetryHandler.handleLobbyInfo)
        self.m_manager.registerCallback(F1PacketType.CAR_DAMAGE, F12023TelemetryHandler.handleCarDamage)
        self.m_manager.registerCallback(F1PacketType.SESSION_HISTORY, F12023TelemetryHandler.handleSessionHistory)
        self.m_manager.registerCallback(F1PacketType.TYRE_SETS, F12023TelemetryHandler.handleTyreSets)
        # self.m_manager.registerCallback(F1PacketType.MOTION_EX, F12023TelemetryHandler.handleMotionEx)

        if self.m_raw_packet_capture != PacketCaptureMode.DISABLED:
            self.m_manager.registerRawPacketCallback(F12023TelemetryHandler.handleRawPacket)

    @staticmethod
    def handleRawPacket(packet: List[bytes]) -> None:
        """
        Handle raw telemetry packet.

        Parameters:
        - packet (List[bytes]): The raw telemetry packet.

        Returns:
        None
        """
        addRawPacket(packet)

    @staticmethod
    def handleMotion(packet: PacketMotionData) -> None:
        """
        Handle motion telemetry packet.

        Parameters:
        - packet (PacketMotionData): The motion telemetry packet.

        Returns:
        None
        """
        return

    @staticmethod
    def handleSessionData(packet: PacketSessionData) -> None:
        """
        Handle session data telemetry packet.

        Parameters:
        - packet (PacketSessionData): The session data telemetry packet.
        """
        if TelData.processSessionUpdate(packet):
            logging.info("Session UID changed")
            TelData.processSessionStarted()

    @staticmethod
    def handleLapData(packet: PacketLapData) -> None:
        """
        Handle lap data telemetry packet.

        Parameters:
        - packet (PacketLapData): The lap data telemetry packet.

        Returns:
        None
        """

        TelData.processLapDataUpdate(packet)

    @staticmethod
    def handleEvent(packet: PacketEventData) -> None:
        """Handle the Event packet

        Args:
            packet (PacketEventData): The parsed object containing the event data packet's contents
        """
        global g_overtakes_table_lock
        global g_overtakes_history
        global g_num_active_cars
        if packet.m_eventStringCode == PacketEventData.EventPacketType.BUTTON_STATUS:
            # explicitly handle this bullshit first because this just adds unnecessary load
            return
        elif packet.m_eventStringCode == PacketEventData.EventPacketType.FASTEST_LAP:
            TelData.processFastestLapUpdate(packet)
        elif packet.m_eventStringCode == PacketEventData.EventPacketType.SESSION_STARTED:
            g_num_active_cars = 0
            TelData.processSessionStarted()
            # Clear the list regardless of event type
            with g_overtakes_table_lock:
                g_overtakes_history.clear()
            logging.info("Received SESSION_STARTED")
        elif packet.m_eventStringCode == PacketEventData.EventPacketType.RETIREMENT:
            TelData.processRetirementEvent(packet)
        elif packet.m_eventStringCode == PacketEventData.EventPacketType.OVERTAKE:
            overtake_csv_str = TelData.getOvertakeString(packet.mEventDetails.overtakingVehicleIdx,
                                                        packet.mEventDetails.beingOvertakenVehicleIdx)
            if overtake_csv_str:
                with g_overtakes_table_lock:
                    # Experimental input sanitizer
                    if len(g_overtakes_history) > 0 and g_overtakes_history[-1] == overtake_csv_str:
                        logging.debug("not adding repeated overtake string " + overtake_csv_str)
                    else:
                        g_overtakes_history.append(overtake_csv_str)
        return

    @staticmethod
    def handleParticipants(packet: PacketParticipantsData) -> None:

        TelData.processParticipantsUpdate(packet)
        return

    @staticmethod
    def handleCarSetups(packet: PacketCarSetupData) -> None:

        return

    @staticmethod
    def handleCarTelemetry(packet: PacketCarTelemetryData) -> None:

        TelData.processCarTelemetryUpdate(packet)
        return

    @staticmethod
    def handleCarStatus(packet: PacketCarStatusData) -> None:

        TelData.processCarStatusUpdate(packet)
        return

    @staticmethod
    def handleFinalClassification(packet: PacketFinalClassificationData) -> None:
        logging.info('Received Final Classification Packet.')
        final_json = TelData.processFinalClassificationUpdate(packet)

        # Perform the auto save stuff only for races
        _, _, event_type_str, _, _, _, _, _, _ = TelData.getGlobals()
        global g_overtakes_table_lock
        global g_directory_mapping
        supported_event_types = [str(SessionType.RACE), str(SessionType.RACE_2), str(SessionType.RACE_3)]
        is_event_supported = False
        for event_type in supported_event_types:
            if event_type in event_type_str:
                is_event_supported = True
                break
        if is_event_supported:

            global g_directory_mapping
            event_str = TelData.getEventInfoStr()
            if not event_str:
                return
            # Capture the packets if required
            global g_pkt_cap_mode
            if g_pkt_cap_mode == PacketCaptureMode.ENABLED_WITH_AUTOSAVE:
                file_name = 'capture_' + event_str + getTimestampStr() + \
                    F1PacketCapture.file_extension
                file_name = g_directory_mapping["packet-captures"] + file_name
                dumpPktCapToFile(file_name=file_name,reason='Final Classification')

            # Save the JSON data
            global g_post_race_data_autosave
            if g_post_race_data_autosave:
                with g_overtakes_table_lock:
                    player_name = TelData.getPlayerName()
                    overtake_analyzer = OvertakeAnalyzer(
                                            input_mode=OvertakeAnalyzerMode.INPUT_MODE_LIST,
                                            input=g_overtakes_history)
                    overtake_analyzer.getFormattedString(driver_name=player_name, is_case_sensitive=True)
                    final_json['overtakes'] = {
                        'records' : g_overtakes_history
                    }
                    # Add the new keys directly to the top level of final_json
                    final_json['overtakes'].update(
                        overtake_analyzer.toJSON(
                            driver_name=player_name,
                            is_case_sensitive=True))
                final_json_file_name = g_directory_mapping['race-info'] + 'race_info_' + \
                        event_str + getTimestampStr() + '.json'
                writeDictToJsonFile(final_json, final_json_file_name)
                logging.info("Wrote race info to " + final_json_file_name)

        return

    @staticmethod
    def handleLobbyInfo(packet: PacketLobbyInfoData) -> None:
        # print('Received Lobby Info Packet. ' + str(packet))
        return

    @staticmethod
    def handleCarDamage(packet: PacketCarDamageData) -> None:

        TelData.processCarDamageUpdate(packet)
        return

    @staticmethod
    def handleSessionHistory(packet: PacketSessionHistoryData) -> None:

        TelData.processSessionHistoryUpdate(packet)
        return

    @staticmethod
    def handleTyreSets(packet: PacketTyreSetsData) -> None:

        TelData.processTyreSetsUpdate(packet)
        return

    @staticmethod
    def handleMotionEx(packet: PacketMotionExData) -> None:

        return
