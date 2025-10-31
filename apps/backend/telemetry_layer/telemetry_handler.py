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
import logging
from datetime import datetime
from typing import Any, Awaitable, Callable, Coroutine, Dict, List, Optional

from apps.backend.state_mgmt_layer import SessionState
from lib.button_debouncer import ButtonDebouncer
from lib.config import CaptureSettings, PngSettings
from lib.f1_types import (F1PacketType, PacketCarDamageData,
                          PacketCarSetupData, PacketCarStatusData,
                          PacketCarTelemetryData, PacketEventData,
                          PacketFinalClassificationData, PacketLapData,
                          PacketMotionData, PacketParticipantsData,
                          PacketSessionData, PacketSessionHistoryData,
                          PacketTimeTrialData, PacketTyreSetsData)
from lib.inter_task_communicator import (
    AsyncInterTaskCommunicator, FinalClassificationNotification,
    HudToggleNotification, ITCMessage, TyreDeltaNotificationMessageCollection)
from lib.save_to_disk import save_json_to_file
from lib.telemetry_manager import AsyncF1TelemetryManager
from lib.wdt import WatchDogTimer

# -------------------------------------- TYPE DEFINITIONS --------------------------------------------------------------

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def setupTelemetryTask(
        settings: PngSettings,
        replay_server: bool,
        session_state: SessionState,
        logger: logging.Logger,
        ver_str: str,
        tasks: List[asyncio.Task]) -> "F1TelemetryHandler":
    """Entry point to start the F1 telemetry server.

    Args:
        settings (PngSettings): App settings
        replay_server (bool): Whether to enable the TCP replay debug server.
        session_state (SessionState): Handle to the session state
        logger (logging.Logger): Logger instance
        ver_str (str): Version string
        tasks (List[asyncio.Task]): List of tasks to be executed

    Returns:
        F1TelemetryHandler: Telemetry handler server
    """

    telemetry_server = F1TelemetryHandler(
        settings=settings,
        logger=logger,
        session_state=session_state,
        replay_server=replay_server,
        ver_str=ver_str,
    )
    tasks.append(telemetry_server.getTask())
    tasks.append(asyncio.create_task(telemetry_server.getWatchdogTask(), name="Watchdog Timer Task"))

    return telemetry_server

# -------------------------------------- TELEMETRY PACKET HANDLERS -----------------------------------------------------

class F1TelemetryHandler:
    """
    Handles incoming F1 telemetry data. Handles the various types of incoming packets

    Attributes:
    - m_manager (F1TelemetryManager): The telemetry manager instance.
    """

    def __init__(self,
        settings: PngSettings,
        logger: logging.Logger,
        session_state: SessionState,
        replay_server: bool = False,
        ver_str: str = "dev") -> None:
        """
        Initialize F1TelemetryHandler.

        Parameters:
            - settings (PngSettings): Png settings
            - port (int): The port number for telemetry.
            - forwarding_targets (List[Tuple[str, int]]): List of IP addr port pairs to forward packets to
            - logger (logging.Logger): Logger
            - capture_settings (CaptureSettings): Capture settings
            - wdt_interval (float): Watchdog interval
            - udp_custom_action_code (Optional[int]): UDP custom action code.
            - udp_tyre_delta_action_code (Optional[int]): UDP tyre delta action code
            - replay_server: bool: If true, init in replay mode (TCP). Else init in live mode (UDP)
            - ver_str (str): Version string
        """
        self.m_manager = AsyncF1TelemetryManager(
            port_number=settings.Network.telemetry_port,
            logger=logger,
            replay_server=replay_server
        )
        self.m_logger: logging.Logger = logger
        self.m_session_state_ref: SessionState = session_state

        self.m_last_session_uid: Optional[int] = None
        self.m_data_cleared_this_session: bool = False
        self.m_udp_custom_action_code: Optional[int] = settings.Network.udp_custom_action_code
        self.m_udp_tyre_delta_action_code: Optional[int] = settings.Network.udp_tyre_delta_action_code
        self.m_hud_toggle_udp_action_code: Optional[int] = settings.HUD.toggle_overlays_udp_action_code
        self.m_final_classification_processed: bool = False
        self.m_capture_settings: CaptureSettings = settings.Capture
        self.m_button_debouncer: ButtonDebouncer = ButtonDebouncer()

        self.m_should_forward: bool = bool(settings.Forwarding.forwarding_targets)
        self.m_version: str = ver_str
        self.m_wdt: WatchDogTimer = WatchDogTimer(
            status_callback=self.m_session_state_ref.setConnectedToSim,
            timeout=float(settings.Network.wdt_interval_sec),
        )
        self.m_manager_task: Optional[asyncio.Task] = None
        self.registerCallbacks()

    def getTask(self, name: Optional[str] = "Game Telemetry Listener Task") -> asyncio.Task:
        """
        Get the telemetry manager task.

        Args:
            name (Optional[str], optional): Name of the task. Defaults to "Game Telemetry Listener Task".

        Returns:
        asyncio.Task: The telemetry manager task.
        """
        self.m_manager_task = asyncio.create_task(self.run(), name=name)
        return self.m_manager_task

    async def run(self):
        """
        Run the telemetry handler.

        Returns:
        None
        """
        await self.m_manager.run()

    async def stop(self) -> None:
        """
        Stop the telemetry manager and watchdog timer.
        """
        if self.m_manager_task:
            self.m_manager_task.cancel()
        self.m_wdt.stop()
        self.m_logger.debug("Telemetry handler stopped. manager and wdt stopped.")

    def getWatchdogTask(self) -> Coroutine:
        """
        Get the watchdog task.

        Returns:
        Coroutine: The watchdog task.
        """
        return self.m_wdt.run()

    def registerCallbacks(self) -> None:
        """
        Register callback functions for different types of telemetry packets.
        """

        @self.m_manager.on_raw_packet()
        async def handleRawPacket(packet: List[bytes]) -> None:
            """
            Handle raw telemetry packet.
            Parameters:
                packet (List[bytes]): The raw telemetry packet.
            """
            self.m_wdt.kick()
            self.m_session_state_ref.m_pkt_count += 1
            if self.m_should_forward:
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
                self.clearAllDataStructures("Session duration is 0")

            elif await self.m_session_state_ref.processSessionUpdate(packet):
                self.m_logger.info("Session UID changed. clearing data structures")
                self.clearAllDataStructures("Session UID changed")

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

            self.m_session_state_ref.handleEvent(packet)

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
            if not self.m_session_state_ref.m_session_info.is_valid:
                self.m_logger.error('Final classification event. Session data not available. Not saving data.')
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

            if session_type and (session_type.isRaceTypeSession() or session_type.isQualiTypeSession()) and player_info:
                player_position = player_info.m_driver_info.position
                message = ITCMessage(
                    m_message_type=ITCMessage.MessageType.FINAL_CLASSIFICATION_NOTIFICATION,
                    m_message=FinalClassificationNotification(player_position)
                )
                await AsyncInterTaskCommunicator().send("frontend-update", message)

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

        # Register the car setup handler if and only if user has allowed this
        if self.m_session_state_ref.m_process_car_setups:
            self.m_logger.debug("Processing car setups")
            @self.m_manager.on_packet(F1PacketType.CAR_SETUPS)
            async def processCarSetupsUpdate(packet: PacketCarSetupData) -> None:
                """Update the data structures with car setup information

                Args:
                    packet (PacketCarSetupData): The car setup update packet
                """

                self.m_session_state_ref.processCarSetupsUpdate(packet)
        else:
            self.m_logger.debug("Not processing car setups")

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
            self.clearAllDataStructures(f"SESSION_START event - UID {packet.m_header.m_sessionUID}")

        async def handleButtonStatus(packet: PacketEventData) -> None:
            """
            Handle and process the button press event

            Args:
                packet (PacketEventData): The parsed object containing the button status packet's contents.
            """

            buttons: PacketEventData.Buttons = packet.mEventDetails
            if self._isUdpActionButtonPressed(buttons, self.m_udp_custom_action_code):
                self.m_logger.debug('UDP action %d pressed - Custom Marker', self.m_udp_custom_action_code)
                await self._processCustomMarkerCreate()

            if self._isUdpActionButtonPressed(buttons, self.m_udp_tyre_delta_action_code):
                self.m_logger.debug('UDP action %d pressed - Tyre Delta', self.m_udp_tyre_delta_action_code)
                await self._processTyreDeltaSound()

            if self._isUdpActionButtonPressed(buttons, self.m_hud_toggle_udp_action_code):
                self.m_logger.debug('UDP action %d pressed - HUD toggle', self.m_hud_toggle_udp_action_code)
                await self._processToggleHud()

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
                    self.clearAllDataStructures("Start lights event")
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

    def clearAllDataStructures(self, reason: str) -> None:
        """Clear all the data structures

        Args:
            reason (str): Reason for clearing
        """
        self.m_session_state_ref.processSessionStarted(reason)
        self.m_data_cleared_this_session = True
        self.m_final_classification_processed = False

    async def postGameDumpToFile(self, final_json: Dict[str, Any]) -> None:
        """
        Write the contents of final_json and player recorded events to a file.

        Arguments:
            final_json (Dict): Dictionary containing JSON data after final classification
        """

        event_str = self.m_session_state_ref.getEventInfoStr()
        if not event_str:
            return

        now = datetime.now().astimezone()
        # Save the JSON data
        # Get timestamp in the format - year_month_day_hour_minute_second
        timestamp_str = now.strftime("%Y_%m_%d_%H_%M_%S")
        final_json_file_name = event_str + timestamp_str + '.json'

        # Insert extra debug info
        final_json["debug"] = final_json.get("debug", {})
        final_json["debug"].update({
            "session-uid" : self.m_session_state_ref.m_session_info.m_session_uid,
            "timestamp" : now.strftime("%Y-%m-%d %H:%M:%S %Z"),
            "timezone" : now.tzinfo.key if hasattr(now.tzinfo, "key") else str(now.tzinfo),
            "utc-offset-seconds" : int(now.utcoffset().total_seconds()),
            "reason": "Auto-save after final classification",
            "packet-count": self.m_session_state_ref.m_pkt_count,
            "file-name": final_json_file_name,
        })
        try:
            await save_json_to_file(final_json, final_json_file_name)
            self.m_logger.info("Wrote race info to %s. Num pkts %d", final_json_file_name,
                               self.m_session_state_ref.m_pkt_count)
        except Exception: # pylint: disable=broad-except
            # No need to crash the app just because write failed
            self.m_logger.exception("Failed to write race info to %s", final_json_file_name)

    def _shouldSaveData(self) -> bool:
        """
        Check if data should be saved based on the current session type.

        Returns:
            bool: True if data should be saved, False otherwise.
        """

        curr_session_type = self.m_session_state_ref.m_session_info.m_session_type
        if not curr_session_type:
            self.m_logger.error("Session type in None. Not saving data.")
            return False

        if curr_session_type.isFpTypeSession() and self.m_capture_settings.post_fp_data_autosave:
            return True
        if curr_session_type.isQualiTypeSession() and self.m_capture_settings.post_quali_data_autosave:
            return True
        if curr_session_type.isRaceTypeSession() and self.m_capture_settings.post_race_data_autosave:
            return True
        if curr_session_type.isTimeTrialTypeSession() and self.m_capture_settings.post_tt_data_autosave:
            return True
        return False # movie or story mode

    def _isUdpActionButtonPressed(self,
                                       buttons_event: PacketEventData.Buttons,
                                       action_code: Optional[int]
                                       ) -> bool:
        """Check if the UDP action button is pressed.

        Args:
            buttons_event (PacketEventData.Buttons): The buttons event packet.
            action_code (Optional[int]): The UDP action code to check.
        """
        return (
            action_code is not None
            and buttons_event.isUDPActionPressed(action_code)
            and self.m_button_debouncer.onButtonPress(action_code)
        )

    async def _processCustomMarkerCreate(self) -> None:
        """Update the data structures with custom marker information
        """

        if custom_marker_obj := self.m_session_state_ref.getInsertCustomMarkerEntryObj():
            await AsyncInterTaskCommunicator().send("frontend-update", ITCMessage(
                m_message_type=ITCMessage.MessageType.CUSTOM_MARKER,
                m_message=custom_marker_obj))

    async def _processTyreDeltaSound(self) -> None:
        """Send the tyre delta notification to the frontend."""
        if messages := self.m_session_state_ref.getTyreDeltaNotificationMessages():
            await AsyncInterTaskCommunicator().send(
                "frontend-update",
                ITCMessage(
                    m_message_type=ITCMessage.MessageType.TYRE_DELTA_NOTIFICATION_V2,
                    m_message=TyreDeltaNotificationMessageCollection(messages)
                )
            )

    async def _processToggleHud(self) -> None:
        """Send the toggle HUD notification to the HUD manager."""
        await AsyncInterTaskCommunicator().send(
            "hud-notifier",
            ITCMessage(
                m_message_type=ITCMessage.MessageType.HUD_TOGGLE_NOTIFICATION,
                m_message=HudToggleNotification()
            )
        )
