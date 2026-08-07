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

"""F1TelemetryHandler's session-UID gate - see session-uid-clearing-plan.md, Commit 2."""

import logging
from types import SimpleNamespace

import pytest

import apps.backend.telemetry_layer.telemetry_handler as telemetry_handler_module
from apps.backend.state_mgmt_layer.session_state import SessionState
from apps.backend.telemetry_layer.telemetry_handler import F1TelemetryHandler
from lib.config import PngSettings
from lib.f1_types import (F1PacketType, GameMode, PacketSessionData,
                          SafetyCarType, SessionType24, TrackID,
                          WeatherForecastSample)
from lib.socket_receiver import TelemetryTransport

# ----------------------------------------------------------------------------------------------------------------------

class FakeTransport(TelemetryTransport):
    """Stands in for the real UDP/TCP transport, which binds a socket at construction time.
    F1TelemetryHandler.__init__ builds a transport unconditionally, so every test here needs
    one; this test never calls run()."""

    def on_packet(self, callback):
        pass

    async def run(self) -> None:
        pass

    async def close(self) -> None:
        pass

    def get_stats(self) -> dict:
        return {}


def _make_uid_only_packet(session_uid: int) -> SimpleNamespace:
    """Minimal packet stand-in for exercising the gate directly - it only reads the header."""
    return SimpleNamespace(
        m_header=SimpleNamespace(m_sessionUID=session_uid, m_packetId=F1PacketType.MOTION))


def _make_session_packet(session_uid: int) -> SimpleNamespace:
    """Duck-typed PacketSessionData, complete enough for handleSessionData's own typed
    processing (SessionState._processSessionUpdateHelper / SessionInfo.processSessionUpdate)."""
    return SimpleNamespace(
        m_header=SimpleNamespace(
            m_packetId=F1PacketType.SESSION, m_sessionUID=session_uid, m_gameYear=24, m_packetFormat=2024),
        m_sessionDuration=3600,
        m_formula=PacketSessionData.FormulaType.F1_MODERN,
        m_trackId=TrackID.Melbourne,
        m_trackLength=5000,
        m_trackTemperature=30,
        m_airTemperature=20,
        m_sessionType=SessionType24.PRACTICE_1,
        m_weather=WeatherForecastSample.WeatherCondition.CLEAR,
        m_gameMode=GameMode.GRAND_PRIX,
        m_weatherForecastSamples=[],
        m_pitSpeedLimit=80,
        m_totalLaps=25,
        m_isSpectating=False,
        m_spectatorCarIndex=255,
        m_safetyCarStatus=SafetyCarType.NO_SAFETY_CAR,
        m_pitStopWindowIdealLap=20,
    )


@pytest.fixture
def handler(monkeypatch) -> F1TelemetryHandler:
    """A real F1TelemetryHandler with a fake transport, so construction never binds a socket."""
    monkeypatch.setattr(
        telemetry_handler_module, "telemetry_transport_factory",
        lambda *_args, **_kwargs: FakeTransport())
    settings = PngSettings()
    logger = logging.getLogger("tests_telemetry_handler_uid_gate")
    session_state = SessionState(logger, settings, "test")
    return F1TelemetryHandler(settings, logger, session_state)

# ----------------------------------------------------------------------------------------------------------------------

async def test_uid_zero_is_ignored(handler):
    gate = handler.m_manager.m_any_packet_callback
    await gate(_make_uid_only_packet(0))

    assert handler.m_last_session_uid is None


async def test_new_uid_clears_on_first_sighting(handler):
    gate = handler.m_manager.m_any_packet_callback
    cleared = []
    handler.clearAllDataStructures = cleared.append

    await gate(_make_uid_only_packet(111))
    assert len(cleared) == 1
    assert handler.m_last_session_uid == 111

    # A second packet with the now-established UID must not clear again.
    await gate(_make_uid_only_packet(111))
    assert len(cleared) == 1


async def test_clear_lands_before_the_session_packets_own_handler_runs(handler):
    # A stale value clearAllDataStructures would wipe, proving the clear actually ran.
    handler.m_session_state_ref.m_num_active_cars = 99

    factory = SimpleNamespace(parse=lambda _raw: _make_session_packet(333))

    await handler.m_manager._processPacket(factory, b"unused")

    # Cleared by the gate, then repopulated by handleSessionData's own processing of this
    # same packet - both had to happen for m_session_uid to end up correct.
    assert handler.m_session_state_ref.m_num_active_cars is None
    assert handler.m_session_state_ref.m_session_info.m_session_uid == 333


def _make_session_history_packet(
        session_uid: int, car_idx: int = 3, frame: int = 11971, num_laps: int = 5) -> SimpleNamespace:
    return SimpleNamespace(
        m_header=SimpleNamespace(m_sessionUID=session_uid, m_frameIdentifier=frame),
        m_carIdx=car_idx,
        m_numLaps=num_laps,
    )


async def test_session_history_with_uid_zero_is_dropped(handler, monkeypatch):
    # Real-world case: a well-formed SESSION_HISTORY packet mid-session with UID 0, seen
    # from a spectator-mode capture, tied to user reports of bogus lap data.
    calls = []
    monkeypatch.setattr(SessionState, "processSessionHistoryUpdate", lambda _self, packet: calls.append(packet))
    monkeypatch.setattr(SessionState, "setRaceOngoing", lambda _self: calls.append("race-ongoing"))

    callback = handler.m_manager.m_callbacks[F1PacketType.SESSION_HISTORY]
    await callback(_make_session_history_packet(session_uid=0))

    assert not calls


async def test_session_history_with_real_uid_is_processed(handler, monkeypatch):
    calls = []
    monkeypatch.setattr(SessionState, "processSessionHistoryUpdate", lambda _self, packet: calls.append(packet))
    monkeypatch.setattr(SessionState, "setRaceOngoing", lambda _self: calls.append("race-ongoing"))

    packet = _make_session_history_packet(session_uid=333)
    callback = handler.m_manager.m_callbacks[F1PacketType.SESSION_HISTORY]
    await callback(packet)

    assert calls == [packet, "race-ongoing"]
