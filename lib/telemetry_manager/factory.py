# MIT License
#
# Copyright (c) [2025] [Ashwin Natarajan]
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

# -------------------------------------- IMPORTS -----------------------------------------------------------------------


from logging import Logger
from typing import Set, Type

from lib.f1_types import (F1PacketBase, F1PacketType, InvalidPacketLengthError,
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
from lib.socket_receiver import TcpReceiver, TelemetryReceiver, UdpReceiver

from .exceptions import UnsupportedPacketFormat, UnsupportedPacketType

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class PacketParserFactory:
    """Factory to parse raw F1 telemetry packets and retrieve registered callbacks."""

    _PACKET_TYPE_MAP: dict[F1PacketType, Type] = {
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
    _MIN_PACKET_FORMAT = 2023

    def __init__(
        self,
        interested_packets: Set[F1PacketType],
        logger: Logger):
        """Initialize the packet parser factory.

        Args:
            interested_packets (Set[F1PacketType]): The set of packet types to be interested in
            logger (Logger): The logger to use
        """
        self._interested_packets = interested_packets
        self._logger = logger

    def parse(self, raw_packet: bytes) -> F1PacketBase:
        """
        Parse a raw UDP packet into a packet object and its registered callback.

        Returns:
            (packet_obj, callback) — either may be None if not processable.
        """
        if len(raw_packet) < PacketHeader.PACKET_LEN:
            return None # Incomplete packet

        # Parse header
        header = PacketHeader(raw_packet[:PacketHeader.PACKET_LEN])

        if not header.is_supported_packet_type:
            return None

        if header.m_packetFormat < self._MIN_PACKET_FORMAT:
            raise UnsupportedPacketFormat(header.m_packetFormat)

        if header.m_packetId not in self._interested_packets:
            return None

        # Parse payload
        parser_cls = self._PACKET_TYPE_MAP.get(header.m_packetId)
        if not parser_cls:
            raise UnsupportedPacketType(header.m_packetId)

        payload_raw = raw_packet[PacketHeader.PACKET_LEN:]
        try:
            packet = parser_cls(header, payload_raw)
        except (InvalidPacketLengthError, PacketParsingError, PacketCountValidationError) as e:
            self._logger.error("Cannot parse packet of type %s. Error = %s",
                                str(header.m_packetId), str(e))
            return None

        return packet

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def telemetry_receiver_factory(port_number: int, replay_server: bool, logger: Logger) -> TelemetryReceiver:
    """Creates a telemetry receiver based on the given port number and replay server mode."""
    if replay_server:
        logger.info("REPLAY RECEIVER MODE. PORT = %s", port_number)
        return TcpReceiver(port_number, "localhost")
    logger.info("LIVE RECEIVER MODE. PORT = %s", port_number)
    return UdpReceiver(port_number, "0.0.0.0", buffer_size=4096)
