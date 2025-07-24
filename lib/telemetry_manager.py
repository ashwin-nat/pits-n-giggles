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

import json
import os
from datetime import datetime
from logging import Logger
from typing import Awaitable, Callable, Dict, Optional

from lib.f1_types import (F1PacketType, InvalidPacketLengthError,
                          PacketCarDamageData, PacketCarSetupData,
                          PacketCarStatusData, PacketCarTelemetryData,
                          PacketCountValidationError, PacketEventData,
                          PacketFinalClassificationData, PacketHeader,
                          PacketLapData, PacketLapPositionsData,
                          PacketLobbyInfoData, PacketMotionData,
                          PacketMotionExData, PacketParsingError,
                          PacketParticipantsData, PacketSessionData,
                          PacketSessionHistoryData, PacketTimeTrialData,
                          PacketTyreSetsData)
from lib.socket_receiver import TcpReceiver, UdpReceiver, TelemetryReceiver

# ------------------------- GLOBALS ------------------------------------------------------------------------------------
F1TelemetryCallback = Optional[Callable[[object], Awaitable[None]]]

# ------------------------- CLASSES ------------------------------------------------------------------------------------

class UnsupportedPacketFormat(Exception):
    """Raised when packet data is malformed or insufficient"""
    def __init__(self, packet_format):
        super().__init__(f"Unsupported packet format. {packet_format}")

class AsyncF1TelemetryManager:
    """
    This class is used to act as the interface between the raw parsers and the user application layer.
    This class handles the following tasks
        1 - manage the socket and receive the data
        2 - identify the packet type and parse the packet accordingly
        3 - identify the callback function that the user has registered and invoke it for the incoming packet type

    Following is the mapping between Packet ID and the packet type
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
        | F1PacketType.LAP_POSITIONS          | PacketLapPositionsData                    |
        +-------------------------------------+-------------------------------------------+
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
        F1PacketType.LAP_POSITIONS: PacketLapPositionsData,
    }

    MIN_PACKET_FORMAT = 2023

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
        self.m_receiver = telemetry_receiver_factory(port_number, replay_server, logger)
        self.m_callbacks: Dict[F1PacketType, F1TelemetryCallback] = {ptype: None for ptype in self.packet_type_map}

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

            # Get next telemetry message
            raw_packet = await self.m_receiver.getNextMessage()
            try:
                await self._processPacket(should_parse_packet, raw_packet)
            except UnsupportedPacketFormat as e:
                self.m_logger.error(e, exc_info=True)
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

        if header.m_packetFormat < self.MIN_PACKET_FORMAT:
            raise UnsupportedPacketFormat(header.m_packetFormat)

        # Parse the payload and call the registered callback
        payload_raw = raw_packet[PacketHeader.PACKET_LEN:]
        try:
            packet = AsyncF1TelemetryManager.packet_type_map[header.m_packetId](header, payload_raw)
        except (InvalidPacketLengthError, PacketParsingError, PacketCountValidationError) as e:
            self.m_logger.error("Cannot parse packet of type %s. Error = %s", str(header.m_packetId), str(e))
            return
        if callback := self.m_callbacks.get(header.m_packetId, None):
            try:
                await callback(packet)
            except Exception as e:
                packet_file = self._dumpPacketToFile(packet)
                self.m_logger.exception(
                    "Exception while handling packet callback.\n"
                    "Packet type: %s\nException type: %s\nMessage: %s\n"
                    "Header: %s\nPacket dumped to: %s",
                    str(header.m_packetId),
                    type(e).__name__,
                    str(e),
                    json.dumps(header.toJSON(), indent=2),
                    packet_file,
                )
                raise

    def _dumpPacketToFile(self, packet_obj: object, directory: str = "crash_packet_dumps") -> str:
        """Dump packet JSON to a timestamped file and return the file path.

        Args:
            packet_obj (object): The packet object to dump.
            directory (str, optional): The directory to dump the packet to. Defaults to "crash_packet_dumps".

        Returns:
            str: The file path of the dumped packet.

        """
        os.makedirs(directory, exist_ok=True)

        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f")
        filename = f"{timestamp}.json"
        filepath = os.path.join(directory, filename)

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(packet_obj.toJSON(), f, ensure_ascii=False, indent=2)
            return filepath
        except Exception as e: # pylint: disable=broad-except
            return f"<Failed to write packet to file: {e}>"

# ------------------------- FUNCTIONS ----------------------------------------------------------------------------------

def telemetry_receiver_factory(port_number: int, replay_server: bool, logger: Logger) -> TelemetryReceiver:
    """Creates a telemetry receiver based on the given port number and replay server mode."""
    if replay_server:
        logger.info("REPLAY RECEIVER MODE. PORT = %s", port_number)
        return TcpReceiver(port_number, "localhost")
    else:
        logger.info("LIVE RECEIVER MODE. PORT = %s", port_number)
        return UdpReceiver(port_number, "0.0.0.0", buffer_size=4096)
