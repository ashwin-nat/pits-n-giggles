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

"""Frame gate scenarios, with packet ordering on: which packets sharing one overall frame get through to the state.
The game sends several EVENT and SESSION_HISTORY packets in one frame, and every other type once.
"""

# ------------------------- IMPORTS ------------------------------------------------------------------------------------

from typing import Dict

import allure
import pytest

from apps.backend.state_mgmt_layer import SessionState
from lib.f1_types import F1PacketType, PacketEventData, SessionType24, TrackID
from lib.f1_types.common import get_num_cars
from lib.race_ctrl import MessageType

from .harness import (FP, LAP_TRACKS, QUALI, RACE, InjectingTelemetryManager,
                      PlayerCar, racing_status, title)
from .packet_helpers import ALL_FORMATS, Packets, ai, car, lap_time, player

# ------------------------- CONSTANTS ----------------------------------------------------------------------------------

UID = 100
GATE_ON = pytest.mark.parametrize("frame_gate_enabled", [True], indirect=True)

pytestmark = allure.feature("Frame gate")

# ------------------------- FIXTURES -----------------------------------------------------------------------------------

@pytest.fixture(params=LAP_TRACKS)
def track(request: pytest.FixtureRequest) -> TrackID:
    """Both track topologies."""
    return request.param

# ------------------------- HELPERS ------------------------------------------------------------------------------------

async def start(manager: InjectingTelemetryManager, packets: Packets, session: SessionType24) -> None:
    """A session at Silverstone with the player and three AI cars, all on lap 1."""
    await manager.inject(packets.session(session_uid=UID, session_type=session.name, track=TrackID.Silverstone,
                                         total_laps=5, track_length=5891))
    await manager.inject(packets.participants(player("Player"), ai("Alpha"), ai("Bravo"), ai("Charlie"),
                                              session_uid=UID))
    await manager.inject(packets.lap(*(car(index, lap=1, lap_distance=1000.0 - 100.0 * index,
                                           status=racing_status(session)) for index in range(4)), session_uid=UID))


def next_overall_frame(manager: InjectingTelemetryManager) -> int:
    """The overall frame after the last injected packet's."""
    return manager.injected[-1].m_header.m_overallFrameIdentifier + 1


def gate_drops(manager: InjectingTelemetryManager) -> Dict[str, int]:
    """The frame gate's drops so far, as reason -> count."""
    dropped = manager.getStats()["packets"].get("__DROPPED_PACKETS_FRAME_GATE__", {})
    return {reason: stat["count"] for reason, stat in dropped.items()}

# ------------------------- ONE OF EACH TYPE ---------------------------------------------------------------------------

@allure.story("One of each type per frame")
@GATE_ON
@allure.title("A second LAP_DATA on the same overall frame is dropped, another type isn't (Race, {packet_format})")
async def test_other_types_stay_unique_per_frame(manager: InjectingTelemetryManager, packets: Packets,
                                                 state: SessionState) -> None:
    """Race. Two LAP_DATA packets and a SESSION_HISTORY, all on overall frame 10.

    Expected: the second LAP_DATA is dropped as a duplicate. SESSION_HISTORY is another type, so it's processed."""
    await manager.inject(packets.session(session_uid=UID, session_type="RACE", track=TrackID.Silverstone,
                                         total_laps=5, track_length=5891))
    await manager.inject(packets.participants(player("Player"), ai("Opponent"), session_uid=UID))

    await manager.inject(packets.lap(car(0, lap=1, lap_distance=1000), session_uid=UID, overall_frame=10))
    await manager.inject(packets.lap(car(0, lap=1, lap_distance=1100), session_uid=UID, overall_frame=10))
    await manager.inject(packets.session_history(car_idx=0, laps=[lap_time(92_000, valid=True)],
                                                 session_uid=UID, overall_frame=10))

    assert state.m_driver_data[0].m_packet_copies.m_packet_lap_data.m_lapDistance == 1000
    stats = manager.getStats()["packets"]
    assert stats["__PROCESSED__"][str(F1PacketType.SESSION_HISTORY)]["count"] == 1
    assert gate_drops(manager) == {"DUPLICATE_PACKET_TYPE": 1}

# ------------------------- BURSTS -------------------------------------------------------------------------------------

@allure.story("Bursts on one frame")
@GATE_ON
@pytest.mark.parametrize("packet_format", ALL_FORMATS, indirect=True)
@pytest.mark.parametrize("session", [FP, QUALI, RACE])
@title("A flashback after a burst of button events on its frame is still handled")
async def test_flashback_after_a_button_burst_is_handled(
        player_car: PlayerCar, session: SessionType24, manager: InjectingTelemetryManager, packets: Packets,
        state: SessionState) -> None:
    """Practice, quali or race. Lap 1 is recorded up to 4511 m. Then 11 BUTTON_STATUS events and a FLBK arrive on
    one overall frame, as in f1_26_sp_quali_suzuka_flashback_mid_lap, and the car lands at 4154.3 m.

    Expected: none of the events is dropped, so the flashback is handled: the recorder and the delta manager are cut
    at the landing point, and the flashback flag is cleared by the landing."""
    await player_car.session(session)
    timed = racing_status(session)
    await player_car.drive(timed, 1, 0.6, 1500.0, 3000.0, 4000.0, 4300.0, 4511.0)

    burst_frame = next_overall_frame(manager)
    with allure.step(f"11 button events on overall frame {burst_frame}"):
        for _ in range(11):
            await manager.inject(packets.event(
                PacketEventData.EventPacketType.BUTTON_STATUS,
                PacketEventData.Buttons.from_status(PacketEventData.Buttons.udp_action_flag(5)),
                session_uid=player_car.session_uid, overall_frame=burst_frame))
    await player_car.flashback(timed, 1, 4154.3, overall_frame=burst_frame)

    assert gate_drops(manager) == {}
    assert player_car.in_progress_lap() == (1, [0.6, 1500.0, 3000.0, 4000.0, 4154.3])
    assert player_car.delta_laps() == {1: [0.6, 1500.0, 3000.0, 4000.0, 4154.3]}
    assert state.m_flashback_occurred is False


@allure.story("Bursts on one frame")
@GATE_ON
@pytest.mark.parametrize("packet_format", ALL_FORMATS, indirect=True)
@pytest.mark.parametrize("session", [FP, QUALI, RACE])
@allure.title("A SESSION_HISTORY for every car on one frame reaches every car ({session}, {packet_format})")
async def test_session_history_burst_is_applied_for_every_car(manager: InjectingTelemetryManager, packets: Packets,
                                                              state: SessionState, session: SessionType24) -> None:
    """Practice, quali or race. One SESSION_HISTORY per car on the grid, all on one overall frame, as the game sends
    them.

    Expected: none is dropped. Every car's session history packet copy is its own."""
    await start(manager, packets, session)
    num_cars = get_num_cars(packets.packet_format)
    for packet in packets.session_history_burst(laps=[lap_time(92_000, valid=True)], session_uid=UID,
                                                overall_frame=next_overall_frame(manager)):
        await manager.inject(packet)

    assert gate_drops(manager) == {}
    assert [state.m_driver_data[index].m_packet_copies.m_packet_session_history.m_carIdx
            for index in range(num_cars)] == list(range(num_cars))


@allure.story("Bursts on one frame")
@GATE_ON
@pytest.mark.parametrize("packet_format", ALL_FORMATS, indirect=True)
@pytest.mark.parametrize("session", [FP, QUALI, RACE])
@allure.title("Overtakes on one frame are all recorded ({session}, {packet_format})")
async def test_overtakes_in_one_frame_are_all_recorded(manager: InjectingTelemetryManager, packets: Packets,
                                                       state: SessionState, session: SessionType24) -> None:
    """Practice, quali or race. Three OVTK events on one overall frame: car 1 passes car 0, car 2 passes car 1, and
    car 3 passes car 2.

    Expected: none is dropped. All three are in the overtakes history and in race control."""
    await start(manager, packets, session)
    burst_frame = next_overall_frame(manager)
    for overtaker in (1, 2, 3):
        await manager.inject(packets.event(PacketEventData.EventPacketType.OVERTAKE,
                                           PacketEventData.Overtake.from_values(overtaker, overtaker - 1),
                                           session_uid=UID, overall_frame=burst_frame))

    assert gate_drops(manager) == {}
    assert [(record.m_overtaking_driver_name, record.m_overtaken_driver_name)
            for record in state.m_overtakes_history.m_overtakes_history] == \
        [("Alpha", "Player"), ("Bravo", "Alpha"), ("Charlie", "Bravo")]
    assert sum(msg.message_type == MessageType.OVERTAKE for msg in state.m_race_ctrl.messages) == 3
