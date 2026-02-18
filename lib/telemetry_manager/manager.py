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

import asyncio
import json
import os
from datetime import datetime
from logging import Logger
from typing import Awaitable, Callable, Dict, Optional

from lib.f1_types import (F1PacketBase, F1PacketType)

from .exceptions import UnsupportedPacketFormat, UnsupportedPacketType
from .factory import PacketParserFactory, telemetry_receiver_factory
from .stats_tracker import PacketStatsTracker

# -------------------------------------- TYPES -------------------------------------------------------------------------

F1TelemetryCallback = Optional[Callable[[F1PacketBase], Awaitable[None]]]

# ------------------------- CLASSES ------------------------------------------------------------------------------------

class AsyncF1TelemetryManager:
    """
    This class is used to act as the interface between the raw parsers and the state management layer.
    This class handles the following tasks
        1 - manage the socket and receive the data
        2 - parse the packet into its appropriate type
        3 - call the appropriate state management layer callback
    """

    def __init__(self, port_number: int, logger: Logger = None, replay_server: bool = False):
        """Init the telemetry manager app and all its sub components

        Args:
            port_number (int): The port number to listen in on
            logger (Logger): The logger to use
            replay_server (bool): If True, the TCP based packet replay server will be created
                NOTE: This is not suited for game. It is meant to be used in conjunction with telemetry_replayer.py
        """

        self.m_replay_server = replay_server
        self.m_stats = PacketStatsTracker()
        self.m_port_number = port_number
        self.m_logger = logger
        self.m_receiver = telemetry_receiver_factory(port_number, replay_server, logger)
        self.m_callbacks: Dict[F1PacketType, F1TelemetryCallback] = {}

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
        """Run the telemetry client asynchronously."""
        if self.m_replay_server:
            self.m_logger.info("REPLAY SERVER MODE. PORT = %s", self.m_port_number)

        pkt_factory = PacketParserFactory(set(self.m_callbacks.keys()), self.m_logger)

        try:
            while True:
                raw_packet = await self.m_receiver.getNextMessage()
                try:
                    await self._processPacket(pkt_factory, raw_packet)
                except (UnsupportedPacketFormat, UnsupportedPacketType) as e:
                    self.m_logger.error(e, exc_info=True)
        except asyncio.CancelledError:
            self.m_logger.debug("Receiver task cancelled - shutting down.")
            await self.m_receiver.close()

    def getStats(self) -> dict:
        """Get the current packet statistics

        Returns:
            dict: The current packet statistics
        """
        return self.m_stats.get_stats()

    async def _processPacket(self,
                             pkt_factory: PacketParserFactory,
                             raw_packet: bytes) -> None:
        """Processes the packet received from the UDP socket

        Args:
            pkt_factory (PacketParserFactory): The packet parser factory
            raw_packet (bytes): The raw packet received from the UDP socket
        """

        self.m_stats.track_raw(raw_packet)
        # First, perform the raw packet callback
        if self.m_raw_packet_callback:
            await self.m_raw_packet_callback(raw_packet)

        parsed_obj = pkt_factory.parse(raw_packet)
        if not parsed_obj:
            return

        self.m_stats.track_parsed(
            parsed_obj.m_header.m_packetId,
            len(raw_packet),
        )

        # Perform the registered callback
        try:
            await self.m_callbacks[parsed_obj.m_header.m_packetId](parsed_obj)
        except Exception as e:
            packet_file = self._dumpPacketToFile(parsed_obj)
            self.m_logger.exception(
                "Exception while handling packet callback.\n"
                "Packet type: %s\nException type: %s\nMessage: %s\n"
                "Header: %s\nPacket dumped to: %s",
                str(parsed_obj.m_header.m_packetId),
                type(e).__name__,
                str(e),
                json.dumps(parsed_obj.m_header.toJSON(), indent=2),
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
