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
"""

# Fixtures that take other fixtures as arguments are how pytest works, not shadowing
# pylint: disable=redefined-outer-name

# ------------------------- IMPORTS ------------------------------------------------------------------------------------

from typing import Optional

import pytest

from apps.backend.state_mgmt_layer import SessionState
from apps.backend.state_mgmt_layer.data_per_driver import TyreSetHistoryEntry
from apps.backend.state_mgmt_layer.data_per_driver.data_per_driver import DataPerDriver
from lib.f1_types import PacketEventData, TrackID

from .harness import InjectingTelemetryManager
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

# ------------------------- FIXTURES -----------------------------------------------------------------------------------

@pytest.fixture(params=[NORMAL_TRACK, WEIRD_TRACK, UNKNOWN_TRACK], ids=["normal", "weird", "unknown"])
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
        await self.manager.inject(self.packets.tyre_sets(car_idx=0, fitted_idx=fitted_idx, session_uid=UID))

    async def car_damage(self, wear: float = NEW_TYRE_WEAR) -> None:
        """(D) CAR_DAMAGE with all four tyres at wear."""
        await self.manager.inject(self.packets.car_damage(damage(0, tyre_wear=wear), session_uid=UID))

    async def lap(self, lap: int) -> None:
        """LAP_DATA putting the player on lap."""
        await self.manager.inject(self.packets.lap(car(0, lap=lap, lap_distance=100.0), session_uid=UID))

    async def lap_change(self) -> None:
        """(L) The player crosses the line."""
        await self.lap(self.driver.m_lap_info.m_current_lap + 1)

    async def all_signals(self) -> None:
        """Every signal this track's topology waits on, after detection."""
        await self.car_damage()
        if IS_WEIRD[self.track]:
            await self.lap_change()

    async def on_old_set(self) -> None:
        """Lap START_LAP on the old set, with its stint in history. Wear reaches OLD_TYRE_WEAR on that lap."""
        await self.session()
        await self.manager.inject(self.packets.participants(player("Player"), session_uid=UID))
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

        assert self.driver.m_lap_info.m_current_lap == START_LAP
        assert self.driver.m_current_set_last_seen_lap == START_LAP
        assert self.stint_count() == 1
        assert self.latest_stint().m_fitted_index == OLD_SET_IDX

    def stint_count(self) -> int:
        """Number of stints recorded in the tyre set history."""
        return self.driver.m_tyre_info.m_tyre_set_history_manager.length

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


@pytest.fixture(params=[NORMAL_TRACK, UNKNOWN_TRACK], ids=["normal", "unknown"])
async def normal_race(request: pytest.FixtureRequest, manager: InjectingTelemetryManager, packets: Packets,
                      state: SessionState) -> Race:
    """A race on the normal track, or on an unrecognised one, on the old set at lap START_LAP."""
    on_track = Race(manager, packets, state, request.param)
    await on_track.on_old_set()
    return on_track


@pytest.fixture
async def weird_race(manager: InjectingTelemetryManager, packets: Packets, state: SessionState) -> Race:
    """A race on the weird track, on the old set at lap START_LAP."""
    on_track = Race(manager, packets, state, WEIRD_TRACK)
    await on_track.on_old_set()
    return on_track

# ------------------------- DETECTION ----------------------------------------------------------------------------------

async def test_detection_registers_pending(race: Race) -> None:
    await race.tyre_sets()

    assert race.driver.m_pending_tyre_change is not None
    assert race.stint_count() == 1, "the change must not complete at detection"


async def test_wait_set_matches_track_topology(race: Race) -> None:
    """Weird tracks wait on a lap change too; normal tracks only on car damage."""
    await race.tyre_sets()

    pending = race.driver.m_pending_tyre_change
    is_weird = IS_WEIRD[race.track]
    assert pending.is_weird_track is is_weird
    assert pending.awaiting_lap_change is is_weird
    assert pending.awaiting_car_dmg


async def test_unchanged_tyre_sets_packet_records_the_lap(race: Race) -> None:
    """Packets confirming the fitted set track the lap, without registering anything."""
    for lap in range(START_LAP + 1, START_LAP + 4):
        await race.lap(lap)
    await race.tyre_sets(OLD_SET_IDX)

    assert race.driver.m_current_set_last_seen_lap == START_LAP + 3
    assert race.driver.m_pending_tyre_change is None


async def test_repeat_tyre_sets_packets_do_not_re_register(race: Race) -> None:
    """Tyre sets packets keep arriving during the pit exit; detection is idempotent."""
    await race.tyre_sets()
    first = race.driver.m_pending_tyre_change
    await race.tyre_sets()

    assert race.driver.m_pending_tyre_change is first

# ------------------------- COMPLETION ---------------------------------------------------------------------------------

async def test_completes_once_all_awaited_signals_arrive(race: Race) -> None:
    await race.tyre_sets()
    await race.all_signals()

    assert race.driver.m_pending_tyre_change is None
    assert race.stint_count() == 2
    assert race.latest_stint().m_fitted_index == NEW_SET_IDX


async def test_new_stint_seeded_from_new_tyre_wear(race: Race) -> None:
    """The whole point of the damage wait: never seed the new stint from the old set."""
    await race.tyre_sets()
    await race.all_signals()

    assert race.latest_stint().m_tyre_wear_history[0].fl_tyre_wear == NEW_TYRE_WEAR


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

async def test_car_damage_alone_completes(normal_race: Race) -> None:
    await normal_race.tyre_sets()
    await normal_race.car_damage()

    assert normal_race.driver.m_pending_tyre_change is None
    assert normal_race.stint_count() == 2


async def test_lap_change_alone_does_not_complete(normal_race: Race) -> None:
    await normal_race.tyre_sets()
    await normal_race.lap_change()

    assert normal_race.driver.m_pending_tyre_change is not None
    assert normal_race.stint_count() == 1

# ------------------------- WEIRD TRACK ORDERINGS ----------------------------------------------------------------------

async def test_car_damage_alone_does_not_complete(weird_race: Race) -> None:
    await weird_race.tyre_sets()
    await weird_race.car_damage()

    assert weird_race.driver.m_pending_tyre_change is not None
    assert weird_race.stint_count() == 1


async def test_t_d_l_completes(weird_race: Race) -> None:
    await weird_race.tyre_sets()
    await weird_race.car_damage()
    await weird_race.lap_change()

    assert weird_race.driver.m_pending_tyre_change is None
    assert weird_race.stint_count() == 2


async def test_t_l_d_completes(weird_race: Race) -> None:
    await weird_race.tyre_sets()
    await weird_race.lap_change()
    await weird_race.car_damage()

    assert weird_race.driver.m_pending_tyre_change is None
    assert weird_race.stint_count() == 2


async def test_old_stint_final_wear_rewritten_to_old_tyre_value(weird_race: Race) -> None:
    """The weird-track rewrite: the old stint's last lap keeps the old set's wear."""
    await weird_race.tyre_sets()
    await weird_race.car_damage()
    await weird_race.lap_change()

    old_stint = weird_race.driver.m_tyre_info.m_tyre_set_history_manager.getEntry(index=0)
    assert old_stint.m_tyre_wear_history[-1].fl_tyre_wear == OLD_TYRE_WEAR


async def test_rewrite_does_not_alias_the_rolling_buffer(weird_race: Race) -> None:
    """The rewrite must store a copy, not the live sample still in the rolling buffer.

    `get_max_average_with_index()` returns the instance held in the deque. Storing that same object into the
    stint history would leave it with two owners, so a later change selecting it again would rewrite an
    already recorded entry in place.
    """
    await weird_race.tyre_sets()
    await weird_race.car_damage()
    await weird_race.lap_change()

    stored = weird_race.driver.m_tyre_info.m_tyre_set_history_manager.getEntry(index=0).m_tyre_wear_history[-1]
    assert all(stored is not sample for sample in weird_race.driver.m_tyre_info.tyre_wear), \
        "stint history must not hold a live rolling buffer instance"

# ------------------------- LAP CHANGE BEFORE DETECTION ----------------------------------------------------------------

async def test_lap_change_before_detection_still_completes(race: Race) -> None:
    """The wait is for "a lap boundary passed since the tyres were fitted". That is already satisfied here, so
    the change completes on the next car damage packet rather than a full lap later."""
    await race.lap_change()     # L - arrives before anything is pending
    await race.tyre_sets()
    await race.car_damage()

    assert race.driver.m_pending_tyre_change is None, "a lap boundary already crossed must satisfy the wait"
    assert race.stint_count() == 2


async def test_new_stint_start_lap_is_the_lap_the_tyres_were_fitted(race: Race) -> None:
    """Knock-on of the above: a late completion would land start_lap a lap out."""
    await race.lap_change()
    await race.tyre_sets()
    await race.car_damage()

    assert race.latest_stint().m_start_lap == START_LAP + 1

# ------------------------- PENDING LIFETIME ---------------------------------------------------------------------------

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


async def test_flashback_discards_pending_change(race: Race) -> None:
    """A flashback rewinds the wear state; a pending change must not outlive it."""
    await race.tyre_sets()
    await race.manager.inject(race.packets.event(
        PacketEventData.EventPacketType.FLASHBACK, PacketEventData.Flashback.from_values(frame_identifier=1),
        session_uid=UID))
    await race.lap(START_LAP - 1)   # the landing packet, a lap back

    assert race.driver.m_pending_tyre_change is None, "a pending change must not complete against rewound state"
