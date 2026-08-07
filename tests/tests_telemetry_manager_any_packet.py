# MIT License
#
# Copyright (c) [2026] [Ashwin Natarajan]
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

"""Tests for AsyncF1TelemetryManager.on_any_packet - see session-uid-clearing-plan.md, Commit 1."""

from typing import List, Optional

from lib.f1_types import F1PacketBase, F1PacketType, PacketHeader
from lib.socket_receiver import TelemetryTransport
from lib.telemetry_manager.manager import AsyncF1TelemetryManager

# ----------------------------------------------------------------------------------------------------------------------

class DummyPacket(F1PacketBase):
    """Minimal concrete packet for testing the manager's dispatch logic."""
    __slots__ = ()

    def __init__(self, session_uid: int, frame_id: int, packet_type: F1PacketType):
        header = PacketHeader.from_values(
            packet_format=2025,
            game_year=25,
            game_major_version=1,
            game_minor_version=0,
            packet_version=1,
            packet_type=packet_type,
            session_uid=session_uid,
            session_time=0.0,
            frame_identifier=frame_id,
            overall_frame_identifier=frame_id,
            player_car_index=0,
            secondary_player_car_index=255,
        )
        super().__init__(header)


class FakeTransport(TelemetryTransport):
    """Manager construction requires a transport; this test never calls run()."""

    def on_packet(self, callback):
        pass

    async def run(self) -> None:
        pass

    async def close(self) -> None:
        pass

    def get_stats(self) -> dict:
        return {}


class FakeFactory:
    """Stands in for PacketParserFactory: returns preset packets instead of parsing bytes,
    so tests can drive _processPacket without real wire-format payloads."""

    def __init__(self, packets: List[Optional[F1PacketBase]]):
        self._packets = list(packets)
        self.last_failure_reason: Optional[str] = None

    def parse(self, _raw_packet: bytes) -> Optional[F1PacketBase]:
        return self._packets.pop(0)


def _make_manager(frame_gate_enabled: bool = False) -> AsyncF1TelemetryManager:
    return AsyncF1TelemetryManager(FakeTransport(), logger=None, frame_gate_enabled=frame_gate_enabled)

# ----------------------------------------------------------------------------------------------------------------------

async def test_any_packet_hook_fires_for_every_registered_packet_type():
    manager = _make_manager()
    seen: List[F1PacketType] = []

    @manager.on_any_packet()
    async def _on_any(packet: F1PacketBase) -> None:
        seen.append(packet.m_header.m_packetId)

    @manager.on_packet(F1PacketType.SESSION)
    async def _on_session(_packet: F1PacketBase) -> None:
        pass

    @manager.on_packet(F1PacketType.LAP_DATA)
    async def _on_lap_data(_packet: F1PacketBase) -> None:
        pass

    session_pkt = DummyPacket(session_uid=1, frame_id=1, packet_type=F1PacketType.SESSION)
    lap_data_pkt = DummyPacket(session_uid=1, frame_id=2, packet_type=F1PacketType.LAP_DATA)
    factory = FakeFactory([session_pkt, lap_data_pkt])

    await manager._processPacket(factory, b"unused")
    await manager._processPacket(factory, b"unused")

    assert seen == [F1PacketType.SESSION, F1PacketType.LAP_DATA]


async def test_any_packet_hook_does_not_see_dropped_packets():
    # Frame gate enabled: a duplicate packet type within the same frame is dropped.
    manager = _make_manager(frame_gate_enabled=True)
    seen: List[F1PacketType] = []

    @manager.on_any_packet()
    async def _on_any(packet: F1PacketBase) -> None:
        seen.append(packet.m_header.m_packetId)

    @manager.on_packet(F1PacketType.SESSION)
    async def _on_session(_packet: F1PacketBase) -> None:
        pass

    first = DummyPacket(session_uid=1, frame_id=5, packet_type=F1PacketType.SESSION)
    duplicate = DummyPacket(session_uid=1, frame_id=5, packet_type=F1PacketType.SESSION)
    factory = FakeFactory([first, duplicate])

    await manager._processPacket(factory, b"unused")
    await manager._processPacket(factory, b"unused")

    assert seen == [F1PacketType.SESSION]


async def test_any_packet_hook_fires_before_typed_callback():
    manager = _make_manager()
    order: List[str] = []

    @manager.on_any_packet()
    async def _on_any(_packet: F1PacketBase) -> None:
        order.append("any")

    @manager.on_packet(F1PacketType.SESSION)
    async def _on_session(_packet: F1PacketBase) -> None:
        order.append("typed")

    packet = DummyPacket(session_uid=1, frame_id=1, packet_type=F1PacketType.SESSION)
    factory = FakeFactory([packet])

    await manager._processPacket(factory, b"unused")

    assert order == ["any", "typed"]


async def test_no_any_packet_hook_is_a_noop():
    manager = _make_manager()
    typed_calls: List[F1PacketType] = []

    @manager.on_packet(F1PacketType.SESSION)
    async def _on_session(packet: F1PacketBase) -> None:
        typed_calls.append(packet.m_header.m_packetId)

    packet = DummyPacket(session_uid=1, frame_id=1, packet_type=F1PacketType.SESSION)
    factory = FakeFactory([packet])

    await manager._processPacket(factory, b"unused")

    assert typed_calls == [F1PacketType.SESSION]
