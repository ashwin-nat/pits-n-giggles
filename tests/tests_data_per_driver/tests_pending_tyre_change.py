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

"""Ordering tests for the delayed tyre set change state machine (``PendingTyreChange``).

The game's packet emitter is periodic and per-car index cycled, so the three inputs that
drive a tyre set change - the tyre sets packet (T), a car damage packet (D) and a lap
change (L) - can interleave in any order. These tests pin the completion semantics for
each interleaving without needing sockets, a replay or a pcap corpus.

Everything that is not inherently topology-specific runs twice, against a normal track
(finish line before the pit garage) and a weird one (pit garage before the finish line),
via the ``track`` fixture.
"""

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

import logging
from typing import Optional
from unittest.mock import MagicMock

import pytest

from apps.backend.state_mgmt_layer.data_per_driver import TyreSetHistoryEntry
from apps.backend.state_mgmt_layer.data_per_driver.data_per_driver import \
    DataPerDriver
from lib.f1_types import F1Utils, TrackID
from lib.tyre_wear_extrapolator import TyreWearPerLap

# -------------------------------------- GLOBALS -----------------------------------------------------------------------

WEIRD_TRACK = TrackID.Monaco          # pit garage before the finish line
NORMAL_TRACK = TrackID.Silverstone    # finish line before the pit garage

OLD_SET_IDX, NEW_SET_IDX, THIRD_SET_IDX = 0, 1, 2
OLD_SET_KEY, NEW_SET_KEY, THIRD_SET_KEY = "old-set", "new-set", "third-set"

START_LAP = 10
OLD_TYRE_WEAR = 40.0    # worn, end of stint
NEW_TYRE_WEAR = 2.0     # fresh set just fitted

# -------------------------------------- HELPERS -----------------------------------------------------------------------

def _car_damage(wear: float) -> MagicMock:
    """Build a car damage packet stub whose four tyres all carry the given wear."""

    pkt = MagicMock()
    pkt.m_tyresWear = [wear] * 4
    return pkt

def _tyre_sets(fitted_idx: int, key: str) -> MagicMock:
    """Build a tyre sets packet stub reporting the given fitted set."""

    pkt = MagicMock()
    pkt.m_fittedIdx = fitted_idx
    pkt.getFittedTyreSetKey.return_value = key
    # getTyreSet() is left as a MagicMock - the race control message only stringifies it
    return pkt

@pytest.fixture(name="track", params=[NORMAL_TRACK, WEIRD_TRACK], ids=["normal", "weird"])
def _track(request) -> TrackID:
    """Run the test against both track topologies."""

    return request.param

@pytest.fixture(name="driver")
def _driver() -> DataPerDriver:
    """A driver mid-race on the old tyre set, with one stint already in history.

    Positioned exactly where a pit stop would put it: the rolling wear buffer holds the
    old set's worn samples, and the packet copies still describe the old set.
    """

    obj = DataPerDriver(
        index=0,
        logger=logging.getLogger("test"),
        total_laps=50,
        state_ref=MagicMock(),
        weather_aware_prediction=False,
        tyre_wear_window_size=None,
        harvest_power_window_size=5,
    )
    obj.m_driver_info.telemetry_setting = True
    obj.m_lap_info.m_current_lap = START_LAP
    # Completion emits a tyre change race control message, which propagates to the session
    obj.m_race_ctrl.session_mgr = MagicMock()

    # The stint that is about to end, with one wear entry for its latest lap
    obj.m_tyre_info.m_tyre_set_history_manager.add(TyreSetHistoryEntry(
        start_lap=1,
        index=OLD_SET_IDX,
        tyre_set_key=OLD_SET_KEY,
        initial_tyre_wear=TyreWearPerLap(
            fl_tyre_wear=OLD_TYRE_WEAR, fr_tyre_wear=OLD_TYRE_WEAR,
            rl_tyre_wear=OLD_TYRE_WEAR, rr_tyre_wear=OLD_TYRE_WEAR,
            lap_number=START_LAP - 1, desc="old set"),
    ))

    # Rolling buffer holds the old set's worn samples
    for _ in range(5):
        obj.m_tyre_info.tyre_wear.push(TyreWearPerLap(
            fl_tyre_wear=OLD_TYRE_WEAR, fr_tyre_wear=OLD_TYRE_WEAR,
            rl_tyre_wear=OLD_TYRE_WEAR, rr_tyre_wear=OLD_TYRE_WEAR,
            lap_number=START_LAP, desc="old set rolling"))

    obj.m_packet_copies.m_packet_tyre_sets = _tyre_sets(OLD_SET_IDX, OLD_SET_KEY)
    obj.m_packet_copies.m_packet_car_damage = _car_damage(OLD_TYRE_WEAR)

    # A tyre sets packet confirming the old set has arrived this lap, as it would have been
    # doing all stint. This is what lets a later change tell whether the line has been
    # crossed since the old set was last seen fitted.
    obj.updateTyreSetData(fitted_index=OLD_SET_IDX, track=NORMAL_TRACK)
    assert obj.m_current_set_last_seen_lap == START_LAP
    return obj

def fire_tyre_sets(driver: DataPerDriver, track: TrackID,
                   fitted_idx: int = NEW_SET_IDX, key: str = NEW_SET_KEY) -> None:
    """(T) The tyre sets packet reporting the new set arrives - this is detection."""

    driver.m_packet_copies.m_packet_tyre_sets = _tyre_sets(fitted_idx, key)
    driver.updateTyreSetData(fitted_index=fitted_idx, track=track)

def fire_car_damage(driver: DataPerDriver, wear: float = NEW_TYRE_WEAR) -> None:
    """(D) A car damage packet arrives, mirroring what session_state does to the driver."""

    driver.m_packet_copies.m_packet_car_damage = _car_damage(wear)
    driver.m_tyre_info.tyre_wear.push(TyreWearPerLap(
        fl_tyre_wear=wear, fr_tyre_wear=wear, rl_tyre_wear=wear, rr_tyre_wear=wear,
        desc="new set rolling"))
    driver.notifyCarDamageUpdated()

def fire_lap_change(driver: DataPerDriver) -> None:
    """(L) The car crosses the line, mirroring _handleLapChangeLogic's ordering."""

    driver.m_lap_info.m_current_lap += 1
    driver.notifyLapChanged()

def deliver_all_signals(driver: DataPerDriver, track: TrackID) -> None:
    """Fire every signal the given topology waits on, after detection."""

    fire_car_damage(driver)
    if F1Utils.isFinishLineAfterPitGarage(track):
        fire_lap_change(driver)

def stint_count(driver: DataPerDriver) -> int:
    """Number of stints recorded in the tyre set history."""

    return driver.m_tyre_info.m_tyre_set_history_manager.length

def latest_stint(driver: DataPerDriver) -> Optional[TyreSetHistoryEntry]:
    """The most recently added stint, or None when the history is empty."""

    return driver.m_tyre_info.m_tyre_set_history_manager.getLastEntry()

# -------------------------------------- TESTS -------------------------------------------------------------------------

class TestDetection:
    """Detection registers a pending change without completing it."""

    def test_detection_registers_pending(self, driver, track):
        fire_tyre_sets(driver, track)

        assert driver.m_pending_tyre_change is not None
        assert stint_count(driver) == 1, "the change must not complete at detection"

    def test_wait_set_matches_track_topology(self, driver, track):
        """Weird tracks wait on a lap change too; normal tracks only on car damage."""

        fire_tyre_sets(driver, track)

        pending = driver.m_pending_tyre_change
        is_weird = F1Utils.isFinishLineAfterPitGarage(track)
        assert pending.is_weird_track is is_weird
        assert pending.awaiting_lap_change is is_weird
        assert pending.awaiting_car_dmg

    def test_unchanged_tyre_sets_packet_records_the_lap(self, driver, track):
        """Packets confirming the fitted set track the lap, without registering anything."""

        driver.m_lap_info.m_current_lap = START_LAP + 3
        driver.updateTyreSetData(fitted_index=OLD_SET_IDX, track=track)

        assert driver.m_current_set_last_seen_lap == START_LAP + 3
        assert driver.m_pending_tyre_change is None

    def test_repeat_tyre_sets_packets_do_not_re_register(self, driver, track):
        """Tyre sets packets keep arriving during the pit exit; detection is idempotent."""

        fire_tyre_sets(driver, track)
        first = driver.m_pending_tyre_change
        fire_tyre_sets(driver, track)

        assert driver.m_pending_tyre_change is first

class TestCompletion:
    """Behaviour once every awaited signal has arrived, on both topologies."""

    def test_completes_once_all_awaited_signals_arrive(self, driver, track):
        fire_tyre_sets(driver, track)
        deliver_all_signals(driver, track)

        assert driver.m_pending_tyre_change is None
        assert stint_count(driver) == 2
        assert latest_stint(driver).m_fitted_index == NEW_SET_IDX

    def test_new_stint_seeded_from_new_tyre_wear(self, driver, track):
        """The whole point of the damage wait: never seed the new stint from the old set."""

        fire_tyre_sets(driver, track)
        deliver_all_signals(driver, track)

        seed = latest_stint(driver).m_tyre_wear_history[0]
        assert seed.fl_tyre_wear == NEW_TYRE_WEAR

    def test_damage_packet_before_detection_does_not_satisfy_the_wait(self, driver, track):
        """D arriving before T must not count - it is what the wait exists to exclude."""

        fire_car_damage(driver)
        assert stint_count(driver) == 1

        fire_tyre_sets(driver, track)
        assert driver.m_pending_tyre_change is not None, "pre-detection D must not count"
        assert stint_count(driver) == 1

        deliver_all_signals(driver, track)
        assert stint_count(driver) == 2

class TestNormalTrackOrderings:
    """On a normal track the car damage packet is the only gate."""

    def test_car_damage_alone_completes(self, driver):
        fire_tyre_sets(driver, NORMAL_TRACK)
        fire_car_damage(driver)

        assert driver.m_pending_tyre_change is None
        assert stint_count(driver) == 2

    def test_lap_change_alone_does_not_complete(self, driver):
        fire_tyre_sets(driver, NORMAL_TRACK)
        fire_lap_change(driver)

        assert driver.m_pending_tyre_change is not None
        assert stint_count(driver) == 1

class TestWeirdTrackOrderings:
    """On a weird track both a lap change and a car damage packet are required."""

    def test_car_damage_alone_does_not_complete(self, driver):
        fire_tyre_sets(driver, WEIRD_TRACK)
        fire_car_damage(driver)

        assert driver.m_pending_tyre_change is not None
        assert stint_count(driver) == 1

    def test_t_d_l_completes(self, driver):
        fire_tyre_sets(driver, WEIRD_TRACK)
        fire_car_damage(driver)
        fire_lap_change(driver)

        assert driver.m_pending_tyre_change is None
        assert stint_count(driver) == 2

    def test_t_l_d_completes(self, driver):
        fire_tyre_sets(driver, WEIRD_TRACK)
        fire_lap_change(driver)
        fire_car_damage(driver)

        assert driver.m_pending_tyre_change is None
        assert stint_count(driver) == 2

    def test_old_stint_final_wear_rewritten_to_old_tyre_value(self, driver):
        """The weird-track rewrite: the old stint's last lap keeps the old set's wear."""

        fire_tyre_sets(driver, WEIRD_TRACK)
        fire_car_damage(driver)
        fire_lap_change(driver)

        old_stint = driver.m_tyre_info.m_tyre_set_history_manager.getEntry(index=0)
        assert old_stint.m_tyre_wear_history[-1].fl_tyre_wear == OLD_TYRE_WEAR

class TestPreDetectionLapChange:
    """A lap change that lands before the tyre sets packet is noticed.

    On a normal track this is harmless - no lap change is awaited. On a weird track it is
    the *expected* ordering: the garage sits seconds before the line and the tyre sets
    packet is per-car index cycled, so the line is routinely crossed before the change is
    noticed.
    """

    def test_lap_change_before_detection_still_completes(self, driver, track):
        """The wait is for "a lap boundary passed since the tyres were fitted".

        That is already satisfied here, so the change must complete on the next car damage
        packet rather than a full lap later. Today `awaiting_lap_change` is edge-triggered
        with no memory, so the pre-detection lap change is dropped. Fix: store
        `detected_at_lap` and complete on `m_current_lap > detected_at_lap`.
        """

        fire_lap_change(driver)          # L - arrives before anything is pending
        fire_tyre_sets(driver, track)
        fire_car_damage(driver)

        assert driver.m_pending_tyre_change is None, \
            "a lap boundary already crossed must satisfy the wait"
        assert stint_count(driver) == 2

    def test_new_stint_start_lap_is_the_lap_the_tyres_were_fitted(self, driver, track):
        """Knock-on of the above: a late completion lands `start_lap` a lap out.

        Completion reads `m_current_lap`, so waiting an extra lap also makes
        `overwriteTyreWear(stint_index=-1, lap_index=-1)` patch the wrong lap of the old
        stint. Fixed by the same `detected_at_lap` change.
        """

        fire_lap_change(driver)
        fire_tyre_sets(driver, track)
        fire_car_damage(driver)

        assert latest_stint(driver).m_start_lap == START_LAP + 1

class TestPendingLifetime:
    """Cancellation, replacement and abandonment of a pending change."""

    def test_stuck_pending_change_does_not_suppress_a_later_one(self, driver, track):
        """A pending change whose packets never arrive must not wedge tyre tracking.

        Completion needs a car damage packet, and on weird tracks a lap boundary too. If the
        driver retires or disconnects first, those never come - and because detection is
        suppressed while anything is pending, and the history entry is only added on
        completion, every later change would be dropped for the rest of the session.
        """

        fire_tyre_sets(driver, track)
        assert driver.m_pending_tyre_change.target_idx == NEW_SET_IDX

        # No packets arrive; the set moves on regardless
        fire_tyre_sets(driver, track, fitted_idx=THIRD_SET_IDX, key=THIRD_SET_KEY)
        assert driver.m_pending_tyre_change.target_idx == THIRD_SET_IDX, \
            "a stale pending change must not suppress the set actually fitted now"

        deliver_all_signals(driver, track)
        assert stint_count(driver) == 2
        assert latest_stint(driver).m_fitted_index == THIRD_SET_IDX

    def test_flashback_discards_pending_change(self, driver, track):
        """A flashback rewinds the wear state; a pending change must not outlive it.

        `_handleFlashBack` rewinds the per-lap snapshots, stint history, extrapolator and
        rolling wear buffer, but leaves `m_pending_tyre_change` set - so a stale change
        later completes against rewound state.
        """

        fire_tyre_sets(driver, track)
        driver._handleFlashBack(START_LAP)  # pylint: disable=protected-access

        assert driver.m_pending_tyre_change is None, \
            "a pending change must not complete against rewound state"

class TestTrackUnknown:
    """The first tyre sets packet can arrive before the session packet names the track."""

    def test_unknown_track_is_not_silently_treated_as_normal(self, driver):
        """isFinishLineAfterPitGarage(None) is bare set membership, so None reads as False.

        On a weird track that means the very first change of the session takes the
        normal-track path and skips the old-stint rewrite entirely.
        """

        assert not F1Utils.isFinishLineAfterPitGarage(None)

        fire_tyre_sets(driver, None)
        assert driver.m_pending_tyre_change.is_weird_track is not False, \
            "an unknown track must not be assumed to be a normal track"
