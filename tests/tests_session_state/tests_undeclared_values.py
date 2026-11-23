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

"""Undeclared wire values: a value a game build sends that our enums don't declare yet. safeCast keeps it as the raw
int, and the state layer must treat it as no special state rather than fail the packet."""

# ------------------------- IMPORTS ------------------------------------------------------------------------------------

import allure
import pytest

from apps.backend.state_mgmt_layer import SessionState
from lib.f1_types import LapData, ResultStatus, TrackID

from .harness import LAP_TRACK_LENGTHS, InjectingTelemetryManager
from .packet_helpers import ALL_FORMATS, Packets, ai, car, player

# ------------------------- CONSTANTS ----------------------------------------------------------------------------------

UID = 100
TRACK = TrackID.Silverstone
UNDECLARED_RESULT_STATUS = max(member.value for member in ResultStatus) + 1
UNDECLARED_PIT_STATUS = max(member.value for member in LapData.PitStatus) + 1

pytestmark = [allure.feature("Undeclared wire values"),
              pytest.mark.parametrize("packet_format", ALL_FORMATS, indirect=True)]

# ------------------------- TESTS --------------------------------------------------------------------------------------

@allure.story("Lap data")
@allure.title("An undeclared result and pit status don't drop the lap data ({packet_format})")
async def test_undeclared_lap_data_statuses_are_tolerated(manager: InjectingTelemetryManager, packets: Packets,
                                                          state: SessionState) -> None:
    """Race with the player on car 0 and an AI on car 1. Three LAP_DATA frames in which car 1 sends a result status
    and a pit status one past the last declared value, as a new game build might. No recording has one; the
    sequence is built.

    Expected: every frame is processed for both cars. Car 1 counts as active, is not in the pits and has no DNF code,
    as before the enum helpers, and its lap distance follows the packets."""
    await manager.inject(packets.session(session_uid=UID, session_type="RACE", track=TRACK, total_laps=5,
                                         track_length=LAP_TRACK_LENGTHS[TRACK]))
    await manager.inject(packets.participants(player("Player"), ai("AI"), session_uid=UID))
    for frame in range(1, 4):
        await manager.inject(packets.lap(
            car(0, lap=1, lap_distance=100.0 * frame),
            car(1, lap=1, lap_distance=90.0 * frame, result_status=UNDECLARED_RESULT_STATUS,
                pit_status=UNDECLARED_PIT_STATUS),
            session_uid=UID))

    ai_car = state.m_driver_data[1]
    assert state.m_num_active_cars == 2
    assert ai_car.m_lap_info.m_is_pitting is False
    assert ai_car.m_driver_info.m_dnf_status_code == ""
    assert ai_car.is_valid
    assert ai_car.m_packet_copies.m_packet_lap_data.m_lapDistance == 270.0
