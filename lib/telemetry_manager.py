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

# ------------------------- IMPORTS ------------------------------------------------------------------------------------

from logging import Logger
from typing import Awaitable, Callable, Dict, Optional

from lib.f1_types import (F1PacketType, InvalidPacketLengthError,
                          PacketCarDamageData, PacketCarSetupData,
                          PacketCarStatusData, PacketCarTelemetryData,
                          PacketEventData, PacketFinalClassificationData,
                          PacketHeader, PacketLapData, PacketLobbyInfoData,
                          PacketMotionData, PacketMotionExData,
                          PacketParticipantsData, PacketSessionData,
                          PacketSessionHistoryData, PacketTimeTrialData,
                          PacketTyreSetsData)
from lib.socket_receiver import (AsyncTCPListener, AsyncUDPListener,
                                 TCPListener, UDPListener)

# ------------------------- GLOBALS ------------------------------------------------------------------------------------

# ------------------------- CLASSES ------------------------------------------------------------------------------------

class AsyncF1TelemetryManager:
    """
    This class is used to act as the interface between the raw parsers and the user application layer.
    This class handles the following tasks
        1 - manage the socket and receive the data
        2 - identify the packet type and parse the packet accordingly
        3 - identify the callback function that the user has registered and invoke it for the incoming packet type
    """

    packet_type_map = {
        F1PacketType.MOTION: PacketMotionData,
        F1PacketType.SESSION: PacketSessionData,
        F1PacketType.LAP_DATA: PacketLapData,
        F1PacketType.EVENT: PacketEventData,
        F1PacketType.PARTICIPANTS: PacketParticipantsData,
        F1PacketType.CAR_SETUPS: PacketCarSetupData,
        F1PacketType.CAR_TELEMETRY: PacketCarTelemetryData,
        F1PacketType.CAR_STATUS: PacketCarStatusData,
        F1PacketType.FINAL_CLASSIFICATION: PacketFinalClassificationData,
        F1PacketType.LOBBY_INFO: PacketLobbyInfoData,
        F1PacketType.CAR_DAMAGE: PacketCarDamageData,
        F1PacketType.SESSION_HISTORY: PacketSessionHistoryData,
        F1PacketType.TYRE_SETS: PacketTyreSetsData,
        F1PacketType.MOTION_EX: PacketMotionExData,
        F1PacketType.TIME_TRIAL: PacketTimeTrialData,
    }

    def __init__(self, port_number: int, logger: Logger = None, replay_server: bool = False):
        """Init the telemetry manager app and all its sub components

        Args:
            port_number (int): The port number to listen in on
            logger (Logger): The logger to use
            replay_server (bool): If True, the TCP based packet replay server will be created
                NOTE: This is not suited for game. It is meant to be used in conjunction with telemetry_replayer.py
        """

        self.m_replay_server = replay_server
        self.m_port_number = port_number
        self.m_logger = logger
        if self.m_replay_server:
            self.m_server = AsyncTCPListener(port_number, "localhost")
        else:
            self.m_server = AsyncUDPListener(port_number, "0.0.0.0", buffer_size=4096)
        self.m_callbacks: Dict[F1PacketType, Optional[Callable[[object], Awaitable[None]]]] = {
            F1PacketType.MOTION: None,
            F1PacketType.SESSION: None,
            F1PacketType.LAP_DATA: None,
            F1PacketType.EVENT: None,
            F1PacketType.PARTICIPANTS: None,
            F1PacketType.CAR_SETUPS: None,
            F1PacketType.CAR_TELEMETRY: None,
            F1PacketType.CAR_STATUS: None,
            F1PacketType.FINAL_CLASSIFICATION: None,
            F1PacketType.LOBBY_INFO: None,
            F1PacketType.CAR_DAMAGE: None,
            F1PacketType.SESSION_HISTORY: None,
            F1PacketType.TYRE_SETS: None,
            F1PacketType.MOTION_EX: None,
            F1PacketType.TIME_TRIAL: None,
        }
        self.m_raw_packet_callback: Optional[Callable[[object], Awaitable[None]]] = None

    def on_packet(self, packet_type: F1PacketType):
        """Decorator to register a callback for a specific packet type

        Args:
            packet_type (F1PacketType): The packet type to register the callback for

        Returns:
            Callable: The decorator function
        """
        if not F1PacketType.isValid(packet_type):
            raise ValueError(f'Invalid packet type: {packet_type}')

        def decorator(callback: Callable[[object], Awaitable[None]]):
            self.m_callbacks[packet_type] = callback
            return callback

        return decorator

    def on_raw_packet(self):
        """Decorator to register a callback for every raw UDP message

        Returns:
            Callable: The decorator function
        """
        def decorator(callback: Callable[[object], Awaitable[None]]):
            self.m_raw_packet_callback = callback
            return callback

        return decorator

    async def run(self) -> None:
        """Run the telemetry client asynchronously
        """

        if self.m_replay_server:
            self.m_logger.info("REPLAY SERVER MODE. PORT = %s", self.m_port_number)

        should_parse_packet = (sum(callback is not None for callback in self.m_callbacks.values()) > 0)

        # Run the client indefinitely
        while True:

            # Get next UDP message (TCP in the case of replay server)
            raw_packet = await self.m_server.getNextMessage()
            try:
                await self._processPacket(should_parse_packet, raw_packet)
            except Exception as e:
                self.m_logger.error("Error processing packet: %s", e, exc_info=True)
                raise  # Re-raises the caught exception

    async def _processPacket(self, should_parse_packet: bool, raw_packet: bytes) -> None:
        """Processes the packet received from the UDP socket

        Args:
            should_parse_packet (bool): Whether to parse the packet or not
            raw_packet (bytes): The raw packet received from the UDP socket
        """
        if len(raw_packet) < PacketHeader.PACKET_LEN:
            # skip incomplete packet
            return

        if self.m_raw_packet_callback:
            await self.m_raw_packet_callback(raw_packet)

        if not should_parse_packet:
            return

        # Parse the header
        header_raw = raw_packet[:PacketHeader.PACKET_LEN]
        header = PacketHeader(header_raw)
        if not header.is_supported_packet_type:
            # Unsupported packet type, skip
            return

        # Parse the payload and call the registered callback
        payload_raw = raw_packet[PacketHeader.PACKET_LEN:]
        try:
            packet = AsyncF1TelemetryManager.packet_type_map[header.m_packetId](header, payload_raw)
        except InvalidPacketLengthError as e:
            self.m_logger.error("Cannot parse packet of type %s. Error = %s", str(header.m_packetId), str(e))
            return
        if callback := self.m_callbacks.get(header.m_packetId, None):
            await callback(packet)

class F1TelemetryManager:
    """
    This class is used to act as the interface between the raw parsers and the user application layer.
    This class handles the following tasks
        1 - manage the socket and receive the data
        2 - identify the packet type and parse the packet accordingly
        3 - identify the callback function that the user has registered and invoke it for the incoming packet type
    """

    packet_type_map = {
        F1PacketType.MOTION : PacketMotionData,
        F1PacketType.SESSION : PacketSessionData,
        F1PacketType.LAP_DATA : PacketLapData,
        F1PacketType.EVENT : PacketEventData,
        F1PacketType.PARTICIPANTS : PacketParticipantsData,
        F1PacketType.CAR_SETUPS : PacketCarSetupData,
        F1PacketType.CAR_TELEMETRY : PacketCarTelemetryData,
        F1PacketType.CAR_STATUS : PacketCarStatusData,
        F1PacketType.FINAL_CLASSIFICATION : PacketFinalClassificationData,
        F1PacketType.LOBBY_INFO : PacketLobbyInfoData,
        F1PacketType.CAR_DAMAGE : PacketCarDamageData,
        F1PacketType.SESSION_HISTORY : PacketSessionHistoryData,
        F1PacketType.TYRE_SETS : PacketTyreSetsData,
        F1PacketType.MOTION_EX : PacketMotionExData,
        F1PacketType.TIME_TRIAL : PacketTimeTrialData,
    }

    def __init__(self, port_number: int, logger: Logger = None, replay_server: bool = False):
        """Init the telemetry manager app and all its sub components

        Args:
            port_number (int): The port number to listen in on
            logger (Logger): The logger to use
            replay_server (bool): If True, the TCP based packet replay server will be created
                NOTE: This is not suited for game. It is meant to be used in conjunction with telemetry_replayer.py
        """

        self.m_replay_server = replay_server
        self.m_port_number = port_number
        self.m_logger = logger
        if self.m_replay_server:
            self.m_server = TCPListener(port_number, "localhost")
        else:
            self.m_server = UDPListener(port_number, "0.0.0.0", buffer_size=4096)
        self.m_callbacks = {
            F1PacketType.MOTION : None,
            F1PacketType.SESSION : None,
            F1PacketType.LAP_DATA : None,
            F1PacketType.EVENT : None,
            F1PacketType.PARTICIPANTS : None,
            F1PacketType.CAR_SETUPS : None,
            F1PacketType.CAR_TELEMETRY : None,
            F1PacketType.CAR_STATUS : None,
            F1PacketType.FINAL_CLASSIFICATION : None,
            F1PacketType.LOBBY_INFO : None,
            F1PacketType.CAR_DAMAGE : None,
            F1PacketType.SESSION_HISTORY : None,
            F1PacketType.TYRE_SETS : None,
            F1PacketType.MOTION_EX : None,
        }
        self.m_raw_packet_callback = None

    def registerRawPacketCallback(self, callback: Callable):
        """Register a callback for every UDP message on this socket. This is useful for debugging

        Args:
            callback (Callable): The callback function to be executed for every incoming UDP packet.
                It should be a function that takes one argument containing the list of raw bytes

        """

        self.m_raw_packet_callback = callback

    def registerCallbacks(self, packet_callbacks: Dict[F1PacketType, Callable]) -> None:
        """
        Registers multiple callback functions for specific F1 packet types.

        Args:
            packet_callbacks (Dict[F1PacketType, Callable]): A dictionary where the keys are F1 packet types
                and the values are callback functions. Each callback should take one argument of the corresponding
                packet type (e.g., `PacketMotionData` for `F1PacketType.MOTION`).
                                It should be a function that takes one argument of the corresponding packet type.
                e.g. if registering for F1PacketType.MOTION event, the arg passed will be PacketMotionData
                Refer to the the below table for all mappings
                    # Packet Type Mappings:
                    +-------------------------------------+-------------------------------------------+
                    | F1PacketType                        | Corresponding Packet Class                |
                    +-------------------------------------+-------------------------------------------+
                    | F1PacketType.MOTION                 | PacketMotionData                          |
                    | F1PacketType.SESSION                | PacketSessionData                         |
                    | F1PacketType.LAP_DATA               | PacketLapData                             |
                    | F1PacketType.EVENT                  | PacketEventData                           |
                    | F1PacketType.PARTICIPANTS           | PacketParticipantsData                    |
                    | F1PacketType.CAR_SETUPS             | PacketCarSetupData                        |
                    | F1PacketType.CAR_TELEMETRY          | PacketCarTelemetryData                    |
                    | F1PacketType.CAR_STATUS             | PacketCarStatusData                       |
                    | F1PacketType.FINAL_CLASSIFICATION   | PacketFinalClassificationData             |
                    | F1PacketType.LOBBY_INFO             | PacketLobbyInfoData                       |
                    | F1PacketType.CAR_DAMAGE             | PacketCarDamageData                       |
                    | F1PacketType.SESSION_HISTORY        | PacketSessionHistoryData                  |
                    | F1PacketType.TYRE_SETS              | PacketTyreSetsData                        |
                    | F1PacketType.MOTION_EX              | PacketMotionExData                        |
                    | F1PacketType.TIME_TRIAL             | PacketTimeTrialData                       |
                    +-------------------------------------+-------------------------------------------+

        Raises:
            ValueError: If any provided packet type is not a valid F1PacketType.
        """

        # Validate and register each callback in the dictionary
        for packet_type, callback in packet_callbacks.items():
            if not F1PacketType.isValid(packet_type):
                raise ValueError(f'Invalid packet type: {packet_type}')
            self.m_callbacks[packet_type] = callback

    def run(self) -> None:
        """Run the telemetry client
        """

        if self.m_replay_server:
            self.m_logger.info("REPLAY SERVER MODE. PORT = %s", self.m_port_number)

        should_parse_packet = (sum(callback is not None for callback in self.m_callbacks.values()) > 0)

        # Run the client indefinitely
        while True:

            # Get next UDP message (TCP in the case of replay server)
            raw_packet = self.m_server.getNextMessage()
            if len(raw_packet) < PacketHeader.PACKET_LEN:
                # skip incomplete packet
                continue

            if self.m_raw_packet_callback:
                self.m_raw_packet_callback(raw_packet)

            if not should_parse_packet:
                continue

            # Parse the header
            header_raw = raw_packet[:PacketHeader.PACKET_LEN]
            header = PacketHeader(header_raw)
            if not header.is_supported_packet_type:
                # Unsupported packet type, skip
                continue

            # Parse the payload and call the registered callback
            payload_raw = raw_packet[PacketHeader.PACKET_LEN:]
            try:
                packet = F1TelemetryManager.packet_type_map[header.m_packetId](header, payload_raw)
            except InvalidPacketLengthError as e:
                self.m_logger.error("Cannot parse packet of type %s. Error = %s", str(header.m_packetId), str(e))
                continue
            if callback := self.m_callbacks.get(header.m_packetId, None):
                callback(packet)
