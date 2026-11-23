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

"""Harvest power estimate: which car's MGU-K/MGU-H power estimators are fed. Only the PU overlay reads them, and
only for its reference car: the player's, or the spectated car while spectating."""

# ------------------------- IMPORTS ------------------------------------------------------------------------------------

from typing import List, Optional

import allure
import pytest

from apps.backend.state_mgmt_layer import SessionState
from lib.f1_types import SessionType24, TrackID

from .harness import (ALL_SESSIONS, FP, LAP_TRACK_LENGTHS, QUALI, RACE,
                      TT, InjectingTelemetryManager, racing_status)
from .packet_helpers import (ALL_FORMATS, DriverSpec, Packets, ai, car,
                             fuel_and_ers, player)

# ------------------------- CONSTANTS ----------------------------------------------------------------------------------

UID = 100
TRACK = TrackID.Silverstone
FRAME_MS = 16
HARVEST_PER_FRAME_J = 1_000.0
HARVEST_POWER_W = HARVEST_PER_FRAME_J / FRAME_MS * 1000.0
SPECTATOR_SESSIONS = [FP, QUALI, RACE]  # time trial is single player, so it can't be spectated

pytestmark = [allure.feature("Harvest power estimate"),
              pytest.mark.parametrize("packet_format", ALL_FORMATS, indirect=True)]

# ------------------------- HELPERS ------------------------------------------------------------------------------------

class Grid:
    """A session on UID 100 at Silverstone. Every car is on lap 1, its lap timer and MGU-K harvest climbing at a
    steady rate, one LAP_DATA then one CAR_STATUS per frame, in the game's order."""

    def __init__(self, manager: InjectingTelemetryManager, packets: Packets, session: SessionType24,
                 drivers: List[DriverSpec]) -> None:
        self.manager = manager
        self.packets = packets
        self.session_type = session
        self.drivers = drivers
        self.frame = 0

    async def session(self, *, spectating: int = None) -> None:
        """SESSION, spectating car index spectating if given, then PARTICIPANTS on the first call."""
        await self.manager.inject(self.packets.session(
            session_uid=UID, session_type=self.session_type.name, track=TRACK, total_laps=5,
            track_length=LAP_TRACK_LENGTHS[TRACK],
            is_spectating=spectating is not None, spectator_car_index=255 if spectating is None else spectating))
        if self.frame == 0:
            await self.manager.inject(self.packets.participants(*self.drivers, session_uid=UID))

    async def drive(self, frames: int, *, absent: Optional[int] = None) -> None:
        """frames more frames for every car, except car index absent, which LAP_DATA sends as an empty slot."""
        num_cars = len(self.drivers)
        for _ in range(frames):
            self.frame += 1
            await self.manager.inject(self.packets.lap(
                *[car(index, lap=1, lap_distance=100.0 + self.frame, lap_time_ms=10_000 + self.frame * FRAME_MS,
                      status=racing_status(self.session_type))
                  for index in range(num_cars) if index != absent], session_uid=UID))
            await self.manager.inject(self.packets.car_status(
                *[fuel_and_ers(index, ers_harvested_mguk=self.frame * HARVEST_PER_FRAME_J) for index in range(num_cars)],
                session_uid=UID))


def _tracked(state: SessionState) -> List[int]:
    """Indices of the cars whose estimators hold a full window."""
    return [index for index, driver in enumerate(state.m_driver_data)
            if driver and driver.m_car_info.m_harv_mguk_power_est.is_valid()]

# ------------------------- TESTS --------------------------------------------------------------------------------------

@allure.story("Reference car")
@pytest.mark.parametrize("session", ALL_SESSIONS)
@allure.title("Player mode: only the player's car is estimated ({session}, {packet_format})")
async def test_player_mode_estimates_only_the_player(manager: InjectingTelemetryManager, packets: Packets,
                                                     state: SessionState, session: SessionType24) -> None:
    """Practice, quali or race with the player on car 0 and two AI cars, or time trial with the player alone, every
    car harvesting at the same steady rate for a full filter window and more.

    Expected: only car 0's estimators are fed, and its MGU-K estimate is the harvest rate."""
    drivers = [player("Player")] if session == TT else [player("Player"), ai("AI 1"), ai("AI 2")]
    grid = Grid(manager, packets, session, drivers)
    await grid.session()
    await grid.drive(state.m_power_filter_window_size + 5)

    assert _tracked(state) == [0]
    assert state.m_driver_data[0].m_car_info.getPowerEstimates()[0] == pytest.approx(HARVEST_POWER_W)


@allure.story("Reference car")
@pytest.mark.parametrize("session", SPECTATOR_SESSIONS)
@allure.title("Spectating: only the spectated car is estimated ({session}, {packet_format})")
async def test_spectating_estimates_only_the_spectated_car(manager: InjectingTelemetryManager, packets: Packets,
                                                           state: SessionState, session: SessionType24) -> None:
    """Practice, quali or race spectated as in f1_24_mp_spectator_bahrain: player car index 255 in every header,
    SESSION with is_spectating on car 1, three cars harvesting at the same steady rate for a full filter window and
    more.

    Expected: only car 1's estimators are fed, and its MGU-K estimate is the harvest rate."""
    packets.player_index = 255
    grid = Grid(manager, packets, session, [player("Host"), player("Guest"), ai("AI")])
    await grid.session(spectating=1)
    await grid.drive(state.m_power_filter_window_size + 5)

    assert _tracked(state) == [1]
    assert state.m_driver_data[1].m_car_info.getPowerEstimates()[0] == pytest.approx(HARVEST_POWER_W)


@allure.story("Reference car")
@pytest.mark.parametrize("session", SPECTATOR_SESSIONS)
@allure.title("Spectating: switching back to a car restarts its estimate ({session}, {packet_format})")
async def test_spectator_switch_restarts_the_estimate(manager: InjectingTelemetryManager, packets: Packets,
                                                      state: SessionState, session: SessionType24) -> None:
    """Spectated practice, quali or race. The spectated car goes 1 -> 0 -> 1, a full filter window on each, as the
    spectator cycles between cars in f1_24_mp_spectator_bahrain (1 -> 2 -> 0 -> 1 -> 2 -> 0 within 10 s, overall
    frames 9475 to 10259). The SESSION carrying each switch comes between frames.

    Expected: one frame after switching back to car 1, its estimate is not reported, since its window holds samples
    from before car 0's stint. A full window later it is the harvest rate again."""
    packets.player_index = 255
    grid = Grid(manager, packets, session, [player("Host"), player("Guest"), ai("AI")])
    window = state.m_power_filter_window_size
    await grid.session(spectating=1)
    await grid.drive(window + 5)
    await grid.session(spectating=0)
    await grid.drive(window + 5)
    assert 0 in _tracked(state)

    await grid.session(spectating=1)
    await grid.drive(1)
    assert 1 not in _tracked(state)
    assert state.m_driver_data[1].m_car_info.getPowerEstimates() == (0.0, 0.0)

    await grid.drive(window)
    assert 1 in _tracked(state)
    assert state.m_driver_data[1].m_car_info.getPowerEstimates()[0] == pytest.approx(HARVEST_POWER_W)


@allure.story("Reference car")
@pytest.mark.parametrize("session", SPECTATOR_SESSIONS)
@allure.title("Spectating: no estimate from an earlier stint between the switching SESSION and lap data "
              "({session}, {packet_format})")
async def test_spectator_switch_reports_no_old_stint_before_lap_data(manager: InjectingTelemetryManager,
                                                                     packets: Packets, state: SessionState,
                                                                     session: SessionType24) -> None:
    """Spectated practice, quali or race. The spectated car goes 1 -> 0 -> 1, a full filter window on each. The
    estimate is read for the reference car, as the PU overlay picks it, straight after the SESSION switching back to
    car 1 and before the next LAP_DATA. The PU overlay can publish in that gap.

    Expected: the reference is car 1 at once, and its estimate is not reported: its filter was emptied when car 0
    took over, so nothing from car 1's first stint is left to read."""
    packets.player_index = 255
    grid = Grid(manager, packets, session, [player("Host"), player("Guest"), ai("AI")])
    window = state.m_power_filter_window_size
    await grid.session(spectating=1)
    await grid.drive(window + 5)
    await grid.session(spectating=0)
    await grid.drive(window + 5)

    await grid.session(spectating=1)
    assert state.ref_index == 1
    assert state.ref_index not in _tracked(state)
    assert state.m_driver_data[state.ref_index].m_car_info.getPowerEstimates() == (0.0, 0.0)


@allure.story("Reference car")
@pytest.mark.parametrize("session", SPECTATOR_SESSIONS)
@allure.title("Spectating: switching to a car missing from that frame's lap data still restarts it "
              "({session}, {packet_format})")
async def test_spectator_switch_to_absent_car_restarts_the_estimate(manager: InjectingTelemetryManager,
                                                                    packets: Packets, state: SessionState,
                                                                    session: SessionType24) -> None:
    """Spectated practice, quali or race. The spectated car goes 1 -> 0 -> 1, a full filter window on each. On the
    first LAP_DATA after switching back, car 1's slot is empty (INVALID result status), then it comes back. No
    recording has a switch onto an empty slot; the sequence is built.

    Expected: one frame after car 1 is back, its estimate is not reported, since its window holds samples from
    before car 0's stint. A full window later it is the harvest rate again."""
    packets.player_index = 255
    grid = Grid(manager, packets, session, [player("Host"), player("Guest"), ai("AI")])
    window = state.m_power_filter_window_size
    await grid.session(spectating=1)
    await grid.drive(window + 5)
    await grid.session(spectating=0)
    await grid.drive(window + 5)

    await grid.session(spectating=1)
    await grid.drive(1, absent=1)
    await grid.drive(1)
    assert 1 not in _tracked(state)
    assert state.m_driver_data[1].m_car_info.getPowerEstimates() == (0.0, 0.0)

    await grid.drive(window)
    assert state.m_driver_data[1].m_car_info.getPowerEstimates()[0] == pytest.approx(HARVEST_POWER_W)
