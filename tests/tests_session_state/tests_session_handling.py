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

import allure
import pytest

from apps.backend.state_mgmt_layer import SessionState
from apps.backend.telemetry_layer.telemetry_handler import F1TelemetryHandler
from lib.f1_types import TrackID

from .harness import (FakeSubsystem, InjectingTelemetryManager, SaveRecorder,
                      SaveRequestRecord, TokenRecorder)
from .packet_helpers import (ALL_FORMATS, Packets, ai, car, classified,
                             lap_time, player)

pytestmark = allure.feature("Session handling")

# ------------------------- HELPERS ------------------------------------------------------------------------------------

async def _race_in_progress(manager: InjectingTelemetryManager, packets: Packets, session_uid: int) -> None:
    """A race on session_uid: session, two cars, one lap in progress, a lap history for the player."""
    await manager.inject(packets.session(session_uid=session_uid, session_type="RACE", track=TrackID.Silverstone,
                                         total_laps=5, track_length=5891))
    await manager.inject(packets.participants(player("Player"), ai("Opponent"), session_uid=session_uid))
    await manager.inject(packets.lap(car(0, lap=1, lap_distance=1000), car(1, lap=1, lap_distance=900),
                                     session_uid=session_uid))
    await manager.inject(packets.session_history(car_idx=0, laps=[lap_time(92_000, valid=True)],
                                                 session_uid=session_uid))

# ------------------------- TESTS --------------------------------------------------------------------------------------

@allure.story("Session UID change")
@pytest.mark.parametrize("packet_format", ALL_FORMATS, indirect=True)
async def test_uid_change_clears_and_saves_just_in_case(manager: InjectingTelemetryManager,
                                                        packets: Packets,
                                                        state: SessionState,
                                                        handler: F1TelemetryHandler,
                                                        saves: SaveRecorder,
                                                        tokens: TokenRecorder) -> None:
    await _race_in_progress(manager, packets, session_uid=100)
    assert state.has_lap_data
    assert saves.requests == []

    # The first packet of a new session, and no FINAL_CLASSIFICATION was ever received for UID 100
    await manager.inject(packets.lap(car(0, lap=1, lap_distance=10), session_uid=200))

    assert saves.requests == [SaveRequestRecord(kind="just_in_case", session_uid=100, reason="Just_in_case")]
    assert tokens.records == []
    assert handler.m_last_session_uid == 200
    assert state.m_session_info.m_session_uid is None
    assert all(driver is None for driver in state.m_driver_data)


@allure.story("Session UID change")
async def test_uid_change_after_final_classification_skips_just_in_case(manager: InjectingTelemetryManager,
                                                                        packets: Packets,
                                                                        state: SessionState,
                                                                        handler: F1TelemetryHandler,
                                                                        saves: SaveRecorder,
                                                                        tokens: TokenRecorder) -> None:
    await _race_in_progress(manager, packets, session_uid=100)
    await manager.inject(packets.final_classification(classified(position=1, num_laps=5),
                                                      classified(position=2, num_laps=5), session_uid=100))
    assert saves.requests == [SaveRequestRecord(kind="final_classification", session_uid=100, reason=None)]

    await manager.inject(packets.lap(car(0, lap=1, lap_distance=10), session_uid=200))

    # Only the final classification save. The session ended properly, so no just-in-case save
    assert saves.requests == [SaveRequestRecord(kind="final_classification", session_uid=100, reason=None)]
    assert tokens.records == []
    assert handler.m_last_session_uid == 200
    assert all(driver is None for driver in state.m_driver_data)


@allure.story("Handler wiring")
async def test_register_tasks_needs_an_async_manager(handler: F1TelemetryHandler,
                                                     fake_subsystem: FakeSubsystem) -> None:
    """The receive loop and raw-packet wiring only exist on AsyncF1TelemetryManager."""
    with pytest.raises(TypeError, match="needs an AsyncF1TelemetryManager, got InjectingTelemetryManager"):
        handler.register_tasks(fake_subsystem)


@allure.story("Final classification")
@pytest.mark.parametrize("packet_format", ALL_FORMATS, indirect=True)
async def test_final_classification_before_any_lap_data(manager: InjectingTelemetryManager,
                                                        packets: Packets,
                                                        state: SessionState,
                                                        saves: SaveRecorder) -> None:
    """No car has sent LAP_DATA, so none has a speed trap reading. The final classification save still works."""
    await manager.inject(packets.session(session_uid=100, session_type="RACE", track=TrackID.Silverstone,
                                         total_laps=5, track_length=5891))
    await manager.inject(packets.participants(player("Player"), ai("Opponent"), session_uid=100))
    await manager.inject(packets.final_classification(classified(position=1, num_laps=5),
                                                      classified(position=2, num_laps=5), session_uid=100))

    assert saves.requests == [SaveRequestRecord(kind="final_classification", session_uid=100, reason=None)]
    expected = [] if packets.packet_format == 2023 else ["Player", "Opponent"]   # 2023 has no speed trap records
    assert [r["name"] for r in state.buildFinalClassificationJSON()["speed-trap-records"]] == expected
