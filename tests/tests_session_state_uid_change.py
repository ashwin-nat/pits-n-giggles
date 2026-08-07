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

"""SessionState.processSessionUpdate no longer clears on its own - see
session-uid-clearing-plan.md, Commit 2, Problem 3 (double clear / blanked session info)."""

import logging
from types import SimpleNamespace

from lib.config import PngSettings
from lib.f1_types import (GameMode, PacketSessionData, SafetyCarType,
                          SessionType24, TrackID, WeatherForecastSample)
from apps.backend.state_mgmt_layer.session_state import SessionState

# ----------------------------------------------------------------------------------------------------------------------

def _make_session_packet(session_uid: int, track: TrackID = TrackID.Melbourne) -> SimpleNamespace:
    """Duck-typed stand-in for PacketSessionData carrying only the fields
    SessionState._processSessionUpdateHelper and SessionInfo.processSessionUpdate read."""
    return SimpleNamespace(
        m_header=SimpleNamespace(m_sessionUID=session_uid, m_gameYear=24, m_packetFormat=2024),
        m_formula=PacketSessionData.FormulaType.F1_MODERN,
        m_trackId=track,
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


def _make_session_state() -> SessionState:
    return SessionState(logging.getLogger("tests_session_state_uid_change"), PngSettings(), "test")

# ----------------------------------------------------------------------------------------------------------------------

async def test_session_info_survives_a_uid_change_without_an_explicit_clear():
    state = _make_session_state()

    await state.processSessionUpdate(_make_session_packet(session_uid=111, track=TrackID.Melbourne))
    assert state.m_session_info.m_session_uid == 111
    assert state.m_session_info.m_track == TrackID.Melbourne

    # A second packet under a different UID, with no clear() in between - the UID gate in
    # F1TelemetryHandler owns clearing now, not this method.
    await state.processSessionUpdate(_make_session_packet(session_uid=222, track=TrackID.Paul_Ricard))

    assert state.m_session_info.m_session_uid == 222
    assert state.m_session_info.m_track == TrackID.Paul_Ricard
    assert state.m_session_info.m_total_laps == 25


async def test_process_session_update_does_not_clear_driver_data():
    state = _make_session_state()
    await state.processSessionUpdate(_make_session_packet(session_uid=111))

    # Populate something clear() would wipe, then feed a UID change through the same path.
    state.m_num_active_cars = 20
    await state.processSessionUpdate(_make_session_packet(session_uid=222))

    assert state.m_num_active_cars == 20
