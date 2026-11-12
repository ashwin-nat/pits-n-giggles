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

# ------------------------- IMPORTS ------------------------------------------------------------------------------------

import logging
from types import SimpleNamespace
from typing import List

import pytest

from lib.f1_types import F1PacketType
from lib.telemetry_manager import AsyncF1TelemetryManager, F1TelemetryManagerBase

# ------------------------- HELPERS ------------------------------------------------------------------------------------

def _packet(packet_id: F1PacketType, overall_frame: int, session_uid: int = 1) -> SimpleNamespace:
    """Minimal stand-in carrying the header fields the manager and frame gate read."""
    header = SimpleNamespace(
        m_packetId=packet_id,
        m_overallFrameIdentifier=overall_frame,
        m_sessionUID=session_uid,
    )
    return SimpleNamespace(m_header=header)

def _manager(frame_gate_enabled: bool = False) -> F1TelemetryManagerBase:
    return F1TelemetryManagerBase(logging.getLogger("tests_telemetry_manager"), frame_gate_enabled)

# ------------------------- TESTS --------------------------------------------------------------------------------------

async def test_any_packet_callback_runs_before_the_typed_callback():
    manager = _manager()
    calls: List[str] = []

    @manager.on_any_packet()
    async def _any(_packet):
        calls.append("any")

    @manager.on_packet(F1PacketType.LAP_DATA)
    async def _typed(_packet):
        calls.append("typed")

    await manager._dispatch(_packet(F1PacketType.LAP_DATA, 1))

    assert calls == ["any", "typed"]

async def test_typed_callback_only_gets_its_own_packet_type():
    manager = _manager()
    seen: List[F1PacketType] = []

    @manager.on_packet(F1PacketType.LAP_DATA)
    async def _lap(pkt):
        seen.append(pkt.m_header.m_packetId)

    @manager.on_packet(F1PacketType.EVENT)
    async def _event(pkt):
        seen.append(pkt.m_header.m_packetId)

    await manager._dispatch(_packet(F1PacketType.EVENT, 1))

    assert seen == [F1PacketType.EVENT]

async def test_gated_packet_reaches_neither_callback():
    manager = _manager(frame_gate_enabled=True)
    calls: List[str] = []

    @manager.on_any_packet()
    async def _any(_packet):
        calls.append("any")

    @manager.on_packet(F1PacketType.LAP_DATA)
    async def _typed(_packet):
        calls.append("typed")

    await manager._dispatch(_packet(F1PacketType.LAP_DATA, 10))
    calls.clear()
    await manager._dispatch(_packet(F1PacketType.LAP_DATA, 10))

    assert not calls

async def test_stats_use_the_same_keys_as_before_the_split():
    manager = _manager(frame_gate_enabled=True)

    @manager.on_packet(F1PacketType.LAP_DATA)
    async def _typed(_packet):
        pass

    await manager._dispatch(_packet(F1PacketType.LAP_DATA, 10), 100)
    await manager._dispatch(_packet(F1PacketType.LAP_DATA, 10), 100)

    packets = manager.getStats()["packets"]
    assert set(packets) >= {"__PROCESSED__", "__DROPPED_PACKETS_FRAME_GATE__"}
    assert str(F1PacketType.LAP_DATA) in packets["__PROCESSED__"]
    assert "DUPLICATE_PACKET_TYPE" in packets["__DROPPED_PACKETS_FRAME_GATE__"]

def test_base_stats_have_no_transport_entry():
    assert set(_manager().getStats()) == {"packets"}

def test_async_manager_stats_add_the_transport_entry():
    transport = SimpleNamespace(get_stats=lambda: {"rx": 0})
    manager = AsyncF1TelemetryManager(transport, logging.getLogger("tests_telemetry_manager"))

    assert isinstance(manager, F1TelemetryManagerBase)
    assert set(manager.getStats()) == {"packets", "transport"}

def test_registering_an_invalid_packet_type_raises():
    with pytest.raises(ValueError):
        _manager().on_packet(999)
