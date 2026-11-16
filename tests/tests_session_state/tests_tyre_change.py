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

"""Ordering scenarios for the delayed tyre set change (PendingTyreChange).

A tyre set change is driven by three packets that can interleave in any order: TYRE_SETS reporting the new
set (T, detection), CAR_DAMAGE (D) and a LAP_DATA lap change (L). On a normal track (finish line before the
pit garage) only D is awaited. On a weird one (pit garage before the finish line) L is awaited as well, and
the old stint's final wear is rewritten on completion. Weird-track handling applies to race stops only.

Every scenario starts from the `race` fixture or one of its variants: the player in a race on lap 10, on a soft
set at 40 % wear, with one wear sample per completed lap at 4 % a lap. A new set is a medium fitted at 2.0 %, and
a third one a hard. Tracks are Silverstone (normal), Monaco (weird) and an ID TrackID doesn't declare (unknown).

The last section covers what a flashback over the line does to the tyre set history.
"""

# Fixtures that take other fixtures as arguments are how pytest works, not shadowing
# pylint: disable=redefined-outer-name

# ------------------------- IMPORTS ------------------------------------------------------------------------------------

from typing import List, Optional, Tuple

import allure
import pytest

from apps.backend.state_mgmt_layer import SessionState
from apps.backend.state_mgmt_layer.data_per_driver import TyreSetHistoryEntry
from apps.backend.state_mgmt_layer.data_per_driver.data_per_driver import DataPerDriver
from lib.f1_types import PacketEventData, TelemetrySetting, TrackID

from .harness import InjectingTelemetryManager, track_param
from .packet_helpers import (FIRST_HARD_IDX, FIRST_MEDIUM_IDX, FIRST_SOFT_IDX,
                             Packets, car, damage, player)

# ------------------------- CONSTANTS ----------------------------------------------------------------------------------

UID = 100
NORMAL_TRACK = TrackID.Silverstone     # finish line before the pit garage
WEIRD_TRACK = TrackID.Monaco           # pit garage before the finish line
UNKNOWN_TRACK = TrackID(99)            # an ID TrackID doesn't declare - must take the normal-track path
TRACK_LENGTHS = {NORMAL_TRACK: 5891, WEIRD_TRACK: 3337, UNKNOWN_TRACK: 5000}
# Stated per track rather than asked of F1Utils, so the scenarios don't share production's answer
IS_WEIRD = {NORMAL_TRACK: False, WEIRD_TRACK: True, UNKNOWN_TRACK: False}

OLD_SET_IDX, NEW_SET_IDX, THIRD_SET_IDX = FIRST_SOFT_IDX, FIRST_MEDIUM_IDX, FIRST_HARD_IDX
START_LAP = 10
WEAR_PER_LAP = 4.0
OLD_TYRE_WEAR = 40.0    # the old set at lap 10, end of its stint
NEW_TYRE_WEAR = 2.0     # fresh set just fitted

pytestmark = allure.feature("Tyre change")

# ------------------------- FIXTURES -----------------------------------------------------------------------------------

NORMAL = track_param(NORMAL_TRACK, "normal")
WEIRD = track_param(WEIRD_TRACK, "weird")
UNKNOWN = track_param(UNKNOWN_TRACK, "unknown")


@pytest.fixture(params=[NORMAL, WEIRD, UNKNOWN])
def track(request: pytest.FixtureRequest) -> TrackID:
    """Both track topologies, plus an unrecognised track."""
    return request.param

# ------------------------- HELPERS ------------------------------------------------------------------------------------

class Race:
    """One player car in a race on track. Sends the packets each tyre change signal arrives as."""

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

    async def session(self) -> None:
        """A SESSION packet for this race."""
        await self.manager.inject(self.packets.session(
            session_uid=UID, session_type="RACE", track=self.track, total_laps=50,
            track_length=TRACK_LENGTHS[self.track]))

    async def tyre_sets(self, fitted_idx: int = NEW_SET_IDX) -> None:
        """(T) TYRE_SETS reporting fitted_idx. A new index is detection."""
        with allure.step(f"(T) tyre sets: set {fitted_idx} fitted"):
            await self.manager.inject(self.packets.tyre_sets(car_idx=0, fitted_idx=fitted_idx, session_uid=UID))

    async def car_damage(self, wear: float = NEW_TYRE_WEAR) -> None:
        """(D) CAR_DAMAGE with all four tyres at wear."""
        with allure.step(f"(D) car damage: tyre wear {wear}%"):
            await self.manager.inject(self.packets.car_damage(damage(0, tyre_wear=wear), session_uid=UID))

    async def lap(self, lap: int) -> None:
        """LAP_DATA putting the player on lap."""
        await self.manager.inject(self.packets.lap(car(0, lap=lap, lap_distance=100.0), session_uid=UID))

    async def lap_change(self) -> None:
        """(L) The player crosses the line."""
        next_lap = self.driver.m_lap_info.m_current_lap + 1
        with allure.step(f"(L) lap change: onto lap {next_lap}"):
            await self.lap(next_lap)

    async def all_signals(self) -> None:
        """Every signal this track's topology waits on, after detection."""
        await self.car_damage()
        if IS_WEIRD[self.track]:
            await self.lap_change()

    async def on_old_set(self, telemetry: TelemetrySetting = TelemetrySetting.PUBLIC) -> None:
        """Lap START_LAP on the old set, with its stint in history. Wear reaches OLD_TYRE_WEAR on that lap.
        With RESTRICTED telemetry the same packets arrive, but no tyre history is kept."""
        with allure.step(f"{self.track.name}: lap {START_LAP} on set {OLD_SET_IDX}, {telemetry.name} telemetry"):
            await self._drive_old_set(telemetry)

        assert self.driver.m_lap_info.m_current_lap == START_LAP
        if not telemetry:
            assert self.stint_count() == 0
            return
        assert self.driver.m_current_set_last_seen_lap == START_LAP
        assert self.stint_count() == 1
        assert self.latest_stint().m_fitted_index == OLD_SET_IDX
        assert self.wear_history() == [(lap, WEAR_PER_LAP * lap) for lap in range(START_LAP)]

    async def _drive_old_set(self, telemetry: TelemetrySetting) -> None:
        """The packets on_old_set sends."""
        await self.session()
        await self.manager.inject(self.packets.participants(player("Player", telemetry), session_uid=UID))
        await self.lap(1)

        # Every packet copy the lap-0 snapshot needs. The second SESSION sets the max safety car status, which
        # only happens for a driver that already has a position and a name
        await self.manager.inject(self.packets.car_telemetry(session_uid=UID))
        await self.manager.inject(self.packets.car_status(session_uid=UID))
        if self.packets.packet_format >= 2026:
            await self.manager.inject(self.packets.car_telemetry_2(session_uid=UID))
        await self.car_damage(wear=0.0)
        await self.tyre_sets(OLD_SET_IDX)
        await self.session()
        await self.lap(1)                   # lap-0 snapshot
        await self.tyre_sets(OLD_SET_IDX)   # the old set's stint starts

        for lap in range(2, START_LAP + 1):
            await self.car_damage(wear=WEAR_PER_LAP * (lap - 1))
            await self.lap(lap)
            await self.tyre_sets(OLD_SET_IDX)
        await self.car_damage(wear=OLD_TYRE_WEAR)
        await self.tyre_sets(OLD_SET_IDX)

    async def flashback(self, land_lap: int, wear: float) -> None:
        """A FLBK event, then the landing LAP_DATA on land_lap and the rewound CAR_DAMAGE at wear."""
        with allure.step(f"Flashback to lap {land_lap}, tyre wear {wear}%"):
            await self.manager.inject(self.packets.event(
                PacketEventData.EventPacketType.FLASHBACK, PacketEventData.Flashback.from_values(frame_identifier=1),
                session_uid=UID))
            await self.lap(land_lap)
            await self.car_damage(wear=wear)

    async def change_tyres(self, fitted_idx: int) -> int:
        """A completed tyre change to fitted_idx, with every signal this track waits on. Returns the lap the new
        stint started on, which on a weird track can be a lap later than on a normal one."""
        with allure.step(f"Tyre change to set {fitted_idx}"):
            await self.tyre_sets(fitted_idx)
            await self.all_signals()
        assert self.latest_stint().m_fitted_index == fitted_idx
        return self.latest_stint().m_start_lap

    def stint_count(self) -> int:
        """Number of stints recorded in the tyre set history."""
        return self.driver.m_tyre_info.m_tyre_set_history_manager.length

    def stint_start_laps(self) -> List[int]:
        """The start lap of every stint in the tyre set history, oldest first."""
        return [stint.m_start_lap for stint in self.driver.m_tyre_info.m_tyre_set_history_manager.m_history]

    def wear_history(self, stint_index: int = -1) -> List[Tuple[int, float]]:
        """(lap number, front left wear) for each wear sample in a stint, oldest first."""
        stint = self.driver.m_tyre_info.m_tyre_set_history_manager.getEntry(index=stint_index)
        return [(sample.lap_number, sample.fl_tyre_wear) for sample in stint.m_tyre_wear_history]

    def latest_stint(self) -> Optional[TyreSetHistoryEntry]:
        """The most recently added stint, or None when the history is empty."""
        return self.driver.m_tyre_info.m_tyre_set_history_manager.getLastEntry()

    def extrapolator_samples(self) -> List[Tuple[int, float]]:
        """(lap number, front left wear) for each sample the tyre wear extrapolator holds, oldest first."""
        return [(sample.lap_number, sample.fl_tyre_wear)
                for sample in self.driver.m_tyre_info.m_tyre_wear_extrapolator.m_initial_data]


@pytest.fixture
async def race(manager: InjectingTelemetryManager, packets: Packets, state: SessionState,
               track: TrackID) -> Race:
    """A race on track, on the old set at lap START_LAP."""
    on_track = Race(manager, packets, state, track)
    await on_track.on_old_set()
    return on_track


@pytest.fixture(params=[NORMAL, UNKNOWN])
async def normal_race(request: pytest.FixtureRequest, manager: InjectingTelemetryManager, packets: Packets,
                      state: SessionState) -> Race:
    """A race on the normal track, or on an unrecognised one, on the old set at lap START_LAP."""
    on_track = Race(manager, packets, state, request.param)
    await on_track.on_old_set()
    return on_track


@pytest.fixture
async def restricted_race(manager: InjectingTelemetryManager, packets: Packets, state: SessionState,
                          track: TrackID) -> Race:
    """A race on track at lap START_LAP, with the player's telemetry RESTRICTED, so no tyre history."""
    on_track = Race(manager, packets, state, track)
    await on_track.on_old_set(TelemetrySetting.RESTRICTED)
    return on_track


@pytest.fixture(params=[WEIRD])
async def weird_race(request: pytest.FixtureRequest, manager: InjectingTelemetryManager, packets: Packets,
                     state: SessionState) -> Race:
    """A race on the weird track, on the old set at lap START_LAP."""
    on_track = Race(manager, packets, state, request.param)
    await on_track.on_old_set()
    return on_track

# ------------------------- DETECTION ----------------------------------------------------------------------------------

@allure.story("Detection")
@allure.title("A new set in the tyre sets packet registers a pending change ({race.track.name})")
async def test_detection_registers_pending(race: Race) -> None:
    """Race on the soft set, on lap 10 at 40 % wear. A TYRE_SETS packet reports the medium set fitted.

    Expected: a pending change is registered, and the history still has only the soft stint. The change can't
    complete until the packets it waits on arrive."""
    await race.tyre_sets()

    assert race.driver.m_pending_tyre_change is not None
    assert race.stint_count() == 1, "the change must not complete at detection"


@allure.story("Detection")
@allure.title("A race stop waits on a lap change only on a weird track ({race.track.name})")
async def test_wait_set_matches_track_topology(race: Race) -> None:
    """Race on the soft set, on lap 10. A TYRE_SETS packet reports the medium set. On Monaco the pit garage is before
    the line, so the stop happens before the lap completes.

    Expected: on Monaco the change waits on a lap change as well as a CAR_DAMAGE, and is flagged as a stop before
    the line. On Silverstone and an unrecognised track it waits on CAR_DAMAGE only."""
    await race.tyre_sets()

    pending = race.driver.m_pending_tyre_change
    is_weird = IS_WEIRD[race.track]
    assert pending.is_stop_before_line is is_weird
    assert pending.awaiting_lap_change is is_weird
    assert pending.awaiting_car_dmg


@allure.story("Detection")
@allure.title("A tyre sets packet for the fitted set records the lap it was seen on ({race.track.name})")
async def test_unchanged_tyre_sets_packet_records_the_lap(race: Race) -> None:
    """Race on the soft set, last seen on lap 10. The car drives on to lap 13, where a TYRE_SETS packet still reports
    the soft set.

    Expected: lap 13 becomes the last lap the soft set was seen on, which tells a later change whether the line has
    been crossed since. Nothing is registered."""
    with allure.step(f"Laps {START_LAP + 1} to {START_LAP + 3} on the soft set"):
        for lap in range(START_LAP + 1, START_LAP + 4):
            await race.lap(lap)
        await race.tyre_sets(OLD_SET_IDX)

    assert race.driver.m_current_set_last_seen_lap == START_LAP + 3
    assert race.driver.m_pending_tyre_change is None


@allure.story("Detection")
@allure.title("A repeated tyre sets packet keeps the first pending change ({race.track.name})")
async def test_repeat_tyre_sets_packets_do_not_re_register(race: Race) -> None:
    """Race on the soft set, on lap 10. Two TYRE_SETS packets report the medium set, as they keep arriving during
    the pit exit.

    Expected: the second one changes nothing. The pending change is the same object, with its waits as they were."""
    await race.tyre_sets()
    first = race.driver.m_pending_tyre_change
    await race.tyre_sets()

    assert race.driver.m_pending_tyre_change is first

# ------------------------- COMPLETION ---------------------------------------------------------------------------------

@allure.story("Completion")
@allure.title("A pending change completes once every awaited packet has arrived ({race.track.name})")
async def test_completes_once_all_awaited_signals_arrive(race: Race) -> None:
    """Race on the soft set, on lap 10. TYRE_SETS reports the medium set, then a CAR_DAMAGE with the new set at
    2.0 %, and on Monaco a lap change as well.

    Expected: nothing is pending, and a medium stint follows the soft one."""
    await race.tyre_sets()
    await race.all_signals()

    assert race.driver.m_pending_tyre_change is None
    assert race.stint_count() == 2
    assert race.latest_stint().m_fitted_index == NEW_SET_IDX


@allure.story("Completion")
@allure.title("The new stint starts from the new set's wear, not the old set's ({race.track.name})")
async def test_new_stint_seeded_from_new_tyre_wear(race: Race) -> None:
    """Race on the soft set, on lap 10 at 40 %. TYRE_SETS reports the medium set, then the CAR_DAMAGE with the new
    set at 2.0 % arrives (and on Monaco the lap change).

    This is what the wait for CAR_DAMAGE is for. The packets can arrive with the new set reported before its wear,
    and a stint started then would begin at 40 % and give the extrapolator a negative slope.

    Expected: the medium stint's first sample is 2.0 %."""
    await race.tyre_sets()
    await race.all_signals()

    assert race.latest_stint().m_tyre_wear_history[0].fl_tyre_wear == NEW_TYRE_WEAR


@allure.story("Completion")
@allure.title("The old stint's final wear is rewritten only on a weird track ({race.track.name})")
async def test_old_stint_final_wear_rewritten_only_on_weird_tracks(race: Race) -> None:
    """Race on the soft set, on lap 10 at 40 %, with samples for laps 0 to 9. A pit stop onto the medium set
    completes.

    Expected: on Monaco the stop came before the line, so the soft stint gains a lap 10 sample holding its final
    40 %. On Silverstone and an unrecognised track the soft stint's samples stay as recorded."""
    before = race.wear_history()
    await race.change_tyres(NEW_SET_IDX)

    expected = before + [(START_LAP, OLD_TYRE_WEAR)] if IS_WEIRD[race.track] else before
    assert race.wear_history(stint_index=0) == expected


@allure.story("Completion")
@allure.title("The old stint stores a copy of the rolling buffer's sample ({race.track.name})")
async def test_old_stint_holds_no_rolling_buffer_instance(race: Race) -> None:
    """Race on the soft set, on lap 10. A pit stop onto the medium set completes. On Monaco the soft stint's final
    wear is taken from the rolling buffer's highest sample.

    Expected: no sample in the soft stint is an object the rolling buffer still holds. A shared one would let a later
    change that picks the same sample rewrite this stint."""
    await race.change_tyres(NEW_SET_IDX)

    stored = race.driver.m_tyre_info.m_tyre_set_history_manager.getEntry(index=0).m_tyre_wear_history
    live = race.driver.m_tyre_info.tyre_wear
    assert not any(s is b for s in stored for b in live), "stint history must not hold a live rolling buffer instance"


@allure.story("Completion")
@allure.title("A car damage packet from before detection doesn't complete the change ({race.track.name})")
async def test_damage_packet_before_detection_does_not_satisfy_the_wait(race: Race) -> None:
    """Race on the soft set, on lap 10. A CAR_DAMAGE arrives, and only then does TYRE_SETS report the medium set.
    That CAR_DAMAGE can still hold the old set's wear, which is the packet the wait exists to skip.

    Expected: the change stays pending until the next CAR_DAMAGE (and on Monaco the lap change), then completes."""
    with allure.step("Before detection: a CAR_DAMAGE"):
        await race.car_damage()
    assert race.stint_count() == 1

    await race.tyre_sets()
    assert race.driver.m_pending_tyre_change is not None, "pre-detection D must not count"
    assert race.stint_count() == 1

    with allure.step("The awaited packets arrive"):
        await race.all_signals()
    assert race.stint_count() == 2

# ------------------------- NORMAL TRACK ORDERINGS ---------------------------------------------------------------------

@allure.story("Normal track orderings")
@allure.title("On a normal track, car damage alone completes the change ({normal_race.track.name})")
async def test_car_damage_alone_completes(normal_race: Race) -> None:
    """Race on Silverstone or an unrecognised track, where the pit garage is after the line, on the soft set on
    lap 10. TYRE_SETS reports the medium set, then a CAR_DAMAGE arrives.

    Expected: the change completes with no lap change, since the stop is already past the line."""
    await normal_race.tyre_sets()
    await normal_race.car_damage()

    assert normal_race.driver.m_pending_tyre_change is None
    assert normal_race.stint_count() == 2


@allure.story("Normal track orderings")
@allure.title("On a normal track, a lap change alone doesn't complete the change ({normal_race.track.name})")
async def test_lap_change_alone_does_not_complete(normal_race: Race) -> None:
    """Race on Silverstone or an unrecognised track, on the soft set on lap 10. TYRE_SETS reports the medium set,
    then the car crosses onto lap 11 before any CAR_DAMAGE.

    Expected: the change is still pending, waiting on CAR_DAMAGE, and the soft stint is the only one."""
    await normal_race.tyre_sets()
    await normal_race.lap_change()

    assert normal_race.driver.m_pending_tyre_change is not None
    assert normal_race.stint_count() == 1

# ------------------------- WEIRD TRACK ORDERINGS ----------------------------------------------------------------------

@allure.story("Weird track orderings")
@allure.title("On a weird track, car damage alone doesn't complete the change ({weird_race.track.name})")
async def test_car_damage_alone_does_not_complete(weird_race: Race) -> None:
    """Race on Monaco, where the pit garage is before the line, on the soft set on lap 10. TYRE_SETS reports the
    medium set, then a CAR_DAMAGE arrives before the car reaches the line.

    Expected: the change is still pending, waiting on the lap change, and the soft stint is the only one."""
    await weird_race.tyre_sets()
    await weird_race.car_damage()

    assert weird_race.driver.m_pending_tyre_change is not None
    assert weird_race.stint_count() == 1


@allure.story("Weird track orderings")
@allure.title("On a weird track, tyre sets, car damage, then a lap change completes the change "
              "({weird_race.track.name})")
async def test_t_d_l_completes(weird_race: Race) -> None:
    """Race on Monaco, on the soft set on lap 10. TYRE_SETS reports the medium set, then a CAR_DAMAGE arrives, then
    the car crosses onto lap 11.

    Expected: the lap change is the last awaited packet, so the change completes there."""
    await weird_race.tyre_sets()
    await weird_race.car_damage()
    await weird_race.lap_change()

    assert weird_race.driver.m_pending_tyre_change is None
    assert weird_race.stint_count() == 2


@allure.story("Weird track orderings")
@allure.title("On a weird track, tyre sets, a lap change, then car damage completes the change "
              "({weird_race.track.name})")
async def test_t_l_d_completes(weird_race: Race) -> None:
    """Race on Monaco, on the soft set on lap 10. TYRE_SETS reports the medium set, then the car crosses onto
    lap 11, then a CAR_DAMAGE arrives.

    Expected: the CAR_DAMAGE is the last awaited packet, so the change completes there."""
    await weird_race.tyre_sets()
    await weird_race.lap_change()
    await weird_race.car_damage()

    assert weird_race.driver.m_pending_tyre_change is None
    assert weird_race.stint_count() == 2

# ------------------------- LAP CHANGE BEFORE DETECTION ----------------------------------------------------------------

@allure.story("Lap change before detection")
@allure.title("A change seen after the car crossed the line doesn't wait another lap ({race.track.name})")
async def test_lap_change_before_detection_still_completes(race: Race) -> None:
    """Race on the soft set, last seen on lap 10. The car crosses onto lap 11, and only then does TYRE_SETS report
    the medium set. On Monaco this is routine: the garage is seconds before the line, and the tyre sets packet
    cycles through the cars.

    Expected: the line has been crossed since the soft set was last seen, so the lap change the wait is for has
    already happened. The next CAR_DAMAGE completes the change, not one a lap later."""
    with allure.step("The car crosses the line before the change is seen"):
        await race.lap_change()
    await race.tyre_sets()
    await race.car_damage()

    assert race.driver.m_pending_tyre_change is None, "a lap boundary already crossed must satisfy the wait"
    assert race.stint_count() == 2


@allure.story("Lap change before detection")
@allure.title("A change seen after the car crossed the line starts the stint on that lap ({race.track.name})")
async def test_new_stint_start_lap_is_the_lap_the_tyres_were_fitted(race: Race) -> None:
    """Race on the soft set, last seen on lap 10. The car crosses onto lap 11, then TYRE_SETS reports the medium set
    and a CAR_DAMAGE arrives. Waiting for another lap change would start the stint on lap 12.

    Expected: the medium stint starts on lap 11."""
    with allure.step("The car crosses the line before the change is seen"):
        await race.lap_change()
    await race.tyre_sets()
    await race.car_damage()

    assert race.latest_stint().m_start_lap == START_LAP + 1

# ------------------------- PENDING LIFETIME ---------------------------------------------------------------------------

@allure.story("Pending lifetime")
@allure.title("A change whose packets never arrive doesn't block a later one ({race.track.name})")
async def test_stuck_pending_change_does_not_suppress_a_later_one(race: Race) -> None:
    """Race on the soft set, on lap 10. TYRE_SETS reports the medium set, but the packets it waits on never arrive,
    as when a car retires or disconnects. Then TYRE_SETS reports the hard set.

    Expected: the pending change re-arms on the hard set and completes on its packets, so the history is the soft
    stint, then the hard one."""
    await race.tyre_sets()
    assert race.driver.m_pending_tyre_change.target_idx == NEW_SET_IDX

    with allure.step("No awaited packets arrive, and the hard set is fitted"):
        await race.tyre_sets(THIRD_SET_IDX)
    assert race.driver.m_pending_tyre_change.target_idx == THIRD_SET_IDX, \
        "a stale pending change must not suppress the set actually fitted now"

    await race.all_signals()
    assert race.stint_count() == 2
    assert race.latest_stint().m_fitted_index == THIRD_SET_IDX


@allure.story("Pending lifetime")
@allure.title("A flashback drops a pending change ({race.track.name})")
async def test_flashback_discards_pending_change(race: Race) -> None:
    """Race on the soft set, on lap 10. TYRE_SETS reports the medium set, and before any awaited packet the player
    flashes back over the line onto lap 9.

    Expected: the landing drops the pending change, since the wear state it would complete against was rewound.
    Only the FLBK and the landing LAP_DATA are sent. A CAR_DAMAGE after them would complete a change that survived,
    and hide it."""
    await race.tyre_sets()
    with allure.step(f"Flashback over the line onto lap {START_LAP - 1}, with no CAR_DAMAGE after it"):
        await race.manager.inject(race.packets.event(
            PacketEventData.EventPacketType.FLASHBACK, PacketEventData.Flashback.from_values(frame_identifier=1),
            session_uid=UID))
        await race.lap(START_LAP - 1)

    assert race.driver.m_pending_tyre_change is None, "a pending change must not complete against rewound state"

# ------------------------- FLASHBACK AND TYRE SET HISTORY -------------------------------------------------------------
#
# A flashback back over the line means the laps from the landing lap on are being redone. Their wear samples, and
# any stint that started on one of them, must go. The landing lap is only recorded again once the car crosses the
# line again, with the wear from then.


@allure.story("Flashback and tyre set history")
@allure.title("A flashback with no tyre history changes nothing ({restricted_race.track.name})")
async def test_flashback_with_no_tyre_history_changes_nothing(restricted_race: Race) -> None:
    """Race on lap 10 with the player's telemetry set to restricted, so no tyre history is kept. A flashback lands
    on lap 9.

    Expected: the history stays empty."""
    await restricted_race.flashback(land_lap=START_LAP - 1, wear=OLD_TYRE_WEAR - WEAR_PER_LAP)

    assert restricted_race.stint_count() == 0


@allure.story("Flashback and tyre set history")
@allure.title("A flashback within the lap keeps the tyre history ({race.track.name})")
async def test_flashback_within_a_lap_keeps_tyre_history(race: Race) -> None:
    """Race on the soft set, on lap 10 at 40 %, with samples for laps 0 to 9. A flashback lands on lap 10 again, at
    38 %.

    Expected: no lap is being redone, so the history is unchanged."""
    before = race.wear_history()
    await race.flashback(land_lap=START_LAP, wear=OLD_TYRE_WEAR - 2.0)

    assert race.wear_history() == before


@allure.story("Flashback and tyre set history")
@allure.title("A flashback over the line drops the redone lap's wear, and records it again ({race.track.name})")
async def test_flashback_over_the_line_drops_the_redone_laps_wear(race: Race) -> None:
    """Race on the soft set, on lap 10, with samples for laps 0 to 9 at 4 % a lap. A flashback lands on lap 9 at
    36 %. The car redoes lap 9 and crosses onto lap 10 again at 38 %.

    Expected: lap 9's sample goes at the landing. The second crossing records lap 9 again, with 38 %."""
    await race.flashback(land_lap=START_LAP - 1, wear=WEAR_PER_LAP * (START_LAP - 1))
    assert race.wear_history() == [(lap, WEAR_PER_LAP * lap) for lap in range(START_LAP - 1)]

    with allure.step(f"Lap {START_LAP - 1} redone: the car crosses onto lap {START_LAP} at 38.0 %"):
        await race.car_damage(wear=38.0)
        await race.lap(START_LAP)
    assert race.wear_history()[-1] == (START_LAP - 1, 38.0)


@allure.story("Flashback and tyre set history")
@allure.title("A flashback over the line keeps a stint that started earlier ({race.track.name})")
async def test_flashback_keeps_the_stint_when_earlier_wear_remains(race: Race) -> None:
    """Race on the soft set, on lap 10. The soft stint started on lap 1. A flashback lands on lap 9.

    Expected: only lap 9's sample goes. The stint started before the landing lap, so it stays, starting on lap 1,
    with laps 0 to 8."""
    await race.flashback(land_lap=START_LAP - 1, wear=WEAR_PER_LAP * (START_LAP - 1))

    assert race.stint_count() == 1
    assert race.latest_stint().m_start_lap == 1
    assert race.wear_history()[:START_LAP - 1] == [(lap, WEAR_PER_LAP * lap) for lap in range(START_LAP - 1)]


@allure.story("Flashback and tyre set history")
@allure.title("A flashback two laps back drops both laps' tyre wear ({race.track.name})")
async def test_flashback_two_laps_back_drops_both_laps(race: Race) -> None:
    """Race on the soft set, on lap 10, with one wear sample per completed lap at 4 % a lap (lap 9 ends at 36 %).
    One FLBK lands on lap 8, two laps back, at 32 %.

    Not reachable in the game: the flashback buffer is about 30 s, so one flashback goes back at most one lap. Kept as
    a robustness check of TyreSetHistoryManager.remove(), which used to drop only the last sample.

    Expected: laps 8 and 9 are being redone, so both their samples go. Laps 0 to 7 stay, and the stint stays."""
    with allure.step(f"One flashback lands on lap {START_LAP - 2}, two laps back"):
        await race.flashback(land_lap=START_LAP - 2, wear=WEAR_PER_LAP * (START_LAP - 2))

    assert race.stint_count() == 1
    assert race.wear_history() == [(lap, WEAR_PER_LAP * lap) for lap in range(START_LAP - 2)]


@allure.story("Flashback and tyre set history")
@allure.title("Two flashbacks in a row each drop one lap's tyre wear ({race.track.name})")
async def test_two_flashbacks_in_a_row_each_trim_history(race: Race) -> None:
    """Race on the soft set, on lap 10, with samples for laps 0 to 9. A flashback lands on lap 9, then a second one
    lands on lap 8, each one lap back from where the car is.

    Expected: each drops its landing lap's sample, leaving laps 0 to 7."""
    await race.flashback(land_lap=START_LAP - 1, wear=WEAR_PER_LAP * (START_LAP - 1))
    await race.flashback(land_lap=START_LAP - 2, wear=WEAR_PER_LAP * (START_LAP - 2))

    assert race.wear_history() == [(lap, WEAR_PER_LAP * lap) for lap in range(START_LAP - 2)]


@allure.story("Flashback and tyre set history")
@allure.title("A flashback to before a pit stop drops the new set's stint ({race.track.name})")
async def test_flashback_to_before_a_tyre_change_drops_the_new_set(race: Race) -> None:
    """Race on the soft set, on lap 10. The car pits onto the medium set, whose stint starts on lap 10 (lap 11 on
    Monaco, where the change waits for the line), and completes a lap on it at 6.0 %. A flashback lands on the lap
    before the medium stint started.

    Expected: the medium stint goes, leaving only the soft one."""
    with allure.step("Pit stop onto the medium set, then a lap on it"):
        medium_start = await race.change_tyres(NEW_SET_IDX)
        await race.car_damage(wear=NEW_TYRE_WEAR + WEAR_PER_LAP)
        await race.lap_change()

    with allure.step("Flashback onto the lap before the medium stint started"):
        await race.flashback(land_lap=medium_start - 1, wear=WEAR_PER_LAP * (START_LAP - 1))

    assert race.stint_count() == 1
    assert race.latest_stint().m_fitted_index == OLD_SET_IDX


@allure.story("Flashback and tyre set history")
@allure.title("A flashback over the line drops a stint with no completed lap ({race.track.name})")
async def test_flashback_drops_a_stint_with_no_completed_lap(race: Race) -> None:
    """Race on the soft set, on lap 10, with one wear sample per completed lap at 4 % a lap. The car pits onto the
    medium set at 2.0 %. On Silverstone the new stint starts on lap 10. On Monaco the change also waits for the line,
    so it starts on lap 11. Before a lap is completed on the new set, the car flashes back over the line onto the lap
    before the stint started.

    The outdated laps are the lap snapshot keys from the landing lap on. The new stint's start lap has no snapshot
    yet, so it wasn't one of them, and the stint used to survive the rewind.

    Expected: the new stint goes, leaving only the old set's. The old stint loses only the redone lap's sample."""
    with allure.step("Pit stop onto the medium set, with no lap completed on it"):
        new_start = await race.change_tyres(NEW_SET_IDX)
    assert race.stint_start_laps() == [1, new_start]
    assert new_start not in race.driver.m_per_lap_snapshots, f"{race.track.name}: a lap was completed on the new set"

    with allure.step(f"The car flashes back over the line onto lap {new_start - 1}"):
        await race.flashback(land_lap=new_start - 1, wear=WEAR_PER_LAP * (new_start - 1))

    assert race.stint_start_laps() == [1]
    assert race.latest_stint().m_fitted_index == OLD_SET_IDX
    assert race.wear_history() == [(lap, WEAR_PER_LAP * lap) for lap in range(new_start - 1)]


@allure.story("Flashback and tyre set history")
@allure.title("A flashback that drops the new stint refills the wear extrapolator from the old one ({track.name})")
async def test_flashback_dropping_the_new_stint_refills_the_extrapolator(race: Race, track: TrackID) -> None:
    """The new set is fitted, which restarts the tyre wear extrapolator from its first sample at 2 %. Before a lap is
    completed on it, the car flashes back over the line onto the previous lap, which drops the new stint.

    Expected: the extrapolator holds the old set's samples from before the stop again, less the redone lap. It used to
    be left empty, since the new set's first sample was its only one."""
    old_set_samples = race.extrapolator_samples()
    new_start = await race.change_tyres(NEW_SET_IDX)
    assert [wear for _, wear in race.extrapolator_samples()] == [NEW_TYRE_WEAR]

    land_lap = new_start - 1
    await race.flashback(land_lap=land_lap, wear=WEAR_PER_LAP * land_lap)

    assert race.extrapolator_samples() == [(lap, wear) for lap, wear in old_set_samples if lap < land_lap]


@allure.story("Flashback and tyre set history")
@allure.title("A flashback into the last stint's first lap drops only that stint ({race.track.name})")
async def test_flashback_across_several_stints_trims_only_the_redone_laps(race: Race) -> None:
    """Race on the soft set, on lap 10. The car pits onto the medium set and does two laps on it, then pits onto the
    hard set and does one lap on that. A flashback lands on the lap the hard stint started on.

    Expected: the hard stint goes. The soft and medium stints stay, with the medium one last."""
    with allure.step("Medium stint: two laps"):
        medium_start = await race.change_tyres(NEW_SET_IDX)
        for lap in (1, 2):
            await race.car_damage(wear=NEW_TYRE_WEAR + lap * WEAR_PER_LAP)
            await race.lap_change()
    with allure.step("Hard stint: one lap"):
        hard_start = await race.change_tyres(THIRD_SET_IDX)
        await race.car_damage(wear=NEW_TYRE_WEAR + WEAR_PER_LAP)
        await race.lap_change()
    assert race.stint_start_laps() == [1, medium_start, hard_start]

    with allure.step(f"Flashback into lap {hard_start}, where the hard stint started"):
        await race.flashback(land_lap=hard_start, wear=NEW_TYRE_WEAR + 2 * WEAR_PER_LAP)

    assert race.stint_start_laps() == [1, medium_start]
    assert race.latest_stint().m_fitted_index == NEW_SET_IDX
