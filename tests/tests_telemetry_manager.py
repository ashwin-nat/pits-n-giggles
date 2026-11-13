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

import asyncio
import json
import logging
import os
from types import SimpleNamespace
from typing import List

import allure
import pytest

from lib.f1_types import F1PacketBase, F1PacketType, PacketEventData, PacketHeader
from lib.telemetry_manager import AsyncF1TelemetryManager, F1TelemetryManagerBase
from lib.telemetry_manager import factory as factory_module
from lib.telemetry_manager.exceptions import UnsupportedPacketType
from lib.telemetry_manager.factory import PacketParserFactory, telemetry_transport_factory

pytestmark = allure.epic("Telemetry manager")

# ------------------------- HELPERS ------------------------------------------------------------------------------------

def _packet(packet_id: F1PacketType, overall_frame: int, session_uid: int = 1) -> SimpleNamespace:
    """Minimal stand-in carrying the header fields the manager and frame gate read."""
    header = SimpleNamespace(
        m_packetId=packet_id,
        m_overallFrameIdentifier=overall_frame,
        m_sessionUID=session_uid,
    )
    return SimpleNamespace(
        m_header=header,
        toJSON=lambda include_header=False: {"header": {"frame": overall_frame}, "body": 1},
    )

def _manager(frame_gate_enabled: bool = False) -> F1TelemetryManagerBase:
    return F1TelemetryManagerBase(logging.getLogger("tests_telemetry_manager"), frame_gate_enabled)

def _raw(packet_id: int, packet_format: int = 2025, payload: bytes = b"") -> bytes:
    """A raw packet: a header with packet_id (any int, so undeclared IDs too), then payload."""
    header = PacketHeader.COMPILED_PACKET_STRUCT.pack(packet_format, packet_format % 100, 1, 0, 1, packet_id,
                                                      1, 0.0, 1, 1, 0, 255)
    return header + payload

def _raw_event(packet_format: int = 2025) -> bytes:
    """A SESSION_STARTED event, which has no details."""
    return _raw(F1PacketType.EVENT.value, packet_format, b"SSTA" + bytes(32))

class _FakeTransport:
    """Hands each raw packet to the manager's handler in turn, then returns, or raises CancelledError."""

    def __init__(self, raw_packets: List[bytes], cancel: bool = False) -> None:
        self._raw_packets = raw_packets
        self._cancel = cancel
        self._handler = None
        self.closed = False

    def on_packet(self, handler):
        self._handler = handler
        return handler

    async def run(self) -> None:
        for raw in self._raw_packets:
            await self._handler(raw)
        if self._cancel:
            raise asyncio.CancelledError

    async def close(self) -> None:
        self.closed = True

    def get_stats(self) -> dict:
        return {}

def _async_manager(transport: _FakeTransport) -> AsyncF1TelemetryManager:
    return AsyncF1TelemetryManager(transport, logging.getLogger("tests_telemetry_manager"))

# ------------------------- TESTS --------------------------------------------------------------------------------------

@allure.feature("Dispatch")
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

@allure.feature("Dispatch")
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

@allure.feature("Dispatch")
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

@allure.feature("Stats")
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

@allure.feature("Stats")
def test_base_stats_have_no_transport_entry():
    assert set(_manager().getStats()) == {"packets"}

@allure.feature("Stats")
def test_async_manager_stats_add_the_transport_entry():
    transport = SimpleNamespace(get_stats=lambda: {"rx": 0})
    manager = AsyncF1TelemetryManager(transport, logging.getLogger("tests_telemetry_manager"))

    assert isinstance(manager, F1TelemetryManagerBase)
    assert set(manager.getStats()) == {"packets", "transport"}

@allure.feature("Dispatch")
def test_registering_an_invalid_packet_type_raises():
    with pytest.raises(ValueError):
        _manager().on_packet(999)

@allure.feature("Dispatch")
async def test_unregistered_packet_type_raises_and_leaves_the_gate_alone():
    manager = _manager(frame_gate_enabled=True)

    @manager.on_packet(F1PacketType.LAP_DATA)
    async def _typed(_packet):
        pass

    with pytest.raises(UnsupportedPacketType):
        await manager._dispatch(_packet(F1PacketType.EVENT, 10))

    # The gate never saw the EVENT packet, so the same frame still accepts it once registered
    @manager.on_packet(F1PacketType.EVENT)
    async def _event(_packet):
        pass

    await manager._dispatch(_packet(F1PacketType.EVENT, 10))
    assert str(F1PacketType.EVENT) in manager.getStats()["packets"]["__PROCESSED__"]

@allure.feature("Dispatch")
async def test_raising_callback_logs_single_line_json_and_writes_no_file(caplog, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    manager = _manager()

    @manager.on_packet(F1PacketType.LAP_DATA)
    async def _typed(_packet):
        raise RuntimeError("boom")

    with caplog.at_level(logging.ERROR, logger="tests_telemetry_manager"):
        with pytest.raises(RuntimeError):
            await manager._dispatch(_packet(F1PacketType.LAP_DATA, 1))

    packet_line = next(l for l in caplog.messages[0].splitlines() if l.startswith("Packet: "))
    assert json.loads(packet_line.removeprefix("Packet: ")) == {"header": {"frame": 1}, "body": 1}
    assert "__EXCEPTION_CB__" in manager.getStats()["packets"]
    assert not os.listdir(tmp_path)

@allure.feature("Dispatch")
async def test_unserialisable_packet_still_logs_and_reraises_the_callback_error(caplog):
    manager = _manager()
    packet = _packet(F1PacketType.LAP_DATA, 1)
    packet.toJSON = lambda include_header=False: {"sector": object()}    # json.dumps raises TypeError

    @manager.on_packet(F1PacketType.LAP_DATA)
    async def _typed(_packet):
        raise RuntimeError("boom")

    with caplog.at_level(logging.ERROR, logger="tests_telemetry_manager"):
        with pytest.raises(RuntimeError, match="boom"):
            await manager._dispatch(packet)

    assert "Message: boom" in caplog.messages[0]
    assert "Packet: <toJSON failed: TypeError: " in caplog.messages[0]

# ------------------------- RECEIVE PATH -------------------------------------------------------------------------------

@allure.feature("Receive path")
async def test_raw_callback_sees_every_packet_before_it_is_parsed():
    manager = _async_manager(_FakeTransport([_raw_event(), b"short"]))
    calls: List[str] = []

    @manager.on_raw_packet()
    async def _raw_cb(raw):
        calls.append(f"raw {len(raw)}")

    @manager.on_packet(F1PacketType.EVENT)
    async def _event(packet):
        calls.append(f"typed {packet.m_eventCode}")

    await manager.run()

    assert calls == [f"raw {len(_raw_event())}", f"typed {PacketEventData.EventPacketType.SESSION_STARTED}", "raw 5"]
    assert manager.getStats()["packets"]["__RAW__"]["__TOTAL__"]["count"] == 2

@allure.feature("Receive path")
async def test_packets_the_parser_drops_are_counted_by_reason():
    manager = _async_manager(_FakeTransport([
        b"short",                                       # shorter than a header
        _raw(99),                                       # an ID F1PacketType doesn't declare
        _raw(F1PacketType.LAP_DATA.value),              # nothing registered for LAP_DATA
    ]))

    @manager.on_packet(F1PacketType.EVENT)
    async def _event(_packet):
        raise AssertionError("no EVENT packet was sent")

    await manager.run()

    dropped = manager.getStats()["packets"]["__DROPPED_PACKETS_PARSER_"]
    assert sorted(dropped) == ["Incomplete packet", "Uninterested packet type. Packet ID = LAP_DATA",
                               "Unsupported packet type. Packet ID = 99"]

@allure.feature("Receive path")
async def test_an_old_packet_format_is_logged_and_the_next_packet_still_arrives(caplog):
    manager = _async_manager(_FakeTransport([_raw_event(packet_format=2022), _raw_event()]))
    formats: List[int] = []

    @manager.on_packet(F1PacketType.EVENT)
    async def _event(packet):
        formats.append(packet.m_header.m_packetFormat)

    with caplog.at_level(logging.ERROR, logger="tests_telemetry_manager"):
        await manager.run()

    assert formats == [2025]
    assert "Unsupported packet format. 2022" in caplog.messages

@allure.feature("Receive path")
async def test_cancelling_run_closes_the_transport():
    transport = _FakeTransport([], cancel=True)

    await _async_manager(transport).run()

    assert transport.closed

@allure.feature("Parser factory")
def test_parse_returns_the_packet_and_clears_the_last_failure():
    factory = PacketParserFactory({F1PacketType.EVENT}, logging.getLogger("tests_telemetry_manager"))
    assert factory.parse(b"short") is None
    assert factory.last_failure_reason == "Incomplete packet"

    packet = factory.parse(_raw_event())

    assert isinstance(packet, PacketEventData)
    assert factory.last_failure_reason is None

@allure.feature("Parser factory")
def test_parse_raises_for_a_registered_type_no_class_parses(monkeypatch):
    # Unreachable while every F1PacketType has a parser (tests_base checks that), so the lookup is faked
    monkeypatch.setattr(F1PacketBase, "parser_for", staticmethod(lambda _packet_id: None))
    factory = PacketParserFactory({F1PacketType.EVENT}, logging.getLogger("tests_telemetry_manager"))

    with pytest.raises(UnsupportedPacketType):
        factory.parse(_raw_event())

@allure.feature("Transport factory")
@pytest.mark.parametrize("replay_server, expected", [(True, ("tcp", 20777, "localhost")),
                                                     (False, ("udp", 20777, "0.0.0.0"))],
                         ids=["replay", "live"])
def test_transport_factory_picks_tcp_for_replay_and_udp_for_live(monkeypatch, replay_server, expected):
    # The real transports bind their socket on construction
    monkeypatch.setattr(factory_module, "TcpTransport", lambda port, ip, **_kw: ("tcp", port, ip))
    monkeypatch.setattr(factory_module, "UdpTransport", lambda port, ip, **_kw: ("udp", port, ip))

    assert telemetry_transport_factory(20777, replay_server, logging.getLogger("tests_telemetry_manager")) == expected
