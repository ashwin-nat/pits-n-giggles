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
from logging import Logger
from typing import Awaitable, Callable, Dict, Optional

from lib.event_counter import EventCounter
from lib.f1_types import F1PacketBase, F1PacketType

from lib.socket_receiver import TelemetryTransport

from .exceptions import UnsupportedPacketFormat, UnsupportedPacketType
from .factory import PacketParserFactory
from .frame_gate import SessionFrameGate

# -------------------------------------- TYPES -------------------------------------------------------------------------

F1TelemetryCallback = Optional[Callable[[F1PacketBase], Awaitable[None]]]

# ------------------------- CLASSES ------------------------------------------------------------------------------------

class F1TelemetryManagerBase:
    """CPU-bound half of the telemetry manager: callback registry, frame gate and dispatch.

    Owns no transport and no receive loop. Feed it parsed packets through _dispatch().
    """

    def __init__(self,
                 logger: Logger = None,
                 frame_gate_enabled: bool = False):
        """Init the callback registry, frame gate and stats

        Args:
            logger (Logger): The logger to use
            frame_gate_enabled (bool): If True, the frame gate will be enabled
        """

        self.m_stats = EventCounter()
        self.m_logger = logger
        self.m_callbacks: Dict[F1PacketType, F1TelemetryCallback] = {}
        self.m_frame_gate: SessionFrameGate = SessionFrameGate(frame_gate_enabled)
        self.m_any_packet_callback: Optional[F1TelemetryCallback] = None

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

    def on_any_packet(self):
        """Decorator to register a callback that fires for every parsed packet, of any type,
        after frame-gate filtering but before that packet's typed callback.

        Only one callback can be registered at a time, same as on_raw_packet - registering a
        second one silently replaces the first. If more than one consumer ever needs this hook,
        fan them out from within a single registered callback.

        A dropped packet never reaches this hook. Like on_packet, it only sees packet types the
        factory was told to parse in the first place, i.e. types with a registered typed
        callback of their own.

        Returns:
            Callable: The decorator function
        """
        def decorator(callback: Callable[[F1PacketBase], Awaitable[None]]):
            self.m_any_packet_callback = callback
            return callback

        return decorator

    def getStats(self) -> dict:
        """Get the current packet statistics

        Returns:
            dict: The current packet statistics
        """
        return {
            "packets": self.m_stats.get_stats(),
        }

    async def _dispatch(self, parsed_obj: F1PacketBase, size: int = 0) -> None:
        """Run a parsed packet through the frame gate, the any-packet callback and its typed callback

        Args:
            parsed_obj (F1PacketBase): The parsed packet
            size (int): Raw packet size in bytes, used only for stats
        """

        packet_id = parsed_obj.m_header.m_packetId
        callback = self.m_callbacks.get(packet_id)
        if callback is None:
            raise UnsupportedPacketType(packet_id)

        if self.m_frame_gate.should_drop(parsed_obj):
            self.m_stats.track_packet(
                "__DROPPED_PACKETS_FRAME_GATE__",
                self.m_frame_gate.last_drop_reason or "N/A",
                size
            )
            return

        # Runs for every packet that reaches this point, ahead of its typed callback, so a
        # consumer can act on the packet (e.g. detect a session change) before anything
        # merges it into per-type state.
        if self.m_any_packet_callback:
            await self.m_any_packet_callback(parsed_obj)

        # Perform the registered callback
        try:
            await callback(parsed_obj)
            self.m_stats.track_packet(
                "__PROCESSED__",
                str(packet_id),
                size,
            )
        except Exception as e:
            self.m_stats.track_packet(
                "__EXCEPTION_CB__",
                str(packet_id),
                size)
            self.m_logger.exception(
                "Exception while handling packet callback.\n"
                "Packet type: %s\nException type: %s\nMessage: %s\nPacket: %s",
                str(packet_id),
                type(e).__name__,
                str(e),
                json.dumps(parsed_obj.toJSON(include_header=True)),
            )
            raise

class AsyncF1TelemetryManager(F1TelemetryManagerBase):
    """
    This class is used to act as the interface between the raw parsers and the state management layer.
    This class handles the following tasks
        1 - manage the socket and receive the data
        2 - parse the packet into its appropriate type
        3 - call the appropriate state management layer callback
    """

    def __init__(self,
                 transport: TelemetryTransport,
                 logger: Logger = None,
                 frame_gate_enabled: bool = False):
        """Init the telemetry manager app and all its sub components

        Args:
            transport (TelemetryTransport): The transport to receive packets from
            logger (Logger): The logger to use
            frame_gate_enabled (bool): If True, the frame gate will be enabled
        """

        super().__init__(logger, frame_gate_enabled)
        self.m_transport = transport
        self.m_raw_packet_callback: Optional[Callable[[object], Awaitable[None]]] = None

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
        pkt_factory = PacketParserFactory(set(self.m_callbacks.keys()), self.m_logger)

        @self.m_transport.on_packet
        async def _handle(raw_packet: bytes) -> None:
            try:
                await self._processPacket(pkt_factory, raw_packet)
            except (UnsupportedPacketFormat, UnsupportedPacketType) as e:
                self.m_logger.error(e, exc_info=True)

        try:
            await self.m_transport.run()
        except asyncio.CancelledError:
            self.m_logger.debug("Receiver task cancelled - shutting down.")
            await self.m_transport.close()

    def getStats(self) -> dict:
        """Get the current packet statistics

        Returns:
            dict: The current packet statistics
        """
        return {
            **super().getStats(),
            "transport": self.m_transport.get_stats(),
        }

    async def _processPacket(self,
                             pkt_factory: PacketParserFactory,
                             raw_packet: bytes) -> None:
        """Processes the packet received from the UDP socket

        Args:
            pkt_factory (PacketParserFactory): The packet parser factory
            raw_packet (bytes): The raw packet received from the UDP socket
        """

        self.m_stats.track_packet("__RAW__", "__TOTAL__", len(raw_packet))
        # First, perform the raw packet callback
        if self.m_raw_packet_callback:
            await self.m_raw_packet_callback(raw_packet)

        parsed_obj = pkt_factory.parse(raw_packet)
        if not parsed_obj:
            self.m_stats.track_packet(
                "__DROPPED_PACKETS_PARSER_",
                pkt_factory.last_failure_reason or "N/A",
                len(raw_packet))
            return

        await self._dispatch(parsed_obj, len(raw_packet))
