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
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

import apps.backend.state_mgmt_layer.telemetry_state as TelState
import lib.race_analyzer as RaceAnalyzer
from apps.backend.common.png_logger import getLogger
from lib.button_debouncer import ButtonDebouncer
from lib.f1_types import (F1PacketType, PacketCarDamageData,
                          PacketCarSetupData, PacketCarStatusData,
                          PacketCarTelemetryData, PacketEventData,
                          PacketFinalClassificationData, PacketLapData,
                          PacketMotionData, PacketParticipantsData,
                          PacketSessionData, PacketSessionHistoryData,
                          PacketTimeTrialData, PacketTyreSetsData,
                          SessionType23, SessionType24)
from lib.inter_task_communicator import AsyncInterTaskCommunicator
from lib.packet_forwarder import AsyncUDPForwarder
from lib.telemetry_manager import AsyncF1TelemetryManager

# -------------------------------------- TYPE DEFINITIONS --------------------------------------------------------------

# -------------------------------------- GLOBALS -----------------------------------------------------------------------

g_post_race_data_autosave: bool = False
g_directory_mapping: Dict[str, str] = {}
g_udp_custom_action_code: Optional[int] = None
g_udp_tyre_delta_action_code: Optional[int] = None
g_last_session_uid: Optional[int] = None
g_data_cleared_this_session: bool = False
g_final_classification_processed: bool = False
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
    else:
        png_logger.debug("No forwarding targets defined. Not registering task.")

# -------------------------------------- THREADS -----------------------------------------------------------------------

async def udpForwardingTask(forwarding_targets: List[Tuple[str, int]]) -> None:

    udp_forwarder = AsyncUDPForwarder(forwarding_targets, png_logger)
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

    event_str = TelState.getEventInfoStr()
    if not event_str:
        return

    # Save the JSON data
    global g_post_race_data_autosave
    if g_post_race_data_autosave:
        # Add the overtakes as well
        final_json['overtakes'] = {
            'records': [record.toJSON() for record in TelState.getOvertakeRecords()]
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

async def clearAllDataStructures() -> None:
    TelState.processSessionStarted()
    global g_data_cleared_this_session, g_final_classification_processed
    g_data_cleared_this_session = True
    g_final_classification_processed = False

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
            logger=png_logger,
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

        if self.m_should_forward:
            @self.m_manager.on_raw_packet()
            async def handleRawPacket(packet: List[bytes]) -> None:
                """
                Handle raw telemetry packet.
                Parameters:
                    packet (List[bytes]): The raw telemetry packet.
                """
                await AsyncInterTaskCommunicator().send("packet-forward", packet)

        @self.m_manager.on_packet(F1PacketType.SESSION)
        async def handleSessionData(packet: PacketSessionData) -> None:
            """
            Handle session data telemetry packet.

            Parameters:
                packet (PacketSessionData): The session data telemetry packet.
            """

            if packet.m_sessionDuration == 0:
                png_logger.info("Session duration is 0. clearing data structures")
                clearAllDataStructures()

            elif TelState.processSessionUpdate(packet):
                png_logger.info("Session UID changed. clearing data structures")
                clearAllDataStructures()

        @self.m_manager.on_packet(F1PacketType.LAP_DATA)
        async def processLapDataUpdate(packet: PacketLapData) -> None:
            """Update the data structures with lap data

            Args:
                packet (PacketLapData): Lap Data packet
            """

            if TelState._driver_data.m_session_info.m_total_laps is not None:
                TelState._driver_data.processLapDataUpdate(packet)
                TelState._driver_data.setRaceOngoing()

        @self.m_manager.on_packet(F1PacketType.EVENT)
        async def handleEvent(packet: PacketEventData) -> None:
            """Handle the Event packet

            Args:
                packet (PacketEventData): The parsed object containing the event data packet's contents
            """

            # Define the handler functions in a dictionary
            event_handler: Dict[PacketEventData.EventPacketType, Callable[[PacketEventData], Awaitable[None]]] = {
                PacketEventData.EventPacketType.BUTTON_STATUS: handleButtonStatus,
                PacketEventData.EventPacketType.FASTEST_LAP: processFastestLapUpdate,
                PacketEventData.EventPacketType.SESSION_STARTED: handeSessionStartEvent,
                PacketEventData.EventPacketType.RETIREMENT: processRetirementEvent,
                PacketEventData.EventPacketType.OVERTAKE: processOvertakeEvent,
                PacketEventData.EventPacketType.COLLISION: processCollisionsEvent,
                PacketEventData.EventPacketType.FLASHBACK: handleFlashBackEvent,
                PacketEventData.EventPacketType.START_LIGHTS: handleStartLightsEvent,
            }.get(packet.m_eventCode)

            if event_handler:
                await event_handler(packet)

        @self.m_manager.on_packet(F1PacketType.PARTICIPANTS)
        async def processParticipantsUpdate(packet: PacketParticipantsData) -> None:
            """Update the data strucutre with participants information

            Args:
                packet (PacketParticipantsData): The pariticpants info packet
            """

            TelState._driver_data.processParticipantsUpdate(packet)

        @self.m_manager.on_packet(F1PacketType.CAR_TELEMETRY)
        async def processCarTelemetryUpdate(packet: PacketCarTelemetryData) -> None:
            """Update the data structure with the car telemetry information

            Args:
                packet (PacketCarTelemetryData): The car telemetry update packet
            """

            TelState._driver_data.processCarTelemetryUpdate(packet)
            TelState._driver_data.setRaceOngoing()

        @self.m_manager.on_packet(F1PacketType.CAR_STATUS)
        async def processCarStatusUpdate(packet: PacketCarStatusData) -> None:
            """Update the data structures with car status information

            Args:
                packet (PacketCarStatusData): The car status update packet
            """

            TelState._driver_data.processCarStatusUpdate(packet)
            TelState._driver_data.setRaceOngoing()

        @self.m_manager.on_packet(F1PacketType.FINAL_CLASSIFICATION)
        async def handleFinalClassification(packet: PacketFinalClassificationData) -> None:
            """
            Handle and process the final classification packet. This is sent out at the end of the event when the game
                displays the final classification table

            Arguments
                packet - PacketCarStatusData object
            """
            global g_final_classification_processed
            if g_final_classification_processed:
                png_logger.debug('Session UID %d final classification already processed.', packet.m_header.m_sessionUID)
                return
            png_logger.info('Received Final Classification Packet.')
            final_json = TelState.processFinalClassificationUpdate(packet)
            g_final_classification_processed = True

            # Perform the auto save stuff only for races
            if event_type_str := str(TelState.getSessionInfo().m_session_type):
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

            # Uncomment the below lines for profiling - Kill the process after one session
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

        @self.m_manager.on_packet(F1PacketType.CAR_DAMAGE)
        async def processCarDamageUpdate(packet: PacketCarDamageData):
            """Update the data strucutres with car damage information

            Args:
                packet (PacketCarDamageData): The car damage update packet
            """

            TelState._driver_data.processCarDamageUpdate(packet)
            TelState._driver_data.setRaceOngoing()

        @self.m_manager.on_packet(F1PacketType.SESSION_HISTORY)
        async def processSessionHistoryUpdate(packet: PacketSessionHistoryData):
            """Update the data structures with session history information

            Args:
                packet (PacketSessionHistoryData): The session history update packet
            """

            TelState._driver_data.processSessionHistoryUpdate(packet)
            TelState._driver_data.setRaceOngoing()

        @self.m_manager.on_packet(F1PacketType.TYRE_SETS)
        async def processTyreSetsUpdate(packet: PacketTyreSetsData) -> None:
            """Update the data structures with tyre history information

            Args:
                packet (PacketTyreSetsData): The tyre history update packet
            """

            TelState._driver_data.processTyreSetsUpdate(packet)
            TelState._driver_data.setRaceOngoing()

        @self.m_manager.on_packet(F1PacketType.MOTION)
        async def processMotionUpdate(packet: PacketMotionData) -> None:
            """Update the data structures with motion information

            Args:
                packet (PacketMotionData): The motion update packet
            """

            TelState._driver_data.processMotionUpdate(packet)

        @self.m_manager.on_packet(F1PacketType.CAR_SETUPS)
        async def processCarSetupsUpdate(packet: PacketCarSetupData) -> None:
            """Update the data structures with car setup information

            Args:
                packet (PacketCarSetupData): The car setup update packet
            """

            if not TelState._driver_data.m_process_car_setups:
                return
            TelState._driver_data.processCarSetupsUpdate(packet)

        @self.m_manager.on_packet(F1PacketType.TIME_TRIAL)
        async def processTimeTrialUpdate(packet: PacketTimeTrialData) -> None:
            """Update the data structures with time trial information

            Args:
                packet (PacketTimeTrialData): The time trial update packet
            """

            TelState._driver_data.processTimeTrialUpdate(packet)

        async def handeSessionStartEvent(packet: PacketEventData) -> None:
            """
            Handle and process the session start event

            Args:
                packet (PacketEventData): The parsed object containing the session start packet's contents.
            """

            global g_last_session_uid
            session_uid = packet.m_header.m_sessionUID

            g_last_session_uid = session_uid
            await clearAllDataStructures()

        global g_button_debouncer

        # Function to handle BUTTON_STATUS action
        async def handleButtonStatus(packet: PacketEventData) -> None:
            """
            Handle and process the button press event

            Args:
                packet (PacketEventData): The parsed object containing the button status packet's contents.
            """

            if (g_udp_custom_action_code is not None) and \
            (packet.mEventDetails.isUDPActionPressed(g_udp_custom_action_code)) and \
            (g_button_debouncer.onButtonPress(g_udp_custom_action_code)):
                png_logger.debug('UDP action %d pressed', g_udp_custom_action_code)
                await TelState.processCustomMarkerCreate()

            if (g_udp_tyre_delta_action_code is not None) and \
            (packet.mEventDetails.isUDPActionPressed(g_udp_tyre_delta_action_code)) and \
            (g_button_debouncer.onButtonPress(g_udp_tyre_delta_action_code)):
                png_logger.debug('UDP action %d pressed', g_udp_tyre_delta_action_code)
                await TelState.processTyreDeltaSound()

        async def handleFlashBackEvent(packet: PacketEventData) -> None:
            """
            Handle and process the flashback event

            Args:
                packet (PacketEventData): The parsed object containing the flashback packet's contents.
            """
            png_logger.info(f"Flashback event received. Frame ID = {packet.mEventDetails.flashbackFrameIdentifier}")

        async def handleStartLightsEvent(packet: PacketEventData) -> None:
            """
            Handle and process the start lights event

            Args:
                packet (PacketEventData): The parsed object containing the start lights packet's contents.
            """
            # In case session start was missed, clear data structures
            png_logger.debug(f"Start lights event received. Lights = {packet.mEventDetails.numLights}")
            if packet.mEventDetails.numLights == 1:
                png_logger.info("Session start was missed. Clearing data structures in start lights event")
                global g_last_session_uid, g_data_cleared_this_session
                session_uid = packet.m_header.m_sessionUID

                if session_uid != g_last_session_uid:
                    g_last_session_uid = session_uid
                    g_data_cleared_this_session = False

                if not g_data_cleared_this_session:
                    await clearAllDataStructures()
                else:
                    png_logger.debug("Not clearing data structures in start lights event")

        async def processFastestLapUpdate(packet: PacketEventData) -> None:
            """Update the data structures with the fastest lap

            Args:
                packet (PacketEventData): Fastest lap Event packet
            """

            TelState._driver_data.processFastestLapUpdate(packet.mEventDetails)

        async def processRetirementEvent(packet: PacketEventData) -> None:
            """Update the data structures with the driver retirement udpate

            Args:
                packet (PacketEventData): Retirement event packet
            """

            TelState._driver_data.processRetirement(packet.mEventDetails)

        async def processCollisionsEvent(packet: PacketEventData) -> None:
            """Update the data structures with collisions event udpate.

            Args:
                packet (PacketEventData): The event packet
            """

            record: PacketEventData.Collision = packet.mEventDetails
            TelState._driver_data.processCollisionEvent(record)

        async def processOvertakeEvent(packet: PacketEventData) -> None:
            """Add the overtake event to the tracker

            Args:
                packet (PacketEventData): Incoming event packet
            """
            record: PacketEventData.Overtake = packet.mEventDetails
            if (overtake_obj := TelState.getOvertakeObj(record.overtakingVehicleIdx,
                                                        record.beingOvertakenVehicleIdx)):
                TelState._driver_data.m_overtakes_history.insert(overtake_obj)

        async def processCollisionsEvent(packet: PacketEventData) -> None:
            """Update the data structures with collisions event udpate.

            Args:
                packet (PacketEventData): The event packet
            """

            record: PacketEventData.Collision = packet.mEventDetails
            TelState._driver_data.processCollisionEvent(record)