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

import asyncio
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import lib.race_analyzer as RaceAnalyzer
import src.telemetry_data as TelData
from lib.button_debouncer import ButtonDebouncer
from lib.f1_types import (F1PacketType, PacketEventData,
                          PacketFinalClassificationData, PacketSessionData,
                          SessionType23, SessionType24)
from lib.inter_task_communicator import AsyncInterTaskCommunicator
from lib.packet_forwarder import AsyncUDPForwarder
from src.png_logger import getLogger
from src.telemetry_manager import AsyncF1TelemetryManager

# -------------------------------------- TYPE DEFINITIONS --------------------------------------------------------------

# -------------------------------------- GLOBALS -----------------------------------------------------------------------

g_post_race_data_autosave: bool = False
g_directory_mapping: Dict[str, str] = {}
g_udp_custom_action_code: Optional[int] = None
g_udp_tyre_delta_action_code: Optional[int] = None
g_completed_session_uid_set: set[int] = set()
g_button_debouncer = ButtonDebouncer()
png_logger = getLogger()

# -------------------------------------- INITIALIZATION ----------------------------------------------------------------

def initTelemetryGlobals(
    post_race_data_autosave: bool,
    udp_custom_action_code: Optional[int],
    udp_tyre_delta_action_code: Optional[int]) -> None:
    """Initialise the autosave settings

    Args:
        post_race_data_autosave (bool): Save JSON file after race
        udp_custom_action_code (Optional[int]): UDP action code to set marker
        udp_tyre_delta_action_code (Optional[int]): UDP action code to play tyre delta sound
    """

    global g_post_race_data_autosave
    global g_udp_custom_action_code
    global g_udp_tyre_delta_action_code
    g_post_race_data_autosave = post_race_data_autosave
    g_udp_custom_action_code = udp_custom_action_code
    g_udp_tyre_delta_action_code = udp_tyre_delta_action_code

def initDirectories() -> None:
    """
    Initialize the necessary directories for storing race information
    This function creates a directory structure based on the current date if it does not already exist.
    """
    def ensureDirectoryExists(directory: str) -> None:
        """
        Ensure that the specified directory exists. If it doesn't, create it along with any missing parent directories.

        Parameters:
        - directory (str): The path of the directory to be checked or created.
        """
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            png_logger.info("Directory '%s' created.", directory)

    global g_directory_mapping
    ts_prefix = datetime.now().strftime("%Y_%m_%d")
    g_directory_mapping['race-info'] = f"data/{ts_prefix}/race-info/"

    for directory in g_directory_mapping.values():
        ensureDirectoryExists(directory)

def initForwarder(forwarding_targets: List[Tuple[str, int]], tasks: List[asyncio.Task]) -> None:
    """Init the forwarding thread, if targets are defined

    Args:
        forwarding_targets (List[Tuple[str, int]]): Forwarding Targets list
        tasks (List[asyncio.Task]): List of tasks
    """

    # Register the task only if targets are defined
    if forwarding_targets:
        tasks.append(asyncio.create_task(udpForwardingTask(forwarding_targets), name="UDP Forwarder Task"))

# -------------------------------------- THREADS -----------------------------------------------------------------------

async def udpForwardingTask(forwarding_targets: List[Tuple[str, int]]) -> None:

    udp_forwarder = AsyncUDPForwarder(forwarding_targets)
    png_logger.info(f"Initialised forwarder. Targets={forwarding_targets}")
    while True:
        packet = await AsyncInterTaskCommunicator().receive("packet-forward")
        assert packet is not None
        await udp_forwarder.forward(packet)

# -------------------------------------- UTILITIES ---------------------------------------------------------------------

def getTimestampStr() -> str:
    """
    Get the current timestamp as a string formatted as year_month_day_hour_minute_second.

    Returns:
        str: A string representing the current timestamp.
    """
    return datetime.now().strftime("%Y_%m_%d_%H_%M_%S")

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

    event_str = TelData.getEventInfoStr()
    if not event_str:
        return

    # Save the JSON data
    global g_post_race_data_autosave
    if g_post_race_data_autosave:
        # Add the overtakes as well
        final_json['overtakes'] = {
            'records': [record.toJSON() for record in TelData.getOvertakeRecords()]
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

async def clearAllDataStructures(_dummy_arg=None) -> None:
    """Clear all data structures.
    """

    TelData.processSessionStarted()
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
        self.m_manager = AsyncF1TelemetryManager(
            port_number=port,
            replay_server=replay_server
        )
        self.m_should_forward = bool(forwarding_targets)
        self.registerCallbacks()

    async def run(self):
        """
        Run the telemetry handler.

        Returns:
        None
        """
        await self.m_manager.run()

    def registerCallbacks(self) -> None:
        """
        Register callback functions for different types of telemetry packets.
        """
        # Mapping of packet types to their corresponding handler functions
        self.m_manager.registerCallbacks({
            F1PacketType.SESSION: F1TelemetryHandler.handleSessionData,
            F1PacketType.LAP_DATA: TelData.processLapDataUpdate,
            F1PacketType.EVENT: F1TelemetryHandler.handleEvent,
            F1PacketType.PARTICIPANTS: TelData.processParticipantsUpdate,
            F1PacketType.CAR_TELEMETRY: TelData.processCarTelemetryUpdate,
            F1PacketType.CAR_STATUS: TelData.processCarStatusUpdate,
            F1PacketType.FINAL_CLASSIFICATION: F1TelemetryHandler.handleFinalClassification,
            F1PacketType.CAR_DAMAGE: TelData.processCarDamageUpdate,
            F1PacketType.SESSION_HISTORY: TelData.processSessionHistoryUpdate,
            F1PacketType.TYRE_SETS: TelData.processTyreSetsUpdate,
            F1PacketType.MOTION: TelData.processMotionUpdate,
            F1PacketType.CAR_SETUPS: TelData.processCarSetupsUpdate,
            F1PacketType.TIME_TRIAL: TelData.processTimeTrialUpdate,
        })

        # If the flag is set, register the raw packet callback
        if self.m_should_forward:
            self.m_manager.registerRawPacketCallback(F1TelemetryHandler.handleRawPacket)

    @staticmethod
    async def handleRawPacket(packet: List[bytes]) -> None:
        """
        Handle raw telemetry packet.

        Parameters:
            packet (List[bytes]): The raw telemetry packet.
        """

        # InterThreadCommunicator().send("packet-forward", packet)
        await AsyncInterTaskCommunicator().send("packet-forward", packet)

    @staticmethod
    async def handleSessionData(packet: PacketSessionData) -> None:
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
    async def handleEvent(packet: PacketEventData) -> None:
        """Handle the Event packet

        Args:
            packet (PacketEventData): The parsed object containing the event data packet's contents
        """

        global g_button_debouncer

        # Function to handle BUTTON_STATUS action
        async def handle_button_status(packet: PacketEventData):
            if (g_udp_custom_action_code is not None) and \
            (packet.mEventDetails.isUDPActionPressed(g_udp_custom_action_code)) and \
            (g_button_debouncer.onButtonPress(g_udp_custom_action_code)):
                png_logger.debug('UDP action %d pressed', g_udp_custom_action_code)
                await TelData.processCustomMarkerCreate()

            if (g_udp_tyre_delta_action_code is not None) and \
            (packet.mEventDetails.isUDPActionPressed(g_udp_tyre_delta_action_code)) and \
            (g_button_debouncer.onButtonPress(g_udp_tyre_delta_action_code)):
                png_logger.debug('UDP action %d pressed', g_udp_tyre_delta_action_code)
                await TelData.processTyreDeltaSound()

        # Define the handler functions in a dictionary
        event_handler = {
            PacketEventData.EventPacketType.BUTTON_STATUS: handle_button_status,
            PacketEventData.EventPacketType.FASTEST_LAP: TelData.processFastestLapUpdate,
            PacketEventData.EventPacketType.SESSION_STARTED: clearAllDataStructures,
            PacketEventData.EventPacketType.RETIREMENT: TelData.processRetirementEvent,
            PacketEventData.EventPacketType.OVERTAKE: TelData.processOvertakeEvent,
            PacketEventData.EventPacketType.COLLISION: TelData.processCollisionsEvent,
        }.get(packet.m_eventCode)

        if event_handler:
            await event_handler(packet)

    @staticmethod
    async def handleFinalClassification(packet: PacketFinalClassificationData) -> None:
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
        if event_type_str := str(TelData.getSessionInfo().m_session_type):
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


            # # Cancel all tasks except itself
            # import asyncio
            # current_task = asyncio.current_task()
            # for task in asyncio.all_tasks():
            #     if task is not current_task:
            #         task.cancel()

            # # Option 1: Self-cancel
            # try:
            #     current_task.cancel()
            # except asyncio.CancelledError:
            #     pass  # Suppress the traceback
            # return  # Ensure it stops running