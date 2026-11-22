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

"""Lap boundary scenarios: which samples the lap recorder keeps, and under which lap, as the driver status and
lap number change. Recorder state is read from driver.m_tel_rec.export().

Lap distances are raw ones from F1 26 captures: negative on a first run's out lap, counting up past the line on a
later run's out lap.
"""

# ------------------------- IMPORTS ------------------------------------------------------------------------------------

import math
from typing import (Awaitable, Callable, Dict, List, NamedTuple, Optional,
                    Tuple)

import allure
import pytest

from apps.backend.state_mgmt_layer import SessionState
from lib.f1_types import SessionType24

from .harness import (ALL_SESSIONS, FLYING, FP, GARAGE, IN_LAP, ON_TRACK, OUT_LAP,
                      QUALI, RACE, TT, PlayerCar, leaving_garage_status,
                      racing_status, title)
from .packet_helpers import ALL_FORMATS, FIRST_SOFT_IDX, classified

# ------------------------- CONSTANTS ----------------------------------------------------------------------------------


pytestmark = [allure.feature("Lap boundaries"),
              pytest.mark.parametrize("packet_format", ALL_FORMATS, indirect=True)]

# ------------------------- OUT LAP TO FLYING LAP ----------------------------------------------------------------------

@allure.story("Out lap to flying lap")
@pytest.mark.parametrize("session", [FP, QUALI])
@title("A first run's lap starts at the line, not the garage")
async def test_out_lap_to_flying_lap_starts_the_lap(player_car: PlayerCar, session: SessionType24) -> None:
    """Practice or quali. Garage, an out lap counting up from -5581 m to the line, then a flying lap. The sim keeps lap
    number 1 throughout and only flips the status from OUT_LAP to FLYING_LAP at the line.

    Expected: when lap 2 starts, lap 1 is stored holding only the flying lap's samples, from 0.6 m. No garage or out
    lap samples."""
    await player_car.session(session)
    await player_car.drive(GARAGE, 1, 228.7)                       # the frame-0 garage spot
    await player_car.drive(OUT_LAP, 1, -5581.1, -2900.0, -1.2)
    await player_car.drive(FLYING, 1, 0.6, 2900.0, 5800.0)         # same lap number: the sim only flips the status
    assert player_car.completed_laps() == {}

    await player_car.drive(FLYING, 2, 0.6)
    assert player_car.completed_laps() == {1: [0.6, 2900.0, 5800.0]}, "lap 1 is stored when lap 2 starts"
    assert player_car.in_progress_lap() == (2, [0.6])


@allure.story("Out lap to flying lap")
@pytest.mark.parametrize("session", [FP, QUALI])
@title("A later run's out lap past the line doesn't eat the flying lap")
async def test_later_run_out_lap_wraps_at_the_line(player_car: PlayerCar, session: SessionType24) -> None:
    """Practice or quali, a later run. The out lap on lap 2 counts up past the line (222 m to 5809.7 m), then the flying
    lap starts on the same lap number at 1.0 m.

    Expected: lap 2 holds every flying lap sample. Before the fix, each one was below the out lap's 5809.7 m high-
    water mark and got dropped."""
    await player_car.session(session)
    await player_car.drive(OUT_LAP, 2, 222.0, 3000.0, 5809.7)      # a later run's out lap counts up past the line
    await player_car.drive(FLYING, 2, 1.0, 2900.0, 5800.0)
    await player_car.drive(FLYING, 3, 0.6)

    assert player_car.completed_laps() == {2: [1.0, 2900.0, 5800.0]}


@allure.story("Out lap to flying lap")
@pytest.mark.parametrize("session", [FP, QUALI])
@title("A 'flying lap' spawn into S3 starts the lap at the line, not at the spawn")
async def test_flying_lap_spawn_waits_for_the_line(player_car: PlayerCar, session: SessionType24) -> None:
    """Practice or quali. From the garage, the car is teleported on its out lap from -5581 m to -1590 m (S3), then
    crosses the line onto a flying lap.

    Expected: the jump isn't a lap start, so the out lap keeps all its samples. The lap starts at the line, and lap 1
    holds only the flying lap."""
    await player_car.session(session)
    await player_car.drive(GARAGE, 1, -5581.2)
    await player_car.drive(OUT_LAP, 1, -5581.1, -1590.7, -800.0, -1.2)    # spawned straight into S3
    assert player_car.in_progress_lap() == (1, [-5581.1, -1590.7, -800.0, -1.2]), "the spawn is not a lap start"

    await player_car.drive(FLYING, 1, 0.6, 2900.0, 5800.0)
    assert player_car.in_progress_lap() == (1, [0.6, 2900.0, 5800.0])

    await player_car.drive(FLYING, 2, 0.6)
    assert player_car.completed_laps() == {1: [0.6, 2900.0, 5800.0]}

# ------------------------- IN LAPS ------------------------------------------------------------------------------------

@allure.story("In laps")
@pytest.mark.parametrize("session", [FP, QUALI])
@title("An in lap crossing the line in the pit lane is not a lap start")
async def test_in_lap_pit_lane_crossing_is_not_a_lap_start(player_car: PlayerCar, session: SessionType24) -> None:
    """Practice or quali. On an in lap, the pit lane takes the car over the line: lap distance wraps from 5809.8 m to
    0.1 m with no lap number change.

    Expected: the in-progress lap keeps its samples up to 5809.8 m. Nothing is stored as a completed lap."""
    await player_car.session(session)
    await player_car.drive(IN_LAP, 2, 3000.0, 5809.8)
    await player_car.drive(IN_LAP, 2, 0.1)                         # the pit lane crosses the line, same lap number

    assert player_car.in_progress_lap() == (2, [3000.0, 5809.8])
    assert player_car.completed_laps() == {}


@allure.story("In laps")
@pytest.mark.parametrize("session", [FP, QUALI])
@title("An in lap right after the line is not a second lap start")
async def test_in_lap_after_a_lap_change_is_not_a_lap_start(player_car: PlayerCar, session: SessionType24) -> None:
    """Practice or quali. A flying lap 1 ends, lap 2 starts at 0.6 m, and the status flips to IN_LAP 3 m later.

    Expected: one lap change. Lap 1 is stored, and lap 2 keeps both its samples."""
    await player_car.session(session)
    await player_car.drive(FLYING, 1, 2900.0, 5800.0)
    await player_car.drive(FLYING, 2, 0.6)
    await player_car.drive(IN_LAP, 2, 3.0)

    assert player_car.completed_laps() == {1: [2900.0, 5800.0]}
    assert player_car.in_progress_lap() == (2, [0.6, 3.0])

# ------------------------- GARAGE -------------------------------------------------------------------------------------

@allure.story("Garage")
@pytest.mark.parametrize("session", [FP, QUALI, TT])
@title("Samples in the garage are not recorded")
async def test_garage_samples_are_not_recorded(player_car: PlayerCar, session: SessionType24) -> None:
    """Practice, quali or time trial. IN_GARAGE packets at the garage spot's lap distances: +228.7 m on frame 0 and
    -5581.2 m after. Then the car leaves: on an out lap, or in time trial straight onto a flying lap.

    Expected: nothing is recorded in the garage. Recording starts with the first out lap sample."""
    await player_car.session(session)
    await player_car.drive(GARAGE, 1, 228.7, -5581.2)              # positive on frame 0, negative after
    assert player_car.in_progress_lap() is None
    assert player_car.completed_laps() == {}

    await player_car.drive(leaving_garage_status(session), 1, -5542.9)
    assert player_car.in_progress_lap() == (1, [-5542.9])


@allure.story("Garage")
@pytest.mark.parametrize("session", [FP, QUALI])
@title("Returning to the garage just after the line drops that lap")
async def test_garage_return_just_after_the_line_drops_the_lap(player_car: PlayerCar, session: SessionType24) -> None:
    """Practice or quali (f1_26_sp_career_fp_singapore does this on lap 4). Lap 1 is done, lap 2 is 260 m in, then the
    car goes back to the garage. A second run follows: an out lap and a flying lap, both still on lap 2.

    Expected: the garage discards the first run's partial lap 2. The stored lap 2 holds only the second run's flying
    lap."""
    await player_car.session(session)
    await player_car.drive(FLYING, 1, 2900.0, 5800.0)
    await player_car.drive(FLYING, 2, 1.0, 130.0, 260.0)
    await player_car.drive(GARAGE, 2, -5581.2)
    assert player_car.in_progress_lap() is None, "the lap 2 started before the garage is discarded"

    await player_car.drive(OUT_LAP, 2, 222.0, 3000.0, 5809.7)
    await player_car.drive(FLYING, 2, 1.0, 2900.0, 5800.0)
    await player_car.drive(FLYING, 3, 0.6)
    assert player_car.completed_laps() == {1: [2900.0, 5800.0], 2: [1.0, 2900.0, 5800.0]}

# ------------------------- SESSION FAST-FORWARD -----------------------------------------------------------------------

# Found in FP recordings; no quali recording shows a fast-forward. QUALI is here for completeness.

@allure.story("Session fast-forward")
@pytest.mark.parametrize("session", [FP, QUALI])
@title("Laps skipped by a session fast-forward are not booked")
async def test_session_fast_forward_books_no_skipped_laps(player_car: PlayerCar, session: SessionType24) -> None:
    """Practice or quali, as in f1_26_mp_fp_baku_short (car 3, overall frame 64842) and f1_26_sp_career_fp_singapore (car 0,
    overall frame 51396). Flying lap 1 ends at 5.401 % wear, then the in lap on lap 2 and back to the garage at
    8.039 %. The session is then fast-forwarded to its end: one LAP_DATA puts the car, still IN_GARAGE, on lap 7, the
    next frame's CAR_DAMAGE reads 0.0 % on all four, and FINAL_CLASSIFICATION gives it 6 laps.

    Expected: nothing is booked for laps 3 to 6, which the car never drove: no per-lap snapshot, stint entry or
    recorded lap. Wear never goes down within the stint."""
    await player_car.session(session)
    await player_car.baseline(GARAGE, 188.4, fuel=7.0, wear=0.0, fitted_idx=FIRST_SOFT_IDX)
    await player_car.drive(OUT_LAP, 1, -5588.3, -2900.0, -1.2)
    await player_car.car_damage(1.971)
    await player_car.drive(FLYING, 1, 0.4, 2900.0, 5800.0)
    await player_car.car_damage(5.401)
    await player_car.drive(IN_LAP, 2, 8.5, 2900.0)
    await player_car.car_damage(8.039)
    await player_car.drive(GARAGE, 2, 61.6, 58.5)
    with allure.step("Fast-forward: lap 7 in the garage, then 0.0 % wear, then 6 laps classified"):
        await player_car.drive(GARAGE, 7, 58.5)
        await player_car.car_damage(0.0)
        await player_car.manager.inject(player_car.packets.final_classification(
            classified(position=1, num_laps=6), session_uid=player_car.session_uid))

    driven = {0, 1, 2}
    assert set(player_car.driver.m_per_lap_snapshots) <= driven
    assert set(player_car.completed_laps()) <= driven
    for _, samples in player_car.stints():
        assert {lap for lap, _ in samples} <= driven
        assert [wear for _, wear in samples] == sorted(wear for _, wear in samples), "wear went down in a stint"


@allure.story("Session fast-forward")
@pytest.mark.parametrize("session", [FP, QUALI])
@title("A car on track at a session fast-forward gets no lap it never drove")
async def test_session_fast_forward_on_track_books_no_skipped_laps(player_car: PlayerCar,
                                                                   session: SessionType24) -> None:
    """Practice or quali, as in f1_26_mp_fp_baku_short (car 18, overall frame 64842). Flying laps 1 to 3, then lap 4 is
    3253 m in when the session is fast-forwarded to its end: one LAP_DATA puts the car, still FLYING_LAP, on lap 10
    at 3254 m, one more follows at 3255 m, and FINAL_CLASSIFICATION gives it 9 laps.

    Expected: nothing is booked for laps 5 to 9, which the car never drove: no per-lap snapshot or recorded lap."""
    await player_car.session(session)
    await player_car.drive(OUT_LAP, 1, -5588.3, -2900.0, -1.2)
    for lap in (1, 2, 3):
        await player_car.drive(FLYING, lap, 0.4, 2900.0, 5800.0)
    await player_car.drive(FLYING, 4, 0.4, 1500.0, 3253.0)
    with allure.step("Fast-forward: lap 10 at 3254 m, then 9 laps classified"):
        await player_car.drive(FLYING, 10, 3254.0, 3255.0)
        await player_car.manager.inject(player_car.packets.final_classification(
            classified(position=1, num_laps=9), session_uid=player_car.session_uid))

    driven = {0, 1, 2, 3, 4}
    assert set(player_car.driver.m_per_lap_snapshots) <= driven
    assert set(player_car.completed_laps()) <= driven

# ------------------------- RACES --------------------------------------------------------------------------------------

@allure.story("Races")
@pytest.mark.parametrize("session", [RACE])
@title("A race pit stop keeps the lap whole")
async def test_race_pit_stop_is_not_a_lap_start(player_car: PlayerCar, session: SessionType24) -> None:
    """Race. Mid lap 3 the car pits: ON_TRACK, IN_LAP, OUT_LAP, then ON_TRACK again.

    Expected: no lap start and no discard. Lap 3 is stored with every sample when lap 4 starts."""
    await player_car.session(session)
    await player_car.drive(ON_TRACK, 3, 100.0, 1500.0)
    await player_car.drive(IN_LAP, 3, 2000.0, 2500.0)
    await player_car.drive(OUT_LAP, 3, 3000.0, 3500.0)
    await player_car.drive(ON_TRACK, 3, 4000.0, 5800.0)
    await player_car.drive(ON_TRACK, 4, 0.6)

    assert player_car.completed_laps() == {3: [100.0, 1500.0, 2000.0, 2500.0, 3000.0, 3500.0, 4000.0, 5800.0]}


@allure.story("Races")
@pytest.mark.parametrize("session", [RACE])
@title("The cool-down lap and garage after the flag keep the last racing lap")
async def test_race_cool_down_lap_wrap_is_left_alone(player_car: PlayerCar, session: SessionType24) -> None:
    """Race. After the flag on lap 5, the cool-down lap wraps from 5809.9 m to 1.2 m with no lap change, then the car is
    put in the garage.

    Expected: neither the wrap nor the garage drops lap 5's samples. Races skip both lap boundary checks."""
    await player_car.session(session)
    await player_car.drive(ON_TRACK, 5, 3000.0, 5809.9)
    await player_car.drive(ON_TRACK, 5, 1.2, 300.0)                # after the flag: wraps without a lap change
    assert player_car.in_progress_lap() == (5, [3000.0, 5809.9])

    await player_car.drive(GARAGE, 5, 228.7)
    assert player_car.in_progress_lap() == (5, [3000.0, 5809.9]), "the garage doesn't discard a race lap"

# ------------------------- LAP ANALYZER SETTINGS ----------------------------------------------------------------------

@allure.story("Lap analyzer settings")
@pytest.mark.parametrize("session", ALL_SESSIONS)
@pytest.mark.parametrize("switch,expected", [
    ("on -> off", None),
    ("off -> on", (1, [300.0, 400.0])),
    ("on -> on", (1, [100.0, 200.0, 300.0, 400.0])),
    ("off -> off", None),
], ids=["on-off", "off-on", "on-on", "off-off"])
@title("Lap analyzer switched {switch} mid-lap")
async def test_disabling_lap_analyzer_discards_the_in_progress_lap(
        player_car: PlayerCar, session: SessionType24, state: SessionState, switch: str,
        expected: Optional[Tuple[int, List[float]]]) -> None:
    """Any session type. Samples at 100 m and 200 m under the first setting, then the lap analyzer is switched in the
    settings, then samples at 300 m and 400 m.

    Expected: turning it off discards the in-progress lap, so turning it back on later can't splice two stretches
    into one lap. Otherwise the lap holds the samples taken while it was on."""
    was_on, now_on = (setting == "on" for setting in switch.split(" -> "))
    lap_analyzer = state.m_lap_analyzer_settings
    await player_car.session(session)
    state.updateLapAnalyzerSettings(lap_analyzer.model_copy(update={"enable": was_on}))
    await player_car.drive(racing_status(session), 1, 100.0, 200.0)

    with allure.step(f"lap analyzer {switch}"):
        state.updateLapAnalyzerSettings(lap_analyzer.model_copy(update={"enable": now_on}))
    await player_car.drive(racing_status(session), 1, 300.0, 400.0)

    assert player_car.in_progress_lap() == expected

# ------------------------- SENSOR VALUES ------------------------------------------------------------------------------

class SensorSource(NamedTuple):
    """The packet that feeds a recorded sensor, and the value it records from it."""
    send_packet: Callable[[PlayerCar], Awaitable[None]]
    value: float


# Looked up by recorded key, one sensor per source: a lambda param would show in Allure with a changing address
SENSOR_SOURCES: Dict[str, SensorSource] = {
    "speed": SensorSource(lambda car: car.speed(283), 283),                                # CAR_TELEMETRY copy
    "tyre_wear.fl": SensorSource(lambda car: car.car_damage(12.5), 12.5),                  # CAR_DAMAGE, tyre info
    "ers.store_energy": SensorSource(lambda car: car.car_status(fuel=10.0, ers_store_mj=2.0), 50.0),  # % of 4 MJ
    # MOTION copies: four fields of one packet, each a distinct value so a swapped field fails
    "motion.position.x": SensorSource(lambda car: car.position(10.5, 2.25, -30.75, 0.5), 10.5),
    "motion.position.y": SensorSource(lambda car: car.position(10.5, 2.25, -30.75, 0.5), 2.25),
    "motion.position.z": SensorSource(lambda car: car.position(10.5, 2.25, -30.75, 0.5), -30.75),
    "motion.yaw": SensorSource(lambda car: car.position(10.5, 2.25, -30.75, 0.5), 0.5),
}


@allure.story("Sensor values")
@pytest.mark.parametrize("sensor", list(SENSOR_SOURCES))
@pytest.mark.parametrize("session", ALL_SESSIONS)
@title("The {sensor} sensor records nothing before its packet, then the packet's value")
async def test_sensor_has_no_value_before_its_packet(player_car: PlayerCar, session: SessionType24,
                                                     sensor: str) -> None:
    """Any session type, every sensor on. A sample at 100 m before the sensor's packet has arrived, then the packet
    (speed 283 km/h, front left wear 12.5 %, ERS store 2 MJ, or world x, y, z 10.5, 2.25,
    -30.75 m and yaw 0.5 rad), then a sample at 200 m.

    Expected: the first sample holds NaN, the recorder's value for a missing reading, not 0. The second holds the
    packet's value."""
    send_packet, value = SENSOR_SOURCES[sensor]
    await player_car.session(session)
    await player_car.drive(racing_status(session), 1, 100.0)
    await send_packet(player_car)
    await player_car.drive(racing_status(session), 1, 200.0)

    before, after = player_car.driver.m_tel_rec.export().in_progress_lap.telemetry[sensor]
    assert math.isnan(before)
    assert after == value

