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
the old stint's final wear is rewritten on completion.

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
async def test_detection_registers_pending(race: Race) -> None:
    await race.tyre_sets()

    assert race.driver.m_pending_tyre_change is not None
    assert race.stint_count() == 1, "the change must not complete at detection"


@allure.story("Detection")
async def test_wait_set_matches_track_topology(race: Race) -> None:
    """Weird tracks wait on a lap change too; normal tracks only on car damage."""
    await race.tyre_sets()

    pending = race.driver.m_pending_tyre_change
    is_weird = IS_WEIRD[race.track]
    assert pending.is_weird_track is is_weird
    assert pending.awaiting_lap_change is is_weird
    assert pending.awaiting_car_dmg


@allure.story("Detection")
async def test_unchanged_tyre_sets_packet_records_the_lap(race: Race) -> None:
    """Packets confirming the fitted set track the lap, without registering anything."""
    for lap in range(START_LAP + 1, START_LAP + 4):
        await race.lap(lap)
    await race.tyre_sets(OLD_SET_IDX)

    assert race.driver.m_current_set_last_seen_lap == START_LAP + 3
    assert race.driver.m_pending_tyre_change is None


@allure.story("Detection")
async def test_repeat_tyre_sets_packets_do_not_re_register(race: Race) -> None:
    """Tyre sets packets keep arriving during the pit exit; detection is idempotent."""
    await race.tyre_sets()
    first = race.driver.m_pending_tyre_change
    await race.tyre_sets()

    assert race.driver.m_pending_tyre_change is first

# ------------------------- COMPLETION ---------------------------------------------------------------------------------

@allure.story("Completion")
async def test_completes_once_all_awaited_signals_arrive(race: Race) -> None:
    await race.tyre_sets()
    await race.all_signals()

    assert race.driver.m_pending_tyre_change is None
    assert race.stint_count() == 2
    assert race.latest_stint().m_fitted_index == NEW_SET_IDX


@allure.story("Completion")
async def test_new_stint_seeded_from_new_tyre_wear(race: Race) -> None:
    """The whole point of the damage wait: never seed the new stint from the old set."""
    await race.tyre_sets()
    await race.all_signals()

    assert race.latest_stint().m_tyre_wear_history[0].fl_tyre_wear == NEW_TYRE_WEAR


@allure.story("Completion")
async def test_old_stint_final_wear_rewritten_only_on_weird_tracks(race: Race) -> None:
    """Weird tracks close the old stint with the old set's final wear. Others leave its history as recorded."""
    before = race.wear_history()
    await race.change_tyres(NEW_SET_IDX)

    expected = before + [(START_LAP, OLD_TYRE_WEAR)] if IS_WEIRD[race.track] else before
    assert race.wear_history(stint_index=0) == expected


@allure.story("Completion")
async def test_old_stint_holds_no_rolling_buffer_instance(race: Race) -> None:
    """The weird-track rewrite stores a copy of the rolling buffer's max sample, not the live instance."""
    await race.change_tyres(NEW_SET_IDX)

    stored = race.driver.m_tyre_info.m_tyre_set_history_manager.getEntry(index=0).m_tyre_wear_history
    live = race.driver.m_tyre_info.tyre_wear
    assert not any(s is b for s in stored for b in live), "stint history must not hold a live rolling buffer instance"


@allure.story("Completion")
async def test_damage_packet_before_detection_does_not_satisfy_the_wait(race: Race) -> None:
    """D arriving before T must not count - it is what the wait exists to exclude."""
    await race.car_damage()
    assert race.stint_count() == 1

    await race.tyre_sets()
    assert race.driver.m_pending_tyre_change is not None, "pre-detection D must not count"
    assert race.stint_count() == 1

    await race.all_signals()
    assert race.stint_count() == 2

# ------------------------- NORMAL TRACK ORDERINGS ---------------------------------------------------------------------

@allure.story("Normal track orderings")
async def test_car_damage_alone_completes(normal_race: Race) -> None:
    await normal_race.tyre_sets()
    await normal_race.car_damage()

    assert normal_race.driver.m_pending_tyre_change is None
    assert normal_race.stint_count() == 2


@allure.story("Normal track orderings")
async def test_lap_change_alone_does_not_complete(normal_race: Race) -> None:
    await normal_race.tyre_sets()
    await normal_race.lap_change()

    assert normal_race.driver.m_pending_tyre_change is not None
    assert normal_race.stint_count() == 1

# ------------------------- WEIRD TRACK ORDERINGS ----------------------------------------------------------------------

@allure.story("Weird track orderings")
async def test_car_damage_alone_does_not_complete(weird_race: Race) -> None:
    await weird_race.tyre_sets()
    await weird_race.car_damage()

    assert weird_race.driver.m_pending_tyre_change is not None
    assert weird_race.stint_count() == 1


@allure.story("Weird track orderings")
async def test_t_d_l_completes(weird_race: Race) -> None:
    await weird_race.tyre_sets()
    await weird_race.car_damage()
    await weird_race.lap_change()

    assert weird_race.driver.m_pending_tyre_change is None
    assert weird_race.stint_count() == 2


@allure.story("Weird track orderings")
async def test_t_l_d_completes(weird_race: Race) -> None:
    await weird_race.tyre_sets()
    await weird_race.lap_change()
    await weird_race.car_damage()

    assert weird_race.driver.m_pending_tyre_change is None
    assert weird_race.stint_count() == 2

# ------------------------- LAP CHANGE BEFORE DETECTION ----------------------------------------------------------------

@allure.story("Lap change before detection")
async def test_lap_change_before_detection_still_completes(race: Race) -> None:
    """The wait is for "a lap boundary passed since the tyres were fitted". That is already satisfied here, so
    the change completes on the next car damage packet rather than a full lap later."""
    await race.lap_change()     # L - arrives before anything is pending
    await race.tyre_sets()
    await race.car_damage()

    assert race.driver.m_pending_tyre_change is None, "a lap boundary already crossed must satisfy the wait"
    assert race.stint_count() == 2


@allure.story("Lap change before detection")
async def test_new_stint_start_lap_is_the_lap_the_tyres_were_fitted(race: Race) -> None:
    """Knock-on of the above: a late completion would land start_lap a lap out."""
    await race.lap_change()
    await race.tyre_sets()
    await race.car_damage()

    assert race.latest_stint().m_start_lap == START_LAP + 1

# ------------------------- PENDING LIFETIME ---------------------------------------------------------------------------

@allure.story("Pending lifetime")
async def test_stuck_pending_change_does_not_suppress_a_later_one(race: Race) -> None:
    """A pending change whose packets never arrive must not wedge tyre tracking: a later set re-arms it."""
    await race.tyre_sets()
    assert race.driver.m_pending_tyre_change.target_idx == NEW_SET_IDX

    # No packets arrive; the set moves on regardless
    await race.tyre_sets(THIRD_SET_IDX)
    assert race.driver.m_pending_tyre_change.target_idx == THIRD_SET_IDX, \
        "a stale pending change must not suppress the set actually fitted now"

    await race.all_signals()
    assert race.stint_count() == 2
    assert race.latest_stint().m_fitted_index == THIRD_SET_IDX


@allure.story("Pending lifetime")
async def test_flashback_discards_pending_change(race: Race) -> None:
    """A flashback rewinds the wear state; a pending change must not outlive it."""
    await race.tyre_sets()
    await race.manager.inject(race.packets.event(
        PacketEventData.EventPacketType.FLASHBACK, PacketEventData.Flashback.from_values(frame_identifier=1),
        session_uid=UID))
    await race.lap(START_LAP - 1)   # the landing packet, a lap back

    assert race.driver.m_pending_tyre_change is None, "a pending change must not complete against rewound state"

# ------------------------- FLASHBACK AND TYRE SET HISTORY -------------------------------------------------------------
#
# A flashback back over the line means the laps from the landing lap on are being redone. Their wear samples, and
# any stint that started on one of them, must go. The landing lap is only recorded again once the car crosses the
# line again, with the wear from then.

# Known bugs on this branch: the xfails flip to XPASS (and fail, being strict) once they are fixed
EARLY_RE_RECORD = ("The landing lap's wear is recorded again at the landing packet, from packet copies taken before "
                   "the rewind: onLapChange runs straight after _handleFlashBack. feat/telemetry-analysis-base "
                   "moves flashback handling into onFlashback.")
SINGLE_SAMPLE_REMOVE = ("TyreSetHistoryManager.remove() pops only the last wear sample, so a rewind of two or more "
                        "laps leaves the earlier laps' samples behind.")


@allure.story("Flashback and tyre set history")
async def test_flashback_with_no_tyre_history_changes_nothing(restricted_race: Race) -> None:
    await restricted_race.flashback(land_lap=START_LAP - 1, wear=OLD_TYRE_WEAR - WEAR_PER_LAP)

    assert restricted_race.stint_count() == 0


@allure.story("Flashback and tyre set history")
async def test_flashback_within_a_lap_keeps_tyre_history(race: Race) -> None:
    """Landing on the same lap redoes no lap, so nothing is removed."""
    before = race.wear_history()
    await race.flashback(land_lap=START_LAP, wear=OLD_TYRE_WEAR - 2.0)

    assert race.wear_history() == before


@allure.story("Flashback and tyre set history")
@pytest.mark.xfail(strict=True, reason=EARLY_RE_RECORD)
async def test_flashback_over_the_line_drops_the_redone_laps_wear(race: Race) -> None:
    await race.flashback(land_lap=START_LAP - 1, wear=WEAR_PER_LAP * (START_LAP - 1))
    assert race.wear_history() == [(lap, WEAR_PER_LAP * lap) for lap in range(START_LAP - 1)]

    # The redone lap is recorded again when the car crosses the line, with the wear from then
    await race.car_damage(wear=38.0)
    await race.lap(START_LAP)
    assert race.wear_history()[-1] == (START_LAP - 1, 38.0)


@allure.story("Flashback and tyre set history")
async def test_flashback_keeps_the_stint_when_earlier_wear_remains(race: Race) -> None:
    """Only the redone lap's sample goes. The stint started before the landing lap, so it stays."""
    await race.flashback(land_lap=START_LAP - 1, wear=WEAR_PER_LAP * (START_LAP - 1))

    assert race.stint_count() == 1
    assert race.latest_stint().m_start_lap == 1
    assert race.wear_history()[:START_LAP - 1] == [(lap, WEAR_PER_LAP * lap) for lap in range(START_LAP - 1)]


@allure.story("Flashback and tyre set history")
@pytest.mark.xfail(strict=True, reason=f"{SINGLE_SAMPLE_REMOVE} {EARLY_RE_RECORD}")
async def test_flashback_two_laps_back_drops_both_laps(race: Race) -> None:
    await race.flashback(land_lap=START_LAP - 2, wear=WEAR_PER_LAP * (START_LAP - 2))

    assert race.wear_history() == [(lap, WEAR_PER_LAP * lap) for lap in range(START_LAP - 2)]


@allure.story("Flashback and tyre set history")
@pytest.mark.xfail(strict=True, reason=f"{SINGLE_SAMPLE_REMOVE} {EARLY_RE_RECORD}")
async def test_two_flashbacks_in_a_row_each_trim_history(race: Race) -> None:
    await race.flashback(land_lap=START_LAP - 1, wear=WEAR_PER_LAP * (START_LAP - 1))
    await race.flashback(land_lap=START_LAP - 2, wear=WEAR_PER_LAP * (START_LAP - 2))

    assert race.wear_history() == [(lap, WEAR_PER_LAP * lap) for lap in range(START_LAP - 2)]


@allure.story("Flashback and tyre set history")
async def test_flashback_to_before_a_tyre_change_drops_the_new_set(race: Race) -> None:
    medium_start = await race.change_tyres(NEW_SET_IDX)
    await race.car_damage(wear=NEW_TYRE_WEAR + WEAR_PER_LAP)
    await race.lap_change()

    # Back to the lap before the medium stint started
    await race.flashback(land_lap=medium_start - 1, wear=WEAR_PER_LAP * (START_LAP - 1))

    assert race.stint_count() == 1
    assert race.latest_stint().m_fitted_index == OLD_SET_IDX


@allure.story("Flashback and tyre set history")
async def test_flashback_across_several_stints_trims_only_the_redone_laps(race: Race) -> None:
    medium_start = await race.change_tyres(NEW_SET_IDX)
    for lap in (1, 2):
        await race.car_damage(wear=NEW_TYRE_WEAR + lap * WEAR_PER_LAP)
        await race.lap_change()
    hard_start = await race.change_tyres(THIRD_SET_IDX)
    await race.car_damage(wear=NEW_TYRE_WEAR + WEAR_PER_LAP)
    await race.lap_change()
    assert race.stint_start_laps() == [1, medium_start, hard_start]

    # Back into the lap the hard stint started on: only that stint goes
    await race.flashback(land_lap=hard_start, wear=NEW_TYRE_WEAR + 2 * WEAR_PER_LAP)

    assert race.stint_start_laps() == [1, medium_start]
    assert race.latest_stint().m_fitted_index == NEW_SET_IDX
