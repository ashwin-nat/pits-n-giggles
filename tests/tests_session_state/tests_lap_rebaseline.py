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

"""Per-lap re-baseline scenarios: what DataPerDriver.onLapStart moves to the line when an out lap becomes a flying
lap without a lap number change. That's the lap-0 snapshot, a fresh stint's starting wear and the per-lap stats.

Fuel, wear and ERS values are from test_data/f1_26_sp_quali_suzuka_multi_run.f1pcap: two runs, with a set change in
the garage between them.
"""

# ------------------------- IMPORTS ------------------------------------------------------------------------------------

import allure
import pytest

from lib.f1_types import SessionType24, TrackID
from lib.f1_types.packet_2_lap_data import LapData

from .harness import FP, LAP_TRACKS, QUALI, RACE, PlayerCar, title
from .packet_helpers import ALL_FORMATS, FIRST_SOFT_IDX

# ------------------------- CONSTANTS ----------------------------------------------------------------------------------

GARAGE, OUT_LAP, FLYING, IN_LAP, ON_TRACK = (LapData.DriverStatus.IN_GARAGE, LapData.DriverStatus.OUT_LAP,
                                             LapData.DriverStatus.FLYING_LAP, LapData.DriverStatus.IN_LAP,
                                             LapData.DriverStatus.ON_TRACK)
RUN_1_SET, RUN_2_SET = FIRST_SOFT_IDX, FIRST_SOFT_IDX + 1

# Known bug: the xfail flips to XPASS (and fails, being strict) once it is fixed
WEIRD_GARAGE_SET_CHANGE = ("On a weird track a pending tyre change also waits for a lap change, which a quali garage "
                           "set change only gets at the end of the next flying lap. That lap is booked to the old "
                           "stint, and the new stint starts at its end.")

pytestmark = [allure.feature("Per-lap re-baseline"),
              pytest.mark.parametrize("packet_format", ALL_FORMATS, indirect=True)]

# ------------------------- FIXTURES -----------------------------------------------------------------------------------

@pytest.fixture(params=LAP_TRACKS)
def track(request: pytest.FixtureRequest) -> TrackID:
    """Both track topologies."""
    return request.param

# ------------------------- HELPERS ------------------------------------------------------------------------------------

def fuel(player_car: PlayerCar, lap: int) -> float:
    """Fuel in the per-lap snapshot of lap, in kg to 0.001."""
    return round(player_car.driver.m_per_lap_snapshots[lap].m_car_status_packet.m_fuelInTank, 3)


async def first_run(player_car: PlayerCar, session: SessionType24) -> None:
    """Run 1 on RUN_1_SET, in a session of type session: garage, out lap, flying lap 1, then the in lap on lap 2 and
    back to the garage. Lap 1 ends at 3.359 % wear."""
    await player_car.session(session)
    await player_car.baseline(GARAGE, 188.4, fuel=7.0, wear=0.0, fitted_idx=RUN_1_SET)
    await player_car.drive(OUT_LAP, 1, -5588.3, -2900.0, -1.2)
    await player_car.car_damage(1.429)
    await player_car.drive(FLYING, 1, 0.4, 2900.0, 5800.0)
    await player_car.car_damage(3.359)
    await player_car.drive(FLYING, 2, 0.3)
    await player_car.drive(IN_LAP, 2, 5636.8)
    await player_car.drive(GARAGE, 2, 185.7)
    await player_car.tyre_sets(RUN_1_SET)

# ------------------------- LAP 1 BASELINE -----------------------------------------------------------------------------

@allure.story("Lap-0 snapshot")
@pytest.mark.parametrize("session", [FP, QUALI])
@title("Lap 1's fuel baseline is taken at the line, not in the garage")
async def test_lap_1_baseline_is_taken_at_the_line(player_car: PlayerCar, session: SessionType24) -> None:
    """Practice or quali. The lap-0 snapshot is first taken in the garage at 5.0 kg, before the fuel load shows. The out
    lap reaches the line at 5.685 kg, and lap 1 ends at 4.364 kg.

    Expected: the line retakes the lap-0 snapshot, so it holds 5.685 kg and lap 1 used 1.321 kg."""
    await player_car.session(session)
    await player_car.baseline(GARAGE, 188.4, fuel=5.0, wear=0.0, fitted_idx=RUN_1_SET)
    await player_car.car_status(fuel=7.0)
    await player_car.drive(OUT_LAP, 1, -5588.3, -2900.0, -1.2)
    assert fuel(player_car, 0) == 5.0

    await player_car.car_status(fuel=5.685)
    await player_car.drive(FLYING, 1, 0.4, 2900.0, 5800.0)
    await player_car.car_status(fuel=4.364)
    await player_car.drive(FLYING, 2, 0.3)
    assert fuel(player_car, 0) == 5.685
    assert round(fuel(player_car, 0) - fuel(player_car, 1), 3) == 1.321


@allure.story("Lap-0 snapshot")
@pytest.mark.parametrize("session", [RACE])
@title("A race's lap 1 baseline stays on the grid")
async def test_race_lap_1_baseline_stays_the_grid(player_car: PlayerCar, session: SessionType24) -> None:
    """Race. The lap-0 snapshot is taken on the grid at 10.0 kg. The car is ON_TRACK from the grid onwards, as in
    f1_26_sp_race_suzuka_flashback_over_line, and lap 1 starts past the line.

    Expected: nothing in lap 1 is a lap start, so the lap-0 snapshot keeps the grid's 10.0 kg."""
    await player_car.session(session)
    await player_car.baseline(ON_TRACK, 184.1, fuel=10.0, wear=0.0, fitted_idx=RUN_1_SET)
    await player_car.car_status(fuel=9.9)
    await player_car.drive(ON_TRACK, 1, 500.0, 2900.0, 5800.0)
    await player_car.car_status(fuel=9.11)
    await player_car.drive(ON_TRACK, 2, 1.5)

    assert fuel(player_car, 0) == 10.0
    assert fuel(player_car, 1) == 9.11

# ------------------------- TYRE STINT START ---------------------------------------------------------------------------

@allure.story("Tyre stint start")
@pytest.mark.parametrize("session", [FP, QUALI])
@title("A fresh stint's starting wear moves to the line")
async def test_fresh_stint_starting_wear_moves_to_the_line(player_car: PlayerCar, session: SessionType24) -> None:
    """Practice or quali. The stint starts in the garage at 0.0 % wear, and the out lap reaches the line at 1.429 %.

    Expected: the stint's starting point becomes 1.429 %, and keeps its lap number (0)."""
    await player_car.session(session)
    await player_car.baseline(GARAGE, 188.4, fuel=7.0, wear=0.0, fitted_idx=RUN_1_SET)
    await player_car.drive(OUT_LAP, 1, -5588.3, -2900.0, -1.2)
    await player_car.car_damage(1.429)
    await player_car.drive(FLYING, 1, 0.4)

    assert player_car.stints() == [(RUN_1_SET, [(0, 1.429)])]


@allure.story("Tyre stint start")
@pytest.mark.parametrize("session", [FP, QUALI])
@title("A run on a new set re-baselines the new stint at the line")
async def test_run_on_a_new_set_rebaselines_the_new_stint(player_car: PlayerCar, session: SessionType24,
                                                          request: pytest.FixtureRequest) -> None:
    """Practice or quali. After run 1, the set is changed in the garage on lap 2 (fresh at 0.0 %). The second run's out
    lap reaches the line at 1.648 %.

    Expected: the new stint starts at 1.648 %, keeping its lap number. Run 1's stint is untouched."""
    if player_car.track == TrackID.Monaco:
        request.applymarker(pytest.mark.xfail(strict=True, reason=WEIRD_GARAGE_SET_CHANGE))
    await first_run(player_car, session)
    await player_car.tyre_sets(RUN_2_SET)
    await player_car.car_damage(0.0)
    assert player_car.stints() == [(RUN_1_SET, [(0, 1.429), (1, 3.359)]), (RUN_2_SET, [(1, 0.0)])]

    await player_car.drive(OUT_LAP, 2, 222.0, 3000.0, 5809.7)
    await player_car.car_damage(1.648)
    await player_car.drive(FLYING, 2, 1.0)
    assert player_car.stints() == [(RUN_1_SET, [(0, 1.429), (1, 3.359)]), (RUN_2_SET, [(1, 1.648)])]


@allure.story("Tyre stint start")
@pytest.mark.parametrize("session", [FP, QUALI])
@title("A run on a used set keeps the previous lap's end as is")
async def test_run_on_a_used_set_keeps_the_previous_lap_end(player_car: PlayerCar, session: SessionType24) -> None:
    """Practice or quali. A second run on run 1's set: the stint already has a completed lap. The second out lap reaches
    the line at 5.9 %.

    Expected: the stint history is unchanged. This is the accepted limit: the in lap's and out lap's wear stays in
    the stint."""
    await first_run(player_car, session)
    await player_car.drive(OUT_LAP, 2, 222.0, 3000.0, 5809.7)
    await player_car.car_damage(5.9)
    await player_car.drive(FLYING, 2, 1.0)

    assert player_car.stints() == [(RUN_1_SET, [(0, 1.429), (1, 3.359)])]


@allure.story("Tyre stint start")
@pytest.mark.parametrize("session", [FP, QUALI])
@title("A pending tyre change skips the stint re-baseline")
async def test_pending_tyre_change_skips_the_rebaseline(player_car: PlayerCar, session: SessionType24) -> None:
    """Practice or quali. In the garage the wear reads 1.0 %, then a new set is detected but the CAR_DAMAGE that
    completes the change hasn't arrived when the out lap reaches the line.

    Expected: the old stint's starting point is not moved to 1.0 %, and no new stint has started."""
    await player_car.session(session)
    await player_car.baseline(GARAGE, 188.4, fuel=7.0, wear=0.0, fitted_idx=RUN_1_SET)
    await player_car.car_damage(1.0)
    await player_car.tyre_sets(RUN_2_SET)
    await player_car.drive(OUT_LAP, 1, -5588.3, -2900.0, -1.2)
    await player_car.drive(FLYING, 1, 0.4)

    assert player_car.driver.m_pending_tyre_change is not None
    assert player_car.stints() == [(RUN_1_SET, [(0, 0.0)])]

# ------------------------- PER-LAP STATS ------------------------------------------------------------------------------

@allure.story("Per-lap stats")
@pytest.mark.parametrize("session", [FP, QUALI])
@title("Top speed and ERS harvest restart at the line")
async def test_per_lap_stats_reset_at_the_line(player_car: PlayerCar, session: SessionType24) -> None:
    """Practice or quali. The out lap reaches 283 km/h and harvests 7.003 MJ through the MGU-K. The flying lap after the
    line tops out at 276 km/h and harvests 6.793 MJ.

    Expected: the flying lap's snapshot has its own 276 km/h and 6.793 MJ, not the out lap's."""
    await player_car.session(session)
    await player_car.baseline(GARAGE, 188.4, fuel=7.0, wear=0.0, fitted_idx=RUN_1_SET)
    await player_car.drive(OUT_LAP, 1, -5588.3, -2900.0)
    await player_car.speed(283)
    await player_car.car_status(fuel=6.0, mguk_mj=7.003)
    await player_car.drive(OUT_LAP, 1, -1.2)

    await player_car.drive(FLYING, 1, 0.4, 2900.0)
    await player_car.speed(276)
    await player_car.car_status(fuel=5.0, mguk_mj=6.793)
    await player_car.drive(FLYING, 1, 5800.0)
    await player_car.drive(FLYING, 2, 0.3)

    snapshot = player_car.driver.m_per_lap_snapshots[1]
    assert snapshot.m_top_speed_kmph == 276
    assert round(snapshot.m_ers_harv_mguk_j / 1e6, 3) == 6.793

# ------------------------- SECOND CROSSING ----------------------------------------------------------------------------

@allure.story("Second crossing")
@pytest.mark.parametrize("session", [FP, QUALI])
@title("A flashback onto the out lap makes the next crossing re-baseline again")
async def test_second_crossing_rebaselines_again(player_car: PlayerCar, session: SessionType24) -> None:
    """Practice or quali. The out lap reaches the line at 5.685 kg and 1.429 % wear, and the car is 149 m into the
    flying lap when a flashback lands back on the out lap. It reaches the line again at 5.702 kg and 1.411 %.

    Expected: the lap-0 snapshot and the stint's starting point hold the second crossing's values."""
    await player_car.session(session)
    await player_car.baseline(GARAGE, 188.4, fuel=7.0, wear=0.0, fitted_idx=RUN_1_SET)
    await player_car.drive(OUT_LAP, 1, -5588.3, -2900.0, -1.2)
    await player_car.car_status(fuel=5.685)
    await player_car.car_damage(1.429)
    await player_car.drive(FLYING, 1, 0.4, 149.0)
    assert fuel(player_car, 0) == 5.685

    await player_car.flashback(OUT_LAP, 1, -248.8)
    await player_car.drive(OUT_LAP, 1, -100.0, -1.2)
    await player_car.car_status(fuel=5.702)
    await player_car.car_damage(1.411)
    await player_car.drive(FLYING, 1, 0.4)

    assert fuel(player_car, 0) == 5.702
    assert player_car.stints() == [(RUN_1_SET, [(0, 1.411)])]
