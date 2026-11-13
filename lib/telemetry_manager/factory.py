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

import struct
from logging import Logger
from typing import Optional, Set

from lib.f1_types import (F1PacketBase, F1PacketType, InvalidPacketLengthError,
                          PacketCountValidationError, PacketHeader,
                          PacketParsingError, UnsupportedValueError)
from lib.socket_receiver import TcpTransport, TelemetryTransport, UdpTransport

from .exceptions import UnsupportedPacketFormat, UnsupportedPacketType

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class PacketParserFactory:
    """Factory to parse raw F1 telemetry packets and retrieve registered callbacks."""

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
        self._last_failure_reason: Optional[str] = None

    def parse(self, raw_packet: bytes) -> F1PacketBase:
        """
        Parse a raw UDP packet into a packet object and its registered callback.

        Returns:
            (packet_obj, callback) — either may be None if not processable.
        """
        if len(raw_packet) < PacketHeader.PACKET_LEN:
            self._last_failure_reason = "Incomplete packet"
            return None # Incomplete packet

        # Parse header
        header = PacketHeader(raw_packet[:PacketHeader.PACKET_LEN])
        if not header.is_supported_packet_type:
            self._last_failure_reason = f"Unsupported packet type. Packet ID = {header.m_packetId}"
            return None

        if header.m_packetFormat < self._MIN_PACKET_FORMAT:
            self._last_failure_reason = f"Unsupported packet format. Packet format = {header.m_packetFormat}"
            raise UnsupportedPacketFormat(header.m_packetFormat)

        if header.m_packetId not in self._interested_packets:
            self._last_failure_reason = f"Uninterested packet type. Packet ID = {header.m_packetId}"
            return None

        # Parse payload
        parser_cls = F1PacketBase.parser_for(header.m_packetId)
        if not parser_cls:
            self._last_failure_reason = f"No parser registered for packet type. Packet ID = {header.m_packetId}"
            raise UnsupportedPacketType(header.m_packetId)

        payload_raw = raw_packet[PacketHeader.PACKET_LEN:]
        try:
            packet = parser_cls(header, payload_raw)
        except (InvalidPacketLengthError, PacketParsingError, PacketCountValidationError,
                UnsupportedValueError, ValueError, TypeError, struct.error) as e:
            self._last_failure_reason = f"Packet parsing error: {str(e)}"
            self._logger.error("Cannot parse packet of type %s. Error = %s",
                                str(header.m_packetId), str(e))
            return None

        self._last_failure_reason = None
        return packet

    @property
    def last_failure_reason(self) -> Optional[str]:
        return self._last_failure_reason

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def telemetry_transport_factory(port_number: int, replay_server: bool, logger: Logger) -> TelemetryTransport:
    """Creates a telemetry transport based on the given port number and replay server mode."""
    if replay_server:
        logger.info("REPLAY RECEIVER MODE. PORT = %s", port_number)
        return TcpTransport(port_number, "localhost")
    logger.info("LIVE RECEIVER MODE. PORT = %s", port_number)
    return UdpTransport(port_number, "0.0.0.0", buffer_size=4096)
