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

"""Lap timer going back without a lap change: at the race end, when F1 zeroes every unfinished car's timer mid-lap
and every finished car's timer on the line, and mid-race. The lap recorder drops any sample whose lap time is
below the last kept one. Timers are from the test_data recordings; distances are shortened to fit Monaco."""

# Fixtures that take other fixtures as arguments are how pytest works, not shadowing
# pylint: disable=redefined-outer-name

# ------------------------- IMPORTS ------------------------------------------------------------------------------------

from typing import Dict, List, Optional, Tuple

import allure
import pytest

from apps.backend.state_mgmt_layer import SessionState
from lib.f1_types import PacketEventData, SessionType24, TrackID

from .harness import (LAP_TRACK_LENGTHS, LAP_TRACKS, RACE,
                      InjectingTelemetryManager, title)
from .packet_helpers import (ALL_FORMATS, CarSpec, Packets, ai, car,
                             classified, fuel_and_ers, player)

# ------------------------- CONSTANTS ----------------------------------------------------------------------------------

UID = 100
PLAYER, AI = 0, 1
LAST_LAP = 5

Samples = List[Tuple[float, int]]

pytestmark = [allure.feature("Race end"),
              pytest.mark.parametrize("packet_format", ALL_FORMATS, indirect=True),
              pytest.mark.parametrize("session", [RACE])]

# ------------------------- FIXTURES -----------------------------------------------------------------------------------

@pytest.fixture(params=LAP_TRACKS)
def track(request: pytest.FixtureRequest) -> TrackID:
    """Both track topologies."""
    return request.param

# ------------------------- HELPERS ------------------------------------------------------------------------------------

async def _race(manager: InjectingTelemetryManager, packets: Packets, session: SessionType24, track: TrackID) -> None:
    """A 5 lap session on track on UID 100: the player on car 0, an AI on car 1."""
    await manager.inject(packets.session(session_uid=UID, session_type=session.name, track=track, total_laps=LAST_LAP,
                                         track_length=LAP_TRACK_LENGTHS[track]))
    await manager.inject(packets.participants(player("Player"), ai("AI"), session_uid=UID))


async def _lap_data(manager: InjectingTelemetryManager, packets: Packets, *cars: CarSpec) -> None:
    await manager.inject(packets.lap(*cars, session_uid=UID))


async def _final_classification(manager: InjectingTelemetryManager, packets: Packets) -> None:
    await manager.inject(packets.final_classification(classified(position=1, num_laps=LAST_LAP),
                                                      classified(position=2, num_laps=LAST_LAP), session_uid=UID))


def _completed(state: SessionState, index: int) -> Dict[int, Samples]:
    """Car index's completed laps, as lap number -> (distance to 0.1 m, lap time in ms) per sample."""
    return {lap.metadata.lap_number: _samples(lap.telemetry)
            for lap in state.m_driver_data[index].m_tel_rec.export().completed_laps}


def _in_progress(state: SessionState, index: int) -> Optional[Tuple[int, Samples]]:
    lap = state.m_driver_data[index].m_tel_rec.export().in_progress_lap
    return None if lap is None else (lap.metadata.lap_number, _samples(lap.telemetry))


def _samples(telemetry: Dict[str, list]) -> Samples:
    return [(round(distance, 1), lap_time_ms)
            for distance, lap_time_ms in zip(telemetry["lap_distance"], telemetry["lap_time_ms"])]

# ------------------------- RACE END -----------------------------------------------------------------------------------

@allure.story("Race end timer reset")
@title("An unfinished AI car's timer reset when the player finishes is not recorded")
async def test_race_end_ai_timer_reset_is_not_recorded(manager: InjectingTelemetryManager, packets: Packets,
                                                       state: SessionState, session: SessionType24,
                                                       track: TrackID) -> None:
    """Race, last lap, as in f1_26_sp_monza_restricted_5lap (car 0): the player leads the AI, which is still mid-lap
    at 2404.8 m / 72143 ms when the player crosses the line and stays on lap 5 (0.2 m, 0 ms). Two frames later the
    AI's timer drops to 16 ms while its distance keeps rising. Then FINAL_CLASSIFICATION, 5 laps each. (A car
    finishing ahead of the player is the cool-down row.)

    Expected: the AI's lap 5 is stored by the final classification and ends at its last sample before the reset.
    No 16 ms sample is kept, and the lap time never goes down. The player's lap 5 ends before its line."""
    length = LAP_TRACK_LENGTHS[track]
    await _race(manager, packets, session, track)
    await _lap_data(manager, packets, car(PLAYER, LAST_LAP, length - 50.0, lap_time_ms=84_500),
                    car(AI, LAST_LAP, 2000.0, lap_time_ms=63_300))
    await _lap_data(manager, packets, car(PLAYER, LAST_LAP, length - 3.1, lap_time_ms=85_120),
                    car(AI, LAST_LAP, 2404.8, lap_time_ms=72_143))
    with allure.step("The player crosses the line, then the AI's timer resets"):
        await _lap_data(manager, packets, car(PLAYER, LAST_LAP, 0.2), car(AI, LAST_LAP, 2405.6, lap_time_ms=72_160))
        await _lap_data(manager, packets, car(PLAYER, LAST_LAP, 1.2, lap_time_ms=16),
                        car(AI, LAST_LAP, 2406.3, lap_time_ms=16))
        await _lap_data(manager, packets, car(PLAYER, LAST_LAP, 2.3, lap_time_ms=16),
                        car(AI, LAST_LAP, 2407.4, lap_time_ms=16))
    assert _in_progress(state, AI) == (LAST_LAP, [(2000.0, 63_300), (2404.8, 72_143), (2405.6, 72_160)])

    await _final_classification(manager, packets)

    assert _completed(state, AI) == {LAST_LAP: [(2000.0, 63_300), (2404.8, 72_143), (2405.6, 72_160)]}
    assert _completed(state, PLAYER) == {LAST_LAP: [(length - 50.0, 84_500), (length - 3.1, 85_120)]}
    assert _in_progress(state, AI) is None


@allure.story("Race end timer reset")
@title("A timer reset at the same distance doesn't overwrite the last sample")
async def test_race_end_timer_reset_at_the_same_distance_keeps_the_last_sample(
        manager: InjectingTelemetryManager, packets: Packets, state: SessionState, session: SessionType24,
        track: TrackID) -> None:
    """Race, last lap: the AI reaches 2405.6 m at 72160 ms, then its timer resets to 16 ms at that same distance.
    (Constructed: in f1_26_sp_monza_restricted_5lap the reset step is always forward, 0.8 m at the least.) Then
    FINAL_CLASSIFICATION.

    Expected: the AI's lap 5 ends at 2405.6 m / 72160 ms. The reset sample doesn't overwrite it."""
    await _race(manager, packets, session, track)
    await _lap_data(manager, packets, car(AI, LAST_LAP, 2000.0, lap_time_ms=63_300))
    await _lap_data(manager, packets, car(AI, LAST_LAP, 2405.6, lap_time_ms=72_160))
    await _lap_data(manager, packets, car(AI, LAST_LAP, 2405.6, lap_time_ms=16))
    await _final_classification(manager, packets)

    assert _completed(state, AI) == {LAST_LAP: [(2000.0, 63_300), (2405.6, 72_160)]}


@allure.story("Race end timer reset")
@title("A finished car's cool-down after its line is not recorded")
async def test_race_end_cool_down_after_the_reset_is_not_recorded(manager: InjectingTelemetryManager,
                                                                  packets: Packets, state: SessionState,
                                                                  session: SessionType24, track: TrackID) -> None:
    """Race, last lap, as in f1_26_sp_hungary_35_laps (car 4, lap 35): the AI reaches 4 m before the line at
    81777 ms and crosses it, staying on lap 5: 0 m / 0 ms, then 1.1 m / 16 ms, then climbing to 915 m with the
    timer stuck at 16. Then (constructed) past its last kept distance, still at 16 ms. Then FINAL_CLASSIFICATION.

    Expected: the AI's lap 5 ends at 4 m before the line / 81777 ms. Nothing after it is kept, including once the
    distance passes the last kept one again."""
    length = LAP_TRACK_LENGTHS[track]
    await _race(manager, packets, session, track)
    await _lap_data(manager, packets, car(AI, LAST_LAP, length / 2, lap_time_ms=41_000))
    await _lap_data(manager, packets, car(AI, LAST_LAP, length - 4.0, lap_time_ms=81_777))
    with allure.step("The AI crosses the line on its last lap"):
        await _lap_data(manager, packets, car(AI, LAST_LAP, 0.0, lap_time_ms=0))
        for distance in (1.1, 2.1, 915.0, length - 2.0):
            await _lap_data(manager, packets, car(AI, LAST_LAP, distance, lap_time_ms=16))
    await _final_classification(manager, packets)

    assert _completed(state, AI) == {LAST_LAP: [(length / 2, 41_000), (length - 4.0, 81_777)]}


@allure.story("Race end timer reset")
@title("Lap 5's tyre laps is the tyre age at final classification, one more for a car past its line")
async def test_race_end_tyre_laps_is_the_tyre_age_at_final_classification(manager: InjectingTelemetryManager,
                                                                          packets: Packets, state: SessionState,
                                                                          session: SessionType24,
                                                                          track: TrackID) -> None:
    """Race: both cars cross onto lap 5 with tyres 3 laps old, which then reads 4. The player crosses the line on
    lap 5 and its tyre age reads 5, while the AI's stays at 4. Then FINAL_CLASSIFICATION. As in
    f1_26_sp_monza_restricted_5lap, where the cars past their line read 5 at the end and the rest 4.

    Expected: lap 4's tyre laps is 3 for both. Lap 5's is 5 for the player and 4 for the AI: the age read at final
    classification. Pinned as it is: the player's 5 is one more than the lap 1 to 4 pattern."""
    length = LAP_TRACK_LENGTHS[track]
    await _race(manager, packets, session, track)

    async def tyre_ages(player_age: int, ai_age: int) -> None:
        await manager.inject(packets.car_status(fuel_and_ers(PLAYER, tyres_age_laps=player_age),
                                                fuel_and_ers(AI, tyres_age_laps=ai_age), session_uid=UID))

    await tyre_ages(3, 3)
    await _lap_data(manager, packets, car(PLAYER, 4, length - 10.0, lap_time_ms=85_000),
                    car(AI, 4, length - 20.0, lap_time_ms=85_500))
    await _lap_data(manager, packets, car(PLAYER, LAST_LAP, 1.0, lap_time_ms=20), car(AI, LAST_LAP, 1.0, lap_time_ms=20))
    await tyre_ages(4, 4)
    await _lap_data(manager, packets, car(PLAYER, LAST_LAP, length - 10.0, lap_time_ms=84_000),
                    car(AI, LAST_LAP, length - 200.0, lap_time_ms=81_000))
    with allure.step("The player crosses the line on its last lap"):
        await _lap_data(manager, packets, car(PLAYER, LAST_LAP, 0.2), car(AI, LAST_LAP, length - 180.0,
                                                                          lap_time_ms=81_300))
        await tyre_ages(5, 4)
    await _final_classification(manager, packets)

    tyre_laps = {index: {lap.metadata.lap_number: lap.metadata.tyre_laps
                         for lap in state.m_driver_data[index].m_tel_rec.export().completed_laps}
                 for index in (PLAYER, AI)}
    assert tyre_laps == {PLAYER: {4: 3, LAST_LAP: 5}, AI: {4: 3, LAST_LAP: 4}}

# ------------------------- MID-RACE -----------------------------------------------------------------------------------

@allure.story("Timer going back mid-race")
@title("A step back in distance and lap time, with no flashback, is dropped")
async def test_lap_time_going_back_with_distance_is_dropped(manager: InjectingTelemetryManager, packets: Packets,
                                                            state: SessionState, session: SessionType24,
                                                            track: TrackID) -> None:
    """Race, lap 3, as in f1_26_sp_hungary_35_laps at overall frame 11385: every car steps back 1 to 2 m and a few
    ms in one LAP_DATA, with no FLBK, then carries on. Then both cars cross onto lap 4.

    Expected: one sample per car is dropped, and lap 3 is recorded as it would be without it."""
    await _race(manager, packets, session, track)
    for player_sample, ai_sample in (((1000.0, 16_400), (900.0, 14_950)),
                                     ((1032.2, 16_919), (921.3, 15_304)),
                                     ((1030.3, 16_908), (919.0, 15_301)),     # the step back
                                     ((1033.0, 16_935), (922.1, 15_320))):
        await _lap_data(manager, packets, car(PLAYER, 3, player_sample[0], lap_time_ms=player_sample[1]),
                        car(AI, 3, ai_sample[0], lap_time_ms=ai_sample[1]))
    await _lap_data(manager, packets, car(PLAYER, 4, 1.0, lap_time_ms=20), car(AI, 4, 1.0, lap_time_ms=20))

    assert _completed(state, PLAYER) == {3: [(1000.0, 16_400), (1032.2, 16_919), (1033.0, 16_935)]}
    assert _completed(state, AI) == {3: [(900.0, 14_950), (921.3, 15_304), (922.1, 15_320)]}


@allure.story("Timer going back mid-race")
@title("A flashback landing whose timer is below the last kept sample is dropped")
async def test_flashback_landing_with_a_rewound_timer_is_dropped(manager: InjectingTelemetryManager,
                                                                 packets: Packets, state: SessionState,
                                                                 session: SessionType24, track: TrackID) -> None:
    """Race, lap 2, as in f1_25_sp_qatar_flashback_1stop (overall frame 4899, the one such landing in 74 across
    test_data): the player passes 2291.9 m at 76637 ms and goes on to 2600 m. A FLBK lands it at 2292.5 m with the
    timer at 76634 ms, 3 ms below the sample before it. Then it drives on.

    Expected: the rollback keeps the samples up to 2291.9 m. The landing sample is dropped (the accepted limit,
    since a flashback has no exemption) and recording carries on from the next one."""
    await _race(manager, packets, session, track)
    for distance, lap_time_ms in ((2000.0, 70_000), (2291.9, 76_637), (2600.0, 83_000)):
        await _lap_data(manager, packets, car(PLAYER, 2, distance, lap_time_ms=lap_time_ms))
    target_frame = manager.injected[-1].m_header.m_frameIdentifier // 2
    with allure.step("Flashback, landing at 2292.5 m, 76634 ms"):
        await manager.inject(packets.event(PacketEventData.EventPacketType.FLASHBACK,
                                           PacketEventData.Flashback.from_values(frame_identifier=target_frame),
                                           session_uid=UID))
        await manager.inject(packets.lap(car(PLAYER, 2, 2292.5, lap_time_ms=76_634), session_uid=UID,
                                         frame=target_frame + 1))
    for distance, lap_time_ms in ((2293.4, 76_650), (2294.3, 76_667)):
        await _lap_data(manager, packets, car(PLAYER, 2, distance, lap_time_ms=lap_time_ms))

    assert _in_progress(state, PLAYER) == (2, [(2000.0, 70_000), (2291.9, 76_637), (2293.4, 76_650),
                                               (2294.3, 76_667)])
