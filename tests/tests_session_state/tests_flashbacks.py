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

"""Flashback scenarios: what a FLBK event and the LAP_DATA the car lands in do to the lap recorder, the delta
manager and the per-lap snapshots. Flashbacks across the tyre set history are in tests_tyre_change.py.
"""

# ------------------------- IMPORTS ------------------------------------------------------------------------------------

from typing import Dict, List, NamedTuple, Optional, Tuple

import allure
import pytest

from apps.backend.state_mgmt_layer import SessionState
from lib.f1_types import SessionType24, TrackID
from lib.f1_types.packet_2_lap_data import LapData

from .harness import (FLYING, FP, GARAGE, IN_LAP, LAP_TRACK_LENGTHS, OUT_LAP, QUALI,
                      RACE, TT, InjectingTelemetryManager, PlayerCar, flashback,
                      racing_status, title)
from .packet_helpers import (ALL_FORMATS, Packets, ai, car, fuel_and_ers,
                             player)

# ------------------------- CONSTANTS ----------------------------------------------------------------------------------

UID = 100

pytestmark = [allure.feature("Flashbacks"),
              pytest.mark.parametrize("packet_format", ALL_FORMATS, indirect=True)]

# ------------------------- WITHIN A LAP -------------------------------------------------------------------------------

@allure.story("Within a lap")
@pytest.mark.parametrize("session", [FP, QUALI, RACE])
@title("A flashback within a lap cuts the recording at the landing point")
async def test_flashback_within_a_lap_truncates_at_the_landing_point(
        player_car: PlayerCar, session: SessionType24) -> None:
    """Practice, quali or race. Lap 1 is recorded up to 4511 m, then a flashback lands at 4154.3 m on the same lap, on
    an earlier frame. The sim resumes about 154 m past its own target, so the landing is past samples it rewound over.

    Expected: the recorder and the delta manager keep the samples below 4154.3 m, plus the landing sample. The lap
    carries on from there with no hole before the landing point."""
    await player_car.session(session)
    timed = racing_status(session)
    await player_car.drive(timed, 1, 0.6, 1500.0, 3000.0, 4000.0, 4300.0, 4511.0)
    await player_car.flashback(timed, 1, 4154.3)
    assert player_car.in_progress_lap() == (1, [0.6, 1500.0, 3000.0, 4000.0, 4154.3])
    assert player_car.delta_laps() == {1: [0.6, 1500.0, 3000.0, 4000.0, 4154.3]}

    await player_car.drive(timed, 1, 4300.0, 5800.0)
    await player_car.drive(timed, 2, 0.6)
    assert player_car.completed_laps() == {1: [0.6, 1500.0, 3000.0, 4000.0, 4154.3, 4300.0, 5800.0]}


@allure.story("Within a lap")
@pytest.mark.parametrize("session", [TT])
@title("A time trial flashback rolls back the recording and leaves the delta alone")
async def test_time_trial_flashback_skips_the_delta(player_car: PlayerCar, session: SessionType24) -> None:
    """Time trial. Lap 1 is recorded up to 4511 m, then a flashback lands at 4154.3 m on the same lap.

    Expected: the recorder rolls back to the landing point. The delta manager isn't used in time trial, and the
    flashback doesn't start using it."""
    await player_car.session(session)
    await player_car.drive(FLYING, 1, 0.6, 1500.0, 3000.0, 4000.0, 4300.0, 4511.0)
    await player_car.flashback(FLYING, 1, 4154.3)

    assert player_car.in_progress_lap() == (1, [0.6, 1500.0, 3000.0, 4000.0, 4154.3])
    assert player_car.delta_laps() == {}


class CarFrame(NamedTuple):
    """The MOTION and CAR_TELEMETRY values a frame carries for the player, after its LAP_DATA."""
    x: float
    y: float
    z: float
    yaw: float
    kmph: int


# From the Monza recording either side of the rewind, at float32-exact values
BEFORE_REWIND = CarFrame(x=-439.75, y=-5.5, z=1086.25, yaw=-1.0, kmph=154)
AFTER_REWIND = CarFrame(x=-331.5, y=-2.5, z=427.5, yaw=-0.125, kmph=315)


async def _send_frame_copies(player_car: PlayerCar, frame: CarFrame) -> None:
    await player_car.position(frame.x, frame.y, frame.z, frame.yaw)
    await player_car.speed(frame.kmph)


async def _drive_frames(player_car: PlayerCar, status: LapData.DriverStatus, lap: int, distances: List[float],
                        frame: CarFrame) -> None:
    for distance in distances:
        await player_car.drive(status, lap, distance)
        await _send_frame_copies(player_car, frame)


@allure.story("Within a lap")
@pytest.mark.parametrize("session", [FP, QUALI, RACE])
@title("The landing sample carries no position or speed from before the rewind")
async def test_flashback_landing_sample_has_no_pre_rewind_values(player_car: PlayerCar, session: SessionType24) -> None:
    """Practice, quali or race. The game sends each frame's LAP_DATA first, then MOTION, then CAR_TELEMETRY. The car
    drives lap 1 to 4511 m at z 1086.25 m and 154 km/h. A flashback then takes it back to 4154.3 m, where it is at
    z 427.5 m and 315 km/h. It drives on to 5800 m and starts lap 2.
    Seen in test_data/f1_26_sp_monza_restricted_5lap.f1pcap at overall frame 26059.

    Expected: from 4154.3 m on, lap 1 holds only the position and speed from after the flashback. Nothing from
    before it is recorded, including at the landing, where the LAP_DATA arrives before the new MOTION and
    CAR_TELEMETRY."""
    await player_car.session(session)
    timed = racing_status(session)
    await _drive_frames(player_car, timed, 1, [0.6, 1500.0, 3000.0, 4000.0, 4300.0, 4511.0], BEFORE_REWIND)
    await player_car.flashback(timed, 1, 4154.3)
    await _send_frame_copies(player_car, AFTER_REWIND)
    await _drive_frames(player_car, timed, 1, [4300.0, 5800.0], AFTER_REWIND)
    await player_car.drive(timed, 2, 0.6)

    lap_1 = player_car.driver.m_tel_rec.export().completed_laps[0].telemetry
    samples = zip(lap_1["lap_distance"], lap_1["motion.position.z"], lap_1["speed"])
    from_before_rewind = [(round(distance, 1), z, kmph) for distance, z, kmph in samples
                          if round(distance, 1) >= 4154.3 and (z, kmph) != (AFTER_REWIND.z, AFTER_REWIND.kmph)]
    assert from_before_rewind == []

# ------------------------- OVER THE LINE ------------------------------------------------------------------------------

@allure.story("Over the line")
@pytest.mark.parametrize("session", [FP, QUALI, RACE])
@title("A flashback over the line redoes the previous lap")
async def test_race_flashback_over_the_line_redoes_the_lap(player_car: PlayerCar, session: SessionType24) -> None:
    """Practice, quali or race. Laps 1 and 2 are done and the car is a few seconds into lap 3, then a flashback lands
    back on lap 2 at 5750 m. The car crosses the line again, and drives lap 3 to the end.

    Expected: the landing drops lap 2's per-lap snapshot and the delta manager's lap 3. The recorder reopens lap 2,
    cut at the landing point. Crossing the line again stores lap 2 properly (it used to go missing, with lap 3
    holding lap 2's trace) and takes a new lap 2 snapshot. Lap 3 is then complete."""
    await player_car.session(session)
    timed = racing_status(session)
    await player_car.drive(timed, 1, 0.6, 2900.0, 5800.0)
    await player_car.drive(timed, 2, 0.6, 2900.0, 5700.0, 5800.0)
    await player_car.drive(timed, 3, 0.6, 100.0, 300.0)
    first_lap_2_snapshot = player_car.driver.m_per_lap_snapshots[2]

    await player_car.flashback(timed, 2, 5750.0)
    assert 2 not in player_car.driver.m_per_lap_snapshots and 1 in player_car.driver.m_per_lap_snapshots
    assert player_car.delta_laps() == {1: [0.6, 2900.0, 5800.0], 2: [0.6, 2900.0, 5700.0, 5750.0]}
    assert player_car.completed_laps() == {1: [0.6, 2900.0, 5800.0]}
    assert player_car.in_progress_lap() == (2, [0.6, 2900.0, 5700.0, 5750.0])

    await player_car.drive(timed, 2, 5800.0)
    await player_car.drive(timed, 3, 0.6, 2900.0, 5800.0)
    await player_car.drive(timed, 4, 0.6)
    assert player_car.completed_laps() == {1: [0.6, 2900.0, 5800.0],
                                    2: [0.6, 2900.0, 5700.0, 5750.0, 5800.0],
                                    3: [0.6, 2900.0, 5800.0]}
    assert player_car.driver.m_per_lap_snapshots[2] is not first_lap_2_snapshot
    assert 3 in player_car.driver.m_per_lap_snapshots

# ------------------------- ONTO THE OUT LAP ---------------------------------------------------------------------------

@allure.story("Onto the out lap")
@pytest.mark.parametrize("session", [FP, QUALI])
@title("A flashback onto the out lap makes the next crossing start the lap again")
async def test_quali_flashback_onto_the_out_lap_restarts_the_line(
        player_car: PlayerCar, session: SessionType24) -> None:
    """Practice or quali. Out lap, the line, 149 m into the flying lap, then a flashback lands back on the out lap at
    -248.8 m. The car crosses the line again.

    Expected: the landing empties the in-progress lap down to the landing sample. The second crossing starts the lap
    again, so lap 1 holds only the flying lap, not the out lap samples after the landing. Snapshot re-baselining at
    that crossing is test_second_crossing_rebaselines_again (13.5)."""
    await player_car.session(session)
    await player_car.drive(GARAGE, 1, -5581.2)
    await player_car.drive(OUT_LAP, 1, -5581.1, -1000.0, -1.2)
    await player_car.drive(FLYING, 1, 0.6, 149.0)
    assert player_car.in_progress_lap() == (1, [0.6, 149.0])

    await player_car.flashback(OUT_LAP, 1, -248.8)
    assert player_car.in_progress_lap() == (1, [-248.8])

    await player_car.drive(OUT_LAP, 1, -100.0, -1.2)
    await player_car.drive(FLYING, 1, 0.6, 2900.0, 5800.0)
    await player_car.drive(FLYING, 2, 0.6)
    assert player_car.completed_laps() == {1: [0.6, 2900.0, 5800.0]}

@allure.story("Onto the out lap")
@pytest.mark.parametrize("session", [FP, QUALI])
@title("A flashback from an out lap back onto a flying lap is not a lap start")
async def test_landing_on_a_flying_lap_from_an_out_lap_is_not_a_lap_start(
        player_car: PlayerCar, session: SessionType24) -> None:
    """Practice or quali. Lap 2 is a flying lap, then an in lap through the pit lane without stopping, and an out lap on
    lap 3. A flashback from the out lap lands back on lap 2's flying lap at 3500 m. Constructed, not captured.

    Expected: the landing changes the status from OUT_LAP to FLYING_LAP but isn't a lap start, so the reopened lap 2
    keeps its samples below 3500 m."""
    await player_car.session(session)
    await player_car.drive(FLYING, 1, 2900.0, 5800.0)
    await player_car.drive(FLYING, 2, 0.6, 2900.0, 4000.0)
    await player_car.drive(IN_LAP, 2, 4500.0, 5809.8)
    await player_car.drive(OUT_LAP, 3, 0.1, 500.0)

    await player_car.flashback(FLYING, 2, 3500.0)
    assert player_car.in_progress_lap() == (2, [0.6, 2900.0, 3500.0])

    await player_car.drive(FLYING, 2, 5800.0)
    await player_car.drive(FLYING, 3, 0.6)
    assert player_car.completed_laps() == {1: [2900.0, 5800.0], 2: [0.6, 2900.0, 3500.0, 5800.0]}

# ------------------------- AI REWOUND LATE ----------------------------------------------------------------------------

AI = 1


async def _ai_drive(manager: InjectingTelemetryManager, packets: Packets, lap: int, *distances: float,
                    status: LapData.DriverStatus = FLYING) -> None:
    """One LAP_DATA per distance for the AI car (car 1), in status on lap."""
    for packet in packets.drive(AI, lap=lap, distances=list(distances), session_uid=UID, status=status):
        await manager.inject(packet)


async def _ai_session(manager: InjectingTelemetryManager, packets: Packets, session: SessionType24,
                      track: TrackID) -> None:
    """The SESSION and PARTICIPANTS packets for the player and the AI car."""
    await manager.inject(packets.session(session_uid=UID, session_type=session.name, track=track, total_laps=0,
                                         track_length=LAP_TRACK_LENGTHS[track]))
    await manager.inject(packets.participants(player("Bottas"), ai("Russell"), session_uid=UID))


async def _ai_fuel(manager: InjectingTelemetryManager, packets: Packets, fuel: float) -> None:
    await manager.inject(packets.car_status(fuel_and_ers(AI, fuel_in_tank=fuel), session_uid=UID))


def _ai_recording(state: SessionState) -> Tuple[Dict[int, List[float]], Optional[Tuple[int, List[float]]]]:
    """The AI car's recorded laps (lap -> distances) and its in-progress lap."""
    export = state.m_driver_data[AI].m_tel_rec.export()
    completed = {lap.metadata.lap_number: [round(d, 1) for d in lap.telemetry["lap_distance"]]
                 for lap in export.completed_laps}
    in_progress = export.in_progress_lap
    current = (None if in_progress is None else
               (in_progress.metadata.lap_number, [round(d, 1) for d in in_progress.telemetry["lap_distance"]]))
    return completed, current


def _ai_laps(state: SessionState) -> Tuple[Dict[int, List[float]], Optional[Tuple[int, List[float]]], float]:
    """The AI car's recorded laps (lap -> distances), its in-progress lap, and lap 2's snapshot fuel in kg."""
    fuel = state.m_driver_data[AI].m_per_lap_snapshots[2].m_car_status_packet.m_fuelInTank
    return *_ai_recording(state), round(fuel, 3)


@allure.story("AI rewound late")
@pytest.mark.parametrize("session", [FP])
@title("An AI car put back a lap well after a flashback redoes that lap")
async def test_ai_lap_count_back_after_a_flashback_redoes_the_lap(manager: InjectingTelemetryManager,
                                                                  packets: Packets, state: SessionState,
                                                                  session: SessionType24, track: TrackID) -> None:
    """Practice, as in f1_26_sp_career_fp_singapore (Russell, car 2), lap 2's end shortened to fit Monaco. The AI
    completes lap 2 with 5.394 kg of fuel and is at 1767.6 m on lap 3 when the player flashes back: the landing
    leaves it on lap 3, at 1405.1 m. It drives on to 2832.9 m. Then, 1748 frames later and with no FLBK, one
    LAP_DATA puts it on lap 2 at 3051.2 m with 5.848 kg. It redoes the rest of lap 2 and crosses onto lap 3 again
    with 5.39 kg.

    Expected: the drop is handled as that car's flashback. Lap 2 is cut back at 3051.2 m and redone, then stored
    again on the second crossing, with the redone lap's 5.39 kg. Lap 3 starts over at the line."""
    await _ai_session(manager, packets, session, track)
    await _ai_drive(manager, packets, 2, 24.5, 1500.0, 3000.0, 3300.0)
    await _ai_fuel(manager, packets, 5.394)
    await _ai_drive(manager, packets, 3, 1.1, 1000.0, 1767.6)
    with allure.step("The player flashes back: the AI lands on lap 3 at 1405.1 m"):
        await flashback(manager, packets, car(AI, lap=3, lap_distance=1405.1, status=FLYING), UID)
    await _ai_drive(manager, packets, 3, 1800.0, 2832.9)
    # No 1405.1: the landing LAP_DATA is skipped, since the car status copy is from before the rewind
    assert _ai_laps(state) == ({2: [24.5, 1500.0, 3000.0, 3300.0]}, (3, [1.1, 1000.0, 1800.0, 2832.9]), 5.394)

    with allure.step("No FLBK: the AI is put back on lap 2 at 3051.2 m"):
        await _ai_drive(manager, packets, 2, 3051.2)
        await _ai_fuel(manager, packets, 5.848)
    await _ai_drive(manager, packets, 2, 3200.0)
    await _ai_fuel(manager, packets, 5.39)
    await _ai_drive(manager, packets, 3, 0.1)

    assert _ai_laps(state) == ({2: [24.5, 1500.0, 3000.0, 3051.2, 3200.0]}, (3, [0.1]), 5.39)


@allure.story("AI rewound late")
@pytest.mark.parametrize("session", [FP])
@pytest.mark.parametrize("back_to", [1, 0], ids=["three laps back", "to lap 0"])
@title("A lap count going back to lap {back_to} with no FLBK isn't a rewind, so the history stays")
async def test_lap_count_back_more_than_a_lap_keeps_the_history(manager: InjectingTelemetryManager,
                                                                packets: Packets, state: SessionState,
                                                                session: SessionType24, track: TrackID,
                                                                back_to: int) -> None:
    """Practice. An AI car completes laps 1 to 3 and is 1000 m into lap 4. Then one LAP_DATA with no FLBK puts it on
    lap 1, or on lap 0. A flashback goes back one lap at most, so neither is a rewind. Constructed, not captured: the
    capture's late drops are all one lap.

    Expected: laps 1 to 3 keep their per-lap snapshots and recorded laps. Only the lap number follows the game."""
    await _ai_session(manager, packets, session, track)
    for lap in (1, 2, 3):
        await _ai_drive(manager, packets, lap, 0.5, 1500.0, 3000.0)
    await _ai_drive(manager, packets, 4, 0.5, 1000.0)
    completed, _ = _ai_recording(state)
    assert sorted(completed) == [1, 2, 3]

    with allure.step(f"No FLBK: the AI's lap count goes to {back_to}"):
        await _ai_drive(manager, packets, back_to, 1100.0)

    driver = state.m_driver_data[AI]
    assert _ai_recording(state)[0] == completed
    assert {1, 2, 3} <= set(driver.m_per_lap_snapshots)
    assert driver.m_lap_info.m_current_lap == back_to


@allure.story("AI rewound late")
@pytest.mark.parametrize("session", [FP])
@title("An AI car put back from its out lap onto a flying lap isn't at a lap start")
async def test_ai_put_back_from_an_out_lap_is_not_a_lap_start(manager: InjectingTelemetryManager, packets: Packets,
                                                              state: SessionState, session: SessionType24,
                                                              track: TrackID) -> None:
    """Practice. An AI car drives lap 2 as a flying lap to 2000 m, then an in lap through the pit lane without
    stopping, and is 500 m into lap 3's out lap. Then one LAP_DATA with no FLBK puts it back on lap 2 at 1500 m, flying:
    the status goes from OUT_LAP to FLYING_LAP in the same packet as the late rewind. Constructed, not captured: the
    capture's late drops come from FLYING_LAP or IN_LAP.

    Expected: the rewind reopens lap 2, cut at 1500 m. The status change isn't a lap start, so the reopened lap keeps
    its samples below 1500 m."""
    await _ai_session(manager, packets, session, track)
    await _ai_drive(manager, packets, 2, 0.5, 1000.0, 2000.0)
    await _ai_drive(manager, packets, 2, 2500.0, 3300.0, status=IN_LAP)
    await _ai_drive(manager, packets, 3, 0.1, 500.0, status=OUT_LAP)

    with allure.step("No FLBK: the AI is put back on lap 2 at 1500 m, flying"):
        await _ai_drive(manager, packets, 2, 1500.0)

    assert _ai_recording(state)[1] == (2, [0.5, 1000.0, 1500.0])
