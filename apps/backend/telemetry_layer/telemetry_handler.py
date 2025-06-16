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
import logging
import os
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

import aiofiles

import apps.backend.state_mgmt_layer.telemetry_state as TelState
import lib.race_analyzer as RaceAnalyzer
from lib.button_debouncer import ButtonDebouncer
from lib.config import CaptureSettings
from lib.f1_types import (F1PacketType, PacketCarDamageData,
                          PacketCarSetupData, PacketCarStatusData,
                          PacketCarTelemetryData, PacketEventData,
                          PacketFinalClassificationData, PacketLapData,
                          PacketMotionData, PacketParticipantsData,
                          PacketSessionData, PacketSessionHistoryData,
                          PacketTimeTrialData, PacketTyreSetsData)
from lib.inter_task_communicator import (AsyncInterTaskCommunicator,
                                         FinalClassificationNotification,
                                         ITCMessage)
from lib.telemetry_manager import AsyncF1TelemetryManager

# -------------------------------------- TYPE DEFINITIONS --------------------------------------------------------------

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def setupTelemetryTask(
        port_number: int,
        replay_server: bool,
        logger: logging.Logger,
        capture_settings: CaptureSettings,
        udp_custom_action_code: Optional[int],
        udp_tyre_delta_action_code: Optional[int],
        forwarding_targets: List[Tuple[str, int]],
        ver_str: str,
        tasks: List[asyncio.Task]) -> None:
    """Entry point to start the F1 telemetry server.

    Args:
        port_number (int): Port number for the telemetry client.
        replay_server (bool): Whether to enable the TCP replay debug server.
        logger (logging.Logger): Logger instance
        capture_settings (CaptureSettings): Capture settings
        udp_custom_action_code (Optional[int]): UDP custom action code.
        udp_tyre_delta_action_code (Optional[int]): UDP tyre delta action code.
        forwarding_targets (List[Tuple[str, int]]): List of IP addr port pairs to forward packets to
        ver_str (str): Version string
        tasks (List[asyncio.Task]): List of tasks to be executed
    """

    telemetry_server = F1TelemetryHandler(
        port=port_number,
        forwarding_targets=forwarding_targets,
        logger=logger,
        capture_settings=capture_settings,
        udp_custom_action_code=udp_custom_action_code,
        udp_tyre_delta_action_code=udp_tyre_delta_action_code,
        replay_server=replay_server,
        ver_str=ver_str
    )
    tasks.append(asyncio.create_task(telemetry_server.run(), name="Game Telemetry Listener Task"))

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
        logger: logging.Logger,
        capture_settings: CaptureSettings,
        udp_custom_action_code: Optional[int] = None,
        udp_tyre_delta_action_code: Optional[int] = None,
        replay_server: bool = False,
        ver_str: str = "dev") -> None:
        """
        Initialize F1TelemetryHandler.

        Parameters:
            - port (int): The port number for telemetry.
            - forwarding_targets (List[Tuple[str, int]]): List of IP addr port pairs to forward packets to
            - logger (logging.Logger): Logger
            - capture_settings (CaptureSettings): Capture settings
            - udp_custom_action_code (Optional[int]): UDP custom action code.
            - udp_tyre_delta_action_code (Optional[int]): UDP tyre delta action code
            - replay_server: bool: If true, init in replay mode (TCP). Else init in live mode (UDP)
            - ver_str (str): Version string
        """
        self.m_manager = AsyncF1TelemetryManager(
            port_number=port,
            logger=logger,
            replay_server=replay_server
        )
        self.m_logger: logging.Logger = logger
        self.m_session_state_ref: TelState.SessionState = TelState.getSessionStateRef()

        self.m_directory_mapping: Dict[str, str] = {}
        self.m_last_session_uid: Optional[int] = None
        self.m_data_cleared_this_session: bool = False
        self.m_udp_custom_action_code: Optional[int] = udp_custom_action_code
        self.m_udp_tyre_delta_action_code: Optional[int] = udp_tyre_delta_action_code
        self.m_final_classification_processed: bool = False
        self.m_post_race_data_autosave: bool = capture_settings.post_race_data_autosave
        self.m_capture_settings: CaptureSettings = capture_settings
        self.m_button_debouncer: ButtonDebouncer = ButtonDebouncer()

        self.m_should_forward: bool = bool(forwarding_targets)
        self.m_version: str = ver_str
        self.initDirectories()
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
                self.m_logger.info("Session duration is 0. clearing data structures")
                await self.clearAllDataStructures()

            elif self.m_session_state_ref.processSessionUpdate(packet):
                self.m_logger.info("Session UID changed. clearing data structures")
                await self.clearAllDataStructures()

        @self.m_manager.on_packet(F1PacketType.LAP_DATA)
        async def processLapDataUpdate(packet: PacketLapData) -> None:
            """Update the data structures with lap data

            Args:
                packet (PacketLapData): Lap Data packet
            """

            if self.m_session_state_ref.m_session_info.m_total_laps is not None:
                self.m_session_state_ref.processLapDataUpdate(packet)
                self.m_session_state_ref.setRaceOngoing()

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

            self.m_session_state_ref.processParticipantsUpdate(packet)

        @self.m_manager.on_packet(F1PacketType.CAR_TELEMETRY)
        async def processCarTelemetryUpdate(packet: PacketCarTelemetryData) -> None:
            """Update the data structure with the car telemetry information

            Args:
                packet (PacketCarTelemetryData): The car telemetry update packet
            """

            self.m_session_state_ref.processCarTelemetryUpdate(packet)
            self.m_session_state_ref.setRaceOngoing()

        @self.m_manager.on_packet(F1PacketType.CAR_STATUS)
        async def processCarStatusUpdate(packet: PacketCarStatusData) -> None:
            """Update the data structures with car status information

            Args:
                packet (PacketCarStatusData): The car status update packet
            """

            self.m_session_state_ref.processCarStatusUpdate(packet)
            self.m_session_state_ref.setRaceOngoing()

        @self.m_manager.on_packet(F1PacketType.FINAL_CLASSIFICATION)
        async def handleFinalClassification(packet: PacketFinalClassificationData) -> None:
            """
            Handle and process the final classification packet. This is sent out at the end of the event when the game
                displays the final classification table

            Arguments
                packet - PacketCarStatusData object
            """

            if self.m_final_classification_processed:
                self.m_logger.debug('Session UID %d final classification already processed.', packet.m_header.m_sessionUID)
                return
            self.m_logger.info('Received Final Classification Packet.')
            final_json = self.m_session_state_ref.processFinalClassificationUpdate(packet)
            self.m_final_classification_processed = True

            # Perform the auto save stuff only if configured
            if self._shouldSaveData():
                await self.postGameDumpToFile(final_json)

            # Notify the frontend about the final classification
            session_type = self.m_session_state_ref.m_session_info.m_session_type
            player_info = self.m_session_state_ref.getPlayerDriverInfo()

            if (session_type.isRaceTypeSession() or session_type.isQualiTypeSession()) and player_info:
                player_position = player_info.m_driver_info.position
                message = ITCMessage(
                    m_message_type=ITCMessage.MessageType.FINAL_CLASSIFICATION_NOTIFICATION,
                    m_message=FinalClassificationNotification(player_position)
                )
                await AsyncInterTaskCommunicator().send("frontend-update", message)


            # ------------ PROFILER MODE --------------
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

            self.m_session_state_ref.processCarDamageUpdate(packet)
            self.m_session_state_ref.setRaceOngoing()

        @self.m_manager.on_packet(F1PacketType.SESSION_HISTORY)
        async def processSessionHistoryUpdate(packet: PacketSessionHistoryData):
            """Update the data structures with session history information

            Args:
                packet (PacketSessionHistoryData): The session history update packet
            """

            self.m_session_state_ref.processSessionHistoryUpdate(packet)
            self.m_session_state_ref.setRaceOngoing()

        @self.m_manager.on_packet(F1PacketType.TYRE_SETS)
        async def processTyreSetsUpdate(packet: PacketTyreSetsData) -> None:
            """Update the data structures with tyre history information

            Args:
                packet (PacketTyreSetsData): The tyre history update packet
            """

            self.m_session_state_ref.processTyreSetsUpdate(packet)
            self.m_session_state_ref.setRaceOngoing()

        @self.m_manager.on_packet(F1PacketType.MOTION)
        async def processMotionUpdate(packet: PacketMotionData) -> None:
            """Update the data structures with motion information

            Args:
                packet (PacketMotionData): The motion update packet
            """

            self.m_session_state_ref.processMotionUpdate(packet)

        @self.m_manager.on_packet(F1PacketType.CAR_SETUPS)
        async def processCarSetupsUpdate(packet: PacketCarSetupData) -> None:
            """Update the data structures with car setup information

            Args:
                packet (PacketCarSetupData): The car setup update packet
            """

            if not self.m_session_state_ref.m_process_car_setups:
                return
            self.m_session_state_ref.processCarSetupsUpdate(packet)

        @self.m_manager.on_packet(F1PacketType.TIME_TRIAL)
        async def processTimeTrialUpdate(packet: PacketTimeTrialData) -> None:
            """Update the data structures with time trial information

            Args:
                packet (PacketTimeTrialData): The time trial update packet
            """

            self.m_session_state_ref.processTimeTrialUpdate(packet)

        # We're not using this data, no need to waste CPU cycles processing it.
        # Commenting it out for now
        # @self.m_manager.on_packet(F1PacketType.LAP_POSITIONS)
        # async def processLapPositionsUpdate(packet: PacketLapPositionsData) -> None:
        #     """Update the data structures with lap positions information

        #     Args:
        #         packet (PacketLapPositionsData): The lap positions update packet
        #     """

        #     self.m_session_state_ref.processLapPositionsUpdate(packet)

        async def handeSessionStartEvent(packet: PacketEventData) -> None:
            """
            Handle and process the session start event

            Args:
                packet (PacketEventData): The parsed object containing the session start packet's contents.
            """

            self.m_last_session_uid = packet.m_header.m_sessionUID
            await self.clearAllDataStructures()

        async def handleButtonStatus(packet: PacketEventData) -> None:
            """
            Handle and process the button press event

            Args:
                packet (PacketEventData): The parsed object containing the button status packet's contents.
            """

            if (self.m_udp_custom_action_code is not None) and \
            (packet.mEventDetails.isUDPActionPressed(self.m_udp_custom_action_code)) and \
            (self.m_button_debouncer.onButtonPress(self.m_udp_custom_action_code)):
                self.m_logger.debug('UDP action %d pressed - Custom Marker', self.m_udp_custom_action_code)
                await TelState.processCustomMarkerCreate()

            if (self.m_udp_tyre_delta_action_code is not None) and \
            (packet.mEventDetails.isUDPActionPressed(self.m_udp_tyre_delta_action_code)) and \
            (self.m_button_debouncer.onButtonPress(self.m_udp_tyre_delta_action_code)):
                self.m_logger.debug('UDP action %d pressed - Tyre Delta', self.m_udp_tyre_delta_action_code)
                await TelState.processTyreDeltaSound()

        async def handleFlashBackEvent(packet: PacketEventData) -> None:
            """
            Handle and process the flashback event

            Args:
                packet (PacketEventData): The parsed object containing the flashback packet's contents.
            """
            self.m_logger.info(f"Flashback event received. Frame ID = {packet.mEventDetails.flashbackFrameIdentifier}")

        async def handleStartLightsEvent(packet: PacketEventData) -> None:
            """
            Handle and process the start lights event

            Args:
                packet (PacketEventData): The parsed object containing the start lights packet's contents.
            """
            # In case session start was missed, clear data structures
            self.m_logger.debug(f"Start lights event received. Lights = {packet.mEventDetails.numLights}")
            if packet.mEventDetails.numLights == 1:
                self.m_logger.info("Session start was missed. Clearing data structures in start lights event")
                session_uid = packet.m_header.m_sessionUID

                if session_uid != self.m_last_session_uid:
                    self.m_last_session_uid = session_uid
                    self.m_data_cleared_this_session = False

                if not self.m_data_cleared_this_session:
                    await self.clearAllDataStructures()
                else:
                    self.m_logger.debug("Not clearing data structures in start lights event")

        async def processFastestLapUpdate(packet: PacketEventData) -> None:
            """Update the data structures with the fastest lap

            Args:
                packet (PacketEventData): Fastest lap Event packet
            """

            self.m_session_state_ref.processFastestLapUpdate(packet.mEventDetails)

        async def processRetirementEvent(packet: PacketEventData) -> None:
            """Update the data structures with the driver retirement udpate

            Args:
                packet (PacketEventData): Retirement event packet
            """

            self.m_session_state_ref.processRetirement(packet.mEventDetails)

        async def processCollisionsEvent(packet: PacketEventData) -> None:
            """Update the data structures with collisions event udpate.

            Args:
                packet (PacketEventData): The event packet
            """

            record: PacketEventData.Collision = packet.mEventDetails
            self.m_session_state_ref.processCollisionEvent(record)

        async def processOvertakeEvent(packet: PacketEventData) -> None:
            """Add the overtake event to the tracker

            Args:
                packet (PacketEventData): Incoming event packet
            """
            record: PacketEventData.Overtake = packet.mEventDetails
            self.m_session_state_ref.processOvertakeEvent(record)

    async def clearAllDataStructures(self) -> None:
        """Clear all the data structures"""
        self.m_session_state_ref.processSessionStarted()
        self.m_data_cleared_this_session = True
        self.m_final_classification_processed = False

    async def writeDictToJsonFile(self, data_dict: Dict, file_name: str) -> None:
        """
        Write a dictionary containing JSON data to a file.

        Parameters:
        - data_dict (Dict): Dictionary containing JSON data.
        - file_name (str): File name to write the data to.
        """
        json_str = json.dumps(data_dict, separators=(",", ":"))
        async with aiofiles.open(file_name, 'w', encoding='utf-8') as json_file:
            await json_file.write(json_str)

    async def postGameDumpToFile(self, final_json: Dict[str, Any]) -> None:
        """
        Write the contents of final_json and player recorded events to a file.

        Arguments:
            final_json (Dict): Dictionary containing JSON data after final classification
        """

        event_str = self.m_session_state_ref.getEventInfoStr()
        if not event_str:
            return

        final_json['version'] = self.m_version

        # Save the JSON data
        if self.m_post_race_data_autosave:
            # Add the overtakes as well
            final_json['overtakes'] = {
                'records': [record.toJSON() for record in self.m_session_state_ref.m_overtakes_history.getRecords()]
            }

            # Next, fastest lap and sector records
            final_json['records'] = {
                'fastest' : RaceAnalyzer.getFastestTimesJson(final_json),
                'tyre-stats' : RaceAnalyzer.getTyreStintRecordsDict(final_json)
            }

            # Get timestamp in the format - year_month_day_hour_minute_second
            timestamp_str = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
            final_json_file_name = self.m_directory_mapping['race-info'] + 'race_info_' + \
                    event_str + timestamp_str + '.json'
            await self.writeDictToJsonFile(final_json, final_json_file_name)
            self.m_logger.info("Wrote race info to %s", final_json_file_name)
        else:
            self.m_logger.debug("Not saving post race data")

    def initDirectories(self) -> None:
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
                self.m_logger.info("Directory '%s' created.", directory)

        ts_prefix = datetime.now().strftime("%Y_%m_%d")
        self.m_directory_mapping['race-info'] = f"data/{ts_prefix}/race-info/"

        for directory in self.m_directory_mapping.values():
            ensureDirectoryExists(directory)

    def _shouldSaveData(self) -> bool:
        """
        Check if data should be saved based on the current session type.

        Returns:
            bool: True if data should be saved, False otherwise.
        """

        if not self.m_session_state_ref.m_session_info.is_valid or not self.m_session_state_ref.m_session_info:
            return False
        curr_session_type = self.m_session_state_ref.m_session_info.m_session_type

        if curr_session_type.isFpTypeSession() and self.m_capture_settings.post_fp_data_autosave:
            return True
        if curr_session_type.isQualiTypeSession() and self.m_capture_settings.post_quali_data_autosave:
            return True
        if curr_session_type.isRaceTypeSession() and self.m_capture_settings.post_race_data_autosave:
            return True
        return False # Time trial, movie or story mode
