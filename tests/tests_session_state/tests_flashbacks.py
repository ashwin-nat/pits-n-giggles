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

# Fixtures that take other fixtures as arguments are how pytest works, not shadowing
# pylint: disable=redefined-outer-name

# ------------------------- IMPORTS ------------------------------------------------------------------------------------

import allure
import pytest

from lib.f1_types import TrackID
from lib.f1_types.packet_2_lap_data import LapData

from .harness import LAP_TRACKS, Run, title
from .packet_helpers import ALL_FORMATS

# ------------------------- CONSTANTS ----------------------------------------------------------------------------------

GARAGE, OUT_LAP, FLYING, IN_LAP, ON_TRACK = (LapData.DriverStatus.IN_GARAGE, LapData.DriverStatus.OUT_LAP,
                                             LapData.DriverStatus.FLYING_LAP, LapData.DriverStatus.IN_LAP,
                                             LapData.DriverStatus.ON_TRACK)

pytestmark = [allure.feature("Flashbacks"),
              pytest.mark.parametrize("packet_format", ALL_FORMATS, indirect=True)]

# ------------------------- FIXTURES -----------------------------------------------------------------------------------

@pytest.fixture(params=LAP_TRACKS)
def track(request: pytest.FixtureRequest) -> TrackID:
    """Both track topologies."""
    return request.param

# ------------------------- WITHIN A LAP -------------------------------------------------------------------------------

@allure.story("Within a lap")
@title("A flashback within a lap cuts the recording at the landing point")
async def test_flashback_within_a_lap_truncates_at_the_landing_point(run: Run) -> None:
    """Quali. Lap 1 is recorded up to 4511 m, then a flashback lands at 4154.3 m on the same lap, on an earlier
    frame. The sim resumes about 154 m past its own target, so the landing is past samples it rewound over.

    Expected: the recorder and the delta manager keep the samples below 4154.3 m, plus the landing sample. The
    lap carries on from there with no hole before the landing point."""
    await run.session("SHORT_QUALIFYING")
    await run.drive(FLYING, 1, 0.6, 1500.0, 3000.0, 4000.0, 4300.0, 4511.0)
    await run.flashback(FLYING, 1, 4154.3)
    assert run.in_progress_lap() == (1, [0.6, 1500.0, 3000.0, 4000.0, 4154.3])
    assert run.delta_laps() == {1: [0.6, 1500.0, 3000.0, 4000.0, 4154.3]}

    await run.drive(FLYING, 1, 4300.0, 5800.0)
    await run.drive(FLYING, 2, 0.6)
    assert run.completed_laps() == {1: [0.6, 1500.0, 3000.0, 4000.0, 4154.3, 4300.0, 5800.0]}


@allure.story("Within a lap")
@title("A time trial flashback rolls back the recording and leaves the delta alone")
async def test_time_trial_flashback_skips_the_delta(run: Run) -> None:
    """Time trial. Lap 1 is recorded up to 4511 m, then a flashback lands at 4154.3 m on the same lap.

    Expected: the recorder rolls back to the landing point. The delta manager isn't used in time trial, and the
    flashback doesn't start using it."""
    await run.session("TIME_TRIAL")
    await run.drive(FLYING, 1, 0.6, 1500.0, 3000.0, 4000.0, 4300.0, 4511.0)
    await run.flashback(FLYING, 1, 4154.3)

    assert run.in_progress_lap() == (1, [0.6, 1500.0, 3000.0, 4000.0, 4154.3])
    assert run.delta_laps() == {}

# ------------------------- OVER THE LINE ------------------------------------------------------------------------------

@allure.story("Over the line")
@title("A race flashback over the line redoes the previous lap")
async def test_race_flashback_over_the_line_redoes_the_lap(run: Run) -> None:
    """Race. Laps 1 and 2 are done and the car is a few seconds into lap 3, then a flashback lands back on lap 2
    at 5750 m. The car crosses the line again, and drives lap 3 to the end.

    Expected: the landing drops lap 2's per-lap snapshot and the delta manager's lap 3. The recorder reopens
    lap 2, cut at the landing point. Crossing the line again stores lap 2 properly (it used to go missing, with
    lap 3 holding lap 2's trace) and takes a new lap 2 snapshot. Lap 3 is then complete."""
    await run.session("RACE")
    await run.drive(ON_TRACK, 1, 0.6, 2900.0, 5800.0)
    await run.drive(ON_TRACK, 2, 0.6, 2900.0, 5700.0, 5800.0)
    await run.drive(ON_TRACK, 3, 0.6, 100.0, 300.0)
    first_lap_2_snapshot = run.driver.m_per_lap_snapshots[2]

    await run.flashback(ON_TRACK, 2, 5750.0)
    assert 2 not in run.driver.m_per_lap_snapshots and 1 in run.driver.m_per_lap_snapshots
    assert run.delta_laps() == {1: [0.6, 2900.0, 5800.0], 2: [0.6, 2900.0, 5700.0, 5750.0]}
    assert run.completed_laps() == {1: [0.6, 2900.0, 5800.0]}
    assert run.in_progress_lap() == (2, [0.6, 2900.0, 5700.0, 5750.0])

    await run.drive(ON_TRACK, 2, 5800.0)
    await run.drive(ON_TRACK, 3, 0.6, 2900.0, 5800.0)
    await run.drive(ON_TRACK, 4, 0.6)
    assert run.completed_laps() == {1: [0.6, 2900.0, 5800.0],
                                    2: [0.6, 2900.0, 5700.0, 5750.0, 5800.0],
                                    3: [0.6, 2900.0, 5800.0]}
    assert run.driver.m_per_lap_snapshots[2] is not first_lap_2_snapshot
    assert 3 in run.driver.m_per_lap_snapshots

# ------------------------- ONTO THE OUT LAP ---------------------------------------------------------------------------

@allure.story("Onto the out lap")
@title("A flashback onto the out lap makes the next crossing start the lap again")
async def test_quali_flashback_onto_the_out_lap_restarts_the_line(run: Run) -> None:
    """Quali. Out lap, the line, 149 m into the flying lap, then a flashback lands back on the out lap at
    -248.8 m. The car crosses the line again.

    Expected: the landing empties the in-progress lap down to the landing sample. The second crossing starts
    the lap again, so lap 1 holds only the flying lap, not the out lap samples after the landing. Snapshot
    re-baselining at that crossing is test_second_crossing_rebaselines_again (13.5)."""
    await run.session("SHORT_QUALIFYING")
    await run.drive(GARAGE, 1, -5581.2)
    await run.drive(OUT_LAP, 1, -5581.1, -1000.0, -1.2)
    await run.drive(FLYING, 1, 0.6, 149.0)
    assert run.in_progress_lap() == (1, [0.6, 149.0])

    await run.flashback(OUT_LAP, 1, -248.8)
    assert run.in_progress_lap() == (1, [-248.8])

    await run.drive(OUT_LAP, 1, -100.0, -1.2)
    await run.drive(FLYING, 1, 0.6, 2900.0, 5800.0)
    await run.drive(FLYING, 2, 0.6)
    assert run.completed_laps() == {1: [0.6, 2900.0, 5800.0]}

@allure.story("Onto the out lap")
@title("A flashback from an out lap back onto a flying lap is not a lap start")
async def test_landing_on_a_flying_lap_from_an_out_lap_is_not_a_lap_start(run: Run) -> None:
    """Practice. Lap 2 is a flying lap, then an in lap through the pit lane without stopping, and an out lap on
    lap 3. A flashback from the out lap lands back on lap 2's flying lap at 3500 m. Constructed, not captured.

    Expected: the landing changes the status from OUT_LAP to FLYING_LAP but isn't a lap start, so the reopened
    lap 2 keeps its samples below 3500 m."""
    await run.session("PRACTICE_1")
    await run.drive(FLYING, 1, 2900.0, 5800.0)
    await run.drive(FLYING, 2, 0.6, 2900.0, 4000.0)
    await run.drive(IN_LAP, 2, 4500.0, 5809.8)
    await run.drive(OUT_LAP, 3, 0.1, 500.0)

    await run.flashback(FLYING, 2, 3500.0)
    assert run.in_progress_lap() == (2, [0.6, 2900.0, 3500.0])

    await run.drive(FLYING, 2, 5800.0)
    await run.drive(FLYING, 3, 0.6)
    assert run.completed_laps() == {1: [2900.0, 5800.0], 2: [0.6, 2900.0, 3500.0, 5800.0]}

# ------------------------- WITHOUT A FLASHBACK ------------------------------------------------------------------------

@allure.story("Lap count going back")
@title("The lap count going back without a flashback only changes the lap number")
async def test_lap_count_back_without_flashback_only_updates_the_lap(run: Run) -> None:
    """Practice. Laps 1 and 2 are done and the car is on lap 3, then LAP_DATA reports lap 1 with no FLBK before
    it: a new practice programme.

    Expected: the current lap becomes 1. The per-lap snapshots and the recorder's completed laps are untouched:
    nothing is dropped as if it were a flashback, and lap 3 isn't stored as if it had ended."""
    await run.session("PRACTICE_1")
    await run.drive(FLYING, 1, 2900.0, 5800.0)
    await run.drive(FLYING, 2, 0.6, 2900.0, 5800.0)
    await run.drive(FLYING, 3, 0.6, 1000.0)
    snapshots_before = dict(run.driver.m_per_lap_snapshots)

    await run.drive(FLYING, 1, 100.0)
    assert run.driver.m_lap_info.m_current_lap == 1
    assert run.driver.m_per_lap_snapshots.keys() == snapshots_before.keys()
    assert all(run.driver.m_per_lap_snapshots[lap] is snapshot for lap, snapshot in snapshots_before.items())
    assert run.completed_laps() == {1: [2900.0, 5800.0], 2: [0.6, 2900.0, 5800.0]}
