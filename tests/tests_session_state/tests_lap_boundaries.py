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

# Fixtures that take other fixtures as arguments are how pytest works, not shadowing
# pylint: disable=redefined-outer-name

# ------------------------- IMPORTS ------------------------------------------------------------------------------------

from typing import Any, Dict, List, Optional, Tuple

import allure
import pytest

from apps.backend.state_mgmt_layer import SessionState
from apps.backend.state_mgmt_layer.data_per_driver.data_per_driver import DataPerDriver
from lib.f1_types import TrackID
from lib.f1_types.packet_2_lap_data import LapData

from .harness import InjectingTelemetryManager, track_param
from .packet_helpers import ALL_FORMATS, Packets, player

# ------------------------- CONSTANTS ----------------------------------------------------------------------------------

UID = 100
NORMAL_TRACK = TrackID.Silverstone     # finish line before the pit garage
WEIRD_TRACK = TrackID.Monaco           # pit garage before the finish line
TRACK_LENGTHS = {NORMAL_TRACK: 5891, WEIRD_TRACK: 3337}

GARAGE, OUT_LAP, FLYING, IN_LAP, ON_TRACK = (LapData.DriverStatus.IN_GARAGE, LapData.DriverStatus.OUT_LAP,
                                             LapData.DriverStatus.FLYING_LAP, LapData.DriverStatus.IN_LAP,
                                             LapData.DriverStatus.ON_TRACK)

pytestmark = [allure.feature("Lap boundaries"),
              pytest.mark.parametrize("packet_format", ALL_FORMATS, indirect=True)]

# ------------------------- FIXTURES -----------------------------------------------------------------------------------

@pytest.fixture(params=[track_param(NORMAL_TRACK, "normal"), track_param(WEIRD_TRACK, "weird")])
def track(request: pytest.FixtureRequest) -> TrackID:
    """Both track topologies."""
    return request.param


@pytest.fixture
def run(manager: InjectingTelemetryManager, packets: Packets, state: SessionState, track: TrackID) -> "Run":
    """The player's car on track. Start the session with await run.session(...)."""
    return Run(manager, packets, state, track)

# ------------------------- HELPERS ------------------------------------------------------------------------------------

class Run:
    """The player's car in one session. drive() sends one LAP_DATA per distance."""

    def __init__(self, manager: InjectingTelemetryManager, packets: Packets, state: SessionState,
                 track: TrackID) -> None:
        self.manager = manager
        self.packets = packets
        self.state = state
        self.track = track

    @property
    def driver(self) -> DataPerDriver:
        """The player's DataPerDriver."""
        return self.state.m_driver_data[0]

    async def session(self, session_type: str) -> None:
        """SESSION and PARTICIPANTS for a session_type session on this track."""
        with allure.step(f"{session_type} at {self.track.name}"):
            await self.manager.inject(self.packets.session(
                session_uid=UID, session_type=session_type, track=self.track, total_laps=5,
                track_length=TRACK_LENGTHS[self.track]))
            await self.manager.inject(self.packets.participants(player("Player"), session_uid=UID))

    async def drive(self, status: LapData.DriverStatus, lap: int, *distances: float) -> None:
        """One LAP_DATA per distance, in status on lap."""
        with allure.step(f"{status.name} lap {lap}: {', '.join(str(d) for d in distances)}"):
            for packet in self.packets.drive(0, lap=lap, distances=list(distances), session_uid=UID, status=status):
                await self.manager.inject(packet)

    def completed_laps(self) -> Dict[int, List[float]]:
        """The recorder's completed laps, as lap number -> lap distances (to 0.1 m)."""
        return {lap.metadata.lap_number: _distances(lap.telemetry)
                for lap in self.driver.m_tel_rec.export().completed_laps}

    def in_progress_lap(self) -> Optional[Tuple[int, List[float]]]:
        """The recorder's in-progress lap as (lap number, lap distances to 0.1 m), or None if it holds no
        samples."""
        lap = self.driver.m_tel_rec.export().in_progress_lap
        return None if lap is None else (lap.metadata.lap_number, _distances(lap.telemetry))


def _distances(telemetry: Dict[str, list]) -> List[float]:
    # Lap distance is a float32 on the wire: 0.6 comes back as 0.6000000238
    return [round(distance, 1) for distance in telemetry["lap_distance"]]


def title(text: str) -> Any:
    """allure.title for a test in this file: text, then the track and packet format the case ran on."""
    return allure.title(text + " ({track.name}, {packet_format})")

# ------------------------- OUT LAP TO FLYING LAP ----------------------------------------------------------------------

@allure.story("Out lap to flying lap")
@title("A first run's lap starts at the line, not the garage")
async def test_out_lap_to_flying_lap_starts_the_lap(run: Run) -> None:
    """Quali. Garage, an out lap counting up from -5581 m to the line, then a flying lap. The sim keeps lap
    number 1 throughout and only flips the status from OUT_LAP to FLYING_LAP at the line.

    Expected: when lap 2 starts, lap 1 is stored holding only the flying lap's samples, from 0.6 m. No garage or
    out lap samples."""
    await run.session("SHORT_QUALIFYING")
    await run.drive(GARAGE, 1, 228.7)                       # the frame-0 garage spot
    await run.drive(OUT_LAP, 1, -5581.1, -2900.0, -1.2)
    await run.drive(FLYING, 1, 0.6, 2900.0, 5800.0)         # same lap number: the sim only flips the status
    assert run.completed_laps() == {}

    await run.drive(FLYING, 2, 0.6)
    assert run.completed_laps() == {1: [0.6, 2900.0, 5800.0]}, "lap 1 is stored when lap 2 starts"
    assert run.in_progress_lap() == (2, [0.6])


@allure.story("Out lap to flying lap")
@title("A later run's out lap past the line doesn't eat the flying lap")
async def test_later_run_out_lap_wraps_at_the_line(run: Run) -> None:
    """Quali, a later run. The out lap on lap 2 counts up past the line (222 m to 5809.7 m), then the flying
    lap starts on the same lap number at 1.0 m.

    Expected: lap 2 holds every flying lap sample. Before the fix, each one was below the out lap's 5809.7 m
    high-water mark and got dropped."""
    await run.session("SHORT_QUALIFYING")
    await run.drive(OUT_LAP, 2, 222.0, 3000.0, 5809.7)      # a later run's out lap counts up past the line
    await run.drive(FLYING, 2, 1.0, 2900.0, 5800.0)
    await run.drive(FLYING, 3, 0.6)

    assert run.completed_laps() == {2: [1.0, 2900.0, 5800.0]}


@allure.story("Out lap to flying lap")
@title("A 'flying lap' spawn into S3 starts the lap at the line, not at the spawn")
async def test_flying_lap_spawn_waits_for_the_line(run: Run) -> None:
    """Quali. From the garage, the car is teleported on its out lap from -5581 m to -1590 m (S3), then
    crosses the line onto a flying lap.

    Expected: the jump isn't a lap start, so the out lap keeps all its samples. The lap starts at the line, and
    lap 1 holds only the flying lap."""
    await run.session("SHORT_QUALIFYING")
    await run.drive(GARAGE, 1, -5581.2)
    await run.drive(OUT_LAP, 1, -5581.1, -1590.7, -800.0, -1.2)    # spawned straight into S3
    assert run.in_progress_lap() == (1, [-5581.1, -1590.7, -800.0, -1.2]), "the spawn is not a lap start"

    await run.drive(FLYING, 1, 0.6, 2900.0, 5800.0)
    assert run.in_progress_lap() == (1, [0.6, 2900.0, 5800.0])

    await run.drive(FLYING, 2, 0.6)
    assert run.completed_laps() == {1: [0.6, 2900.0, 5800.0]}

# ------------------------- IN LAPS ------------------------------------------------------------------------------------

@allure.story("In laps")
@title("An in lap crossing the line in the pit lane is not a lap start")
async def test_in_lap_pit_lane_crossing_is_not_a_lap_start(run: Run) -> None:
    """Quali. On an in lap, the pit lane takes the car over the line: lap distance wraps from 5809.8 m to 0.1 m
    with no lap number change.

    Expected: the in-progress lap keeps its samples up to 5809.8 m. Nothing is stored as a completed lap."""
    await run.session("SHORT_QUALIFYING")
    await run.drive(IN_LAP, 2, 3000.0, 5809.8)
    await run.drive(IN_LAP, 2, 0.1)                         # the pit lane crosses the line, same lap number

    assert run.in_progress_lap() == (2, [3000.0, 5809.8])
    assert run.completed_laps() == {}


@allure.story("In laps")
@title("An in lap right after the line is not a second lap start")
async def test_in_lap_after_a_lap_change_is_not_a_lap_start(run: Run) -> None:
    """Quali. A flying lap 1 ends, lap 2 starts at 0.6 m, and the status flips to IN_LAP 3 m later.

    Expected: one lap change. Lap 1 is stored, and lap 2 keeps both its samples."""
    await run.session("SHORT_QUALIFYING")
    await run.drive(FLYING, 1, 2900.0, 5800.0)
    await run.drive(FLYING, 2, 0.6)
    await run.drive(IN_LAP, 2, 3.0)

    assert run.completed_laps() == {1: [2900.0, 5800.0]}
    assert run.in_progress_lap() == (2, [0.6, 3.0])

# ------------------------- GARAGE -------------------------------------------------------------------------------------

@allure.story("Garage")
@title("Samples in the garage are not recorded")
async def test_garage_samples_are_not_recorded(run: Run) -> None:
    """Quali. IN_GARAGE packets at the garage spot's lap distances: +228.7 m on frame 0 and -5581.2 m after.
    Then the car leaves on an out lap.

    Expected: nothing is recorded in the garage. Recording starts with the first out lap sample."""
    await run.session("SHORT_QUALIFYING")
    await run.drive(GARAGE, 1, 228.7, -5581.2)              # positive on frame 0, negative after
    assert run.in_progress_lap() is None
    assert run.completed_laps() == {}

    await run.drive(OUT_LAP, 1, -5542.9)
    assert run.in_progress_lap() == (1, [-5542.9])


@allure.story("Garage")
@title("Returning to the garage just after the line drops that lap")
async def test_garage_return_just_after_the_line_drops_the_lap(run: Run) -> None:
    """Quali. Lap 1 is done, lap 2 is 260 m in, then the car goes back to the garage. A second run follows: an
    out lap and a flying lap, both still on lap 2.

    Expected: the garage discards the first run's partial lap 2. The stored lap 2 holds only the second run's
    flying lap."""
    await run.session("SHORT_QUALIFYING")
    await run.drive(FLYING, 1, 2900.0, 5800.0)
    await run.drive(FLYING, 2, 1.0, 130.0, 260.0)
    await run.drive(GARAGE, 2, -5581.2)
    assert run.in_progress_lap() is None, "the lap 2 started before the garage is discarded"

    await run.drive(OUT_LAP, 2, 222.0, 3000.0, 5809.7)
    await run.drive(FLYING, 2, 1.0, 2900.0, 5800.0)
    await run.drive(FLYING, 3, 0.6)
    assert run.completed_laps() == {1: [2900.0, 5800.0], 2: [1.0, 2900.0, 5800.0]}

# ------------------------- RACES --------------------------------------------------------------------------------------

@allure.story("Races")
@title("A race pit stop keeps the lap whole")
async def test_race_pit_stop_is_not_a_lap_start(run: Run) -> None:
    """Race. Mid lap 3 the car pits: ON_TRACK, IN_LAP, OUT_LAP, then ON_TRACK again.

    Expected: no lap start and no discard. Lap 3 is stored with every sample when lap 4 starts."""
    await run.session("RACE")
    await run.drive(ON_TRACK, 3, 100.0, 1500.0)
    await run.drive(IN_LAP, 3, 2000.0, 2500.0)
    await run.drive(OUT_LAP, 3, 3000.0, 3500.0)
    await run.drive(ON_TRACK, 3, 4000.0, 5800.0)
    await run.drive(ON_TRACK, 4, 0.6)

    assert run.completed_laps() == {3: [100.0, 1500.0, 2000.0, 2500.0, 3000.0, 3500.0, 4000.0, 5800.0]}


@allure.story("Races")
@title("The cool-down lap and garage after the flag keep the last racing lap")
async def test_race_cool_down_lap_wrap_is_left_alone(run: Run) -> None:
    """Race. After the flag on lap 5, the cool-down lap wraps from 5809.9 m to 1.2 m with no lap change, then
    the car is put in the garage.

    Expected: neither the wrap nor the garage drops lap 5's samples. Races skip both lap boundary checks."""
    await run.session("RACE")
    await run.drive(ON_TRACK, 5, 3000.0, 5809.9)
    await run.drive(ON_TRACK, 5, 1.2, 300.0)                # after the flag: wraps without a lap change
    assert run.in_progress_lap() == (5, [3000.0, 5809.9])

    await run.drive(GARAGE, 5, 228.7)
    assert run.in_progress_lap() == (5, [3000.0, 5809.9]), "the garage doesn't discard a race lap"

# ------------------------- LAP ANALYZER SETTINGS ----------------------------------------------------------------------

@allure.story("Lap analyzer settings")
@pytest.mark.parametrize("switch,expected", [
    ("on -> off", None),
    ("off -> on", (1, [300.0, 400.0])),
    ("on -> on", (1, [100.0, 200.0, 300.0, 400.0])),
    ("off -> off", None),
], ids=["on-off", "off-on", "on-on", "off-off"])
@title("Lap analyzer switched {switch} mid-lap")
async def test_disabling_lap_analyzer_discards_the_in_progress_lap(
        run: Run, state: SessionState, switch: str, expected: Optional[Tuple[int, List[float]]]) -> None:
    """Quali. Samples at 100 m and 200 m under the first setting, then the lap analyzer is switched in the
    settings, then samples at 300 m and 400 m.

    Expected: turning it off discards the in-progress lap, so turning it back on later can't splice two
    stretches into one lap. Otherwise the lap holds the samples taken while it was on."""
    was_on, now_on = (setting == "on" for setting in switch.split(" -> "))
    lap_analyzer = state.m_lap_analyzer_settings
    await run.session("SHORT_QUALIFYING")
    state.updateLapAnalyzerSettings(lap_analyzer.model_copy(update={"enable": was_on}))
    await run.drive(FLYING, 1, 100.0, 200.0)

    with allure.step(f"lap analyzer {switch}"):
        state.updateLapAnalyzerSettings(lap_analyzer.model_copy(update={"enable": now_on}))
    await run.drive(FLYING, 1, 300.0, 400.0)

    assert run.in_progress_lap() == expected
