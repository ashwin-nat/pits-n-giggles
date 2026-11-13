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
from lib.f1_types import TrackID

from .harness import InjectingTelemetryManager
from .packet_helpers import Packets, ai, car, lap_time, player

pytestmark = allure.feature("Frame gate")

# ------------------------- TESTS --------------------------------------------------------------------------------------

@pytest.mark.parametrize("frame_gate_enabled", [True], indirect=True)
async def test_other_types_stay_unique_per_frame(manager: InjectingTelemetryManager,
                                                 packets: Packets,
                                                 state: SessionState) -> None:
    await manager.inject(packets.session(session_uid=100, session_type="RACE", track=TrackID.Silverstone,
                                         total_laps=5, track_length=5891))
    await manager.inject(packets.participants(player("Player"), ai("Opponent"), session_uid=100))

    # Two LAP_DATA packets and one SESSION_HISTORY, all on overall frame 10
    await manager.inject(packets.lap(car(0, lap=1, lap_distance=1000), session_uid=100, overall_frame=10))
    await manager.inject(packets.lap(car(0, lap=1, lap_distance=1100), session_uid=100, overall_frame=10))
    await manager.inject(packets.session_history(car_idx=0, laps=[lap_time(92_000, valid=True)],
                                                 session_uid=100, overall_frame=10))

    # The second LAP_DATA is dropped. SESSION_HISTORY is a different type, so it gets through
    assert state.m_driver_data[0].m_packet_copies.m_packet_lap_data.m_lapDistance == 1000
    assert state.has_lap_data
    dropped = manager.getStats()["packets"]["__DROPPED_PACKETS_FRAME_GATE__"]
    assert {reason: stat["count"] for reason, stat in dropped.items()} == {"DUPLICATE_PACKET_TYPE": 1}
