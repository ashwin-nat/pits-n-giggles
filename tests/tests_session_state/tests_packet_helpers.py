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

"""Checks on the harness itself: every packet helper builds a packet the handler accepts, with the fields it was
given, and the FakeSubsystem controls behave as documented."""

# ------------------------- IMPORTS ------------------------------------------------------------------------------------

import asyncio
from typing import Optional

import allure
import pytest

from lib.f1_types import (PacketEventData, PacketSessionData, TelemetrySetting,
                          TrackID)
from lib.f1_types.common import get_num_cars
from lib.f1_types.packet_2_lap_data import LapData

from .harness import FakeSubsystem, InjectingTelemetryManager, ProcessCall, SaveRecorder
from .packet_helpers import (ALL_FORMATS, Packets, ai, car, classified,
                             fuel_and_ers, lap_time, player, speed,
                             world_position)

pytestmark = allure.feature("Harness")

# ------------------------- HELPERS ------------------------------------------------------------------------------------

UID = 100
FORMAT_SWEEP = pytest.mark.parametrize("packet_format", ALL_FORMATS, indirect=True)


async def _start(manager: InjectingTelemetryManager, packets: Packets) -> None:
    """A valid race session with a player and an AI car."""
    await manager.inject(packets.session(session_uid=UID, session_type="RACE", track=TrackID.Silverstone,
                                         total_laps=5, track_length=5891))
    await manager.inject(packets.participants(player("Player"), ai("Opponent"), session_uid=UID))

# ------------------------- PACKET HELPERS -----------------------------------------------------------------------------

@allure.story("Packet helpers")
@FORMAT_SWEEP
@pytest.mark.parametrize("session_type", ["RACE", "SHORT_QUALIFYING", "TIME_TRIAL"])
async def test_session_sets_its_fields(manager: InjectingTelemetryManager, packets: Packets, session_type: str) -> None:
    packet = packets.session(session_uid=UID, session_type=session_type, track=TrackID.Monaco, total_laps=3,
                             track_length=3337, formula=PacketSessionData.FormulaType.F2, is_spectating=True)
    await manager.inject(packet)

    assert packet.m_sessionType.name == session_type
    assert (packet.m_trackId, packet.m_totalLaps, packet.m_trackLength) == (TrackID.Monaco, 3, 3337)
    assert packet.m_formula == PacketSessionData.FormulaType.F2
    assert packet.m_isSpectating is True


@allure.story("Packet helpers")
@FORMAT_SWEEP
async def test_participants_set_ai_and_telemetry(manager: InjectingTelemetryManager, packets: Packets) -> None:
    packet = packets.participants(player("Player", TelemetrySetting.RESTRICTED), ai("Opponent"), session_uid=UID)
    await manager.inject(packet)

    assert packet.m_numActiveCars == 2
    assert len(packet.m_participants) == get_num_cars(packets.packet_format)
    assert (packet.m_participants[0].m_aiControlled, packet.m_participants[0].m_yourTelemetry) == \
        (False, TelemetrySetting.RESTRICTED)
    assert (packet.m_participants[1].m_aiControlled, packet.m_participants[1].m_yourTelemetry) == \
        (True, TelemetrySetting.PUBLIC)


@allure.story("Packet helpers")
@FORMAT_SWEEP
async def test_lap_sets_status_lap_time_and_a_negative_distance(manager: InjectingTelemetryManager,
                                                                packets: Packets) -> None:
    await _start(manager, packets)
    packet = packets.lap(car(0, lap=1, lap_distance=-120.5, status=LapData.DriverStatus.OUT_LAP, lap_time_ms=1234),
                         session_uid=UID)
    await manager.inject(packet)

    entry = packet.m_lapData[0]
    assert (entry.m_currentLapNum, entry.m_lapDistance, entry.m_currentLapTimeInMS) == (1, -120.5, 1234)
    assert entry.m_driverStatus == LapData.DriverStatus.OUT_LAP


@allure.story("Packet helpers")
@FORMAT_SWEEP
async def test_car_status_sets_fuel_and_ers(manager: InjectingTelemetryManager, packets: Packets) -> None:
    await _start(manager, packets)
    packet = packets.car_status(fuel_and_ers(0, fuel_in_tank=5.5, ers_harvested_mguk=1_000_000.0,
                                             ers_deployed=2_000_000.0), session_uid=UID)
    await manager.inject(packet)

    entry = packet.m_carStatusData[0]
    assert (entry.m_fuelInTank, entry.m_ersHarvestedThisLapMGUK, entry.m_ersDeployedThisLap) == \
        (5.5, 1_000_000.0, 2_000_000.0)
    assert packet.m_carStatusData[1].m_fuelInTank == 0.0


@allure.story("Packet helpers")
@FORMAT_SWEEP
async def test_car_telemetry_sets_speed(manager: InjectingTelemetryManager, packets: Packets) -> None:
    await _start(manager, packets)
    packet = packets.car_telemetry(speed(0, 283), session_uid=UID)
    await manager.inject(packet)

    assert packet.m_carTelemetryData[0].m_speed == 283
    assert packet.m_carTelemetryData[1].m_speed == 0


@allure.story("Packet helpers")
@FORMAT_SWEEP
async def test_motion_sets_position_and_yaw(manager: InjectingTelemetryManager, packets: Packets) -> None:
    await _start(manager, packets)
    packet = packets.motion(world_position(0, x=1.5, y=2.5, z=3.5, yaw=0.75), session_uid=UID)
    await manager.inject(packet)

    entry = packet.m_carMotionData[0]
    assert (entry.m_worldPositionX, entry.m_worldPositionY, entry.m_worldPositionZ, entry.m_yaw) == \
        (1.5, 2.5, 3.5, 0.75)


# Looked up by event type: a details object shows in Allure as its repr, whose address changes every run
EVENT_DETAILS = {
    PacketEventData.EventPacketType.FLASHBACK: PacketEventData.Flashback.from_values(frame_identifier=7),
    PacketEventData.EventPacketType.BUTTON_STATUS:
        PacketEventData.Buttons.from_status(PacketEventData.Buttons.udp_action_flag(5)),
    PacketEventData.EventPacketType.OVERTAKE: PacketEventData.Overtake.from_values(1, 0),
    PacketEventData.EventPacketType.SESSION_ENDED: None,
    PacketEventData.EventPacketType.SESSION_STARTED: None,
    PacketEventData.EventPacketType.SPEED_TRAP_TRIGGERED: PacketEventData.SpeedTrap.from_values(0, 321.5),
}


@allure.story("Packet helpers")
@FORMAT_SWEEP
@pytest.mark.parametrize("event_type", list(EVENT_DETAILS), ids=["FLBK", "BUTN", "OVTK", "SEND", "SSTA", "SPTP"])
async def test_event_carries_its_details(manager: InjectingTelemetryManager, packets: Packets,
                                         event_type: PacketEventData.EventPacketType) -> None:
    details: Optional[object] = EVENT_DETAILS[event_type]
    await _start(manager, packets)
    packet = packets.event(event_type, details, session_uid=UID)
    await manager.inject(packet)

    assert packet.m_eventCode == event_type
    assert packet.mEventDetails is details


@allure.story("Packet helpers")
@FORMAT_SWEEP
async def test_final_classification_sets_laps_per_car(manager: InjectingTelemetryManager, packets: Packets,
                                                      saves: SaveRecorder) -> None:
    await _start(manager, packets)
    await manager.inject(packets.lap(car(0, lap=5, lap_distance=5800.0), car(1, lap=4, lap_distance=5800.0),
                                     session_uid=UID))
    packet = packets.final_classification(classified(position=1, num_laps=5), classified(position=2, num_laps=4),
                                          session_uid=UID)
    await manager.inject(packet)

    assert [entry.m_numLaps for entry in packet.m_classificationData] == [5, 4]
    assert len(saves.requests) == 1


@allure.story("Packet helpers")
async def test_drive_counts_frames_up(packets: Packets) -> None:
    lap_packets = packets.drive(0, lap=2, distances=[10.0, 20.0, 30.0], session_uid=UID)

    frames = [packet.m_header.m_overallFrameIdentifier for packet in lap_packets]
    assert frames == sorted(set(frames)) and len(frames) == 3
    assert [packet.m_lapData[0].m_lapDistance for packet in lap_packets] == [10.0, 20.0, 30.0]
    assert {packet.m_lapData[0].m_currentLapNum for packet in lap_packets} == {2}


@allure.story("Packet helpers")
@FORMAT_SWEEP
async def test_session_history_burst_covers_the_grid_on_one_frame(manager: InjectingTelemetryManager,
                                                                  packets: Packets) -> None:
    await _start(manager, packets)
    burst = packets.session_history_burst(laps=[lap_time(92_000, valid=True)], session_uid=UID, overall_frame=50)
    for packet in burst:
        await manager.inject(packet)

    assert [packet.m_carIdx for packet in burst] == list(range(get_num_cars(packets.packet_format)))
    assert {packet.m_header.m_overallFrameIdentifier for packet in burst} == {50}

# ------------------------- FAKE SUBSYSTEM -----------------------------------------------------------------------------

def _write(path: str, *, mode: str) -> None:
    raise AssertionError("run_in_process must not run fn")


@allure.story("Fake subsystem")
async def test_run_in_process_records_the_call_and_resolves() -> None:
    subsystem = FakeSubsystem()

    assert await subsystem.run_in_process(_write, "out.pngt", mode="w") is None
    assert subsystem.process_calls == [ProcessCall(fn_name="_write", args=("out.pngt",), kwargs={"mode": "w"})]


@allure.story("Fake subsystem")
async def test_run_in_process_block_holds_calls_until_release() -> None:
    subsystem = FakeSubsystem()
    subsystem.block()
    first = asyncio.ensure_future(subsystem.run_in_process(_write, "a", mode="w"))
    second = asyncio.ensure_future(subsystem.run_in_process(_write, "b", mode="w"))
    await asyncio.sleep(0)
    assert not first.done() and not second.done()

    subsystem.release()
    assert await first is None and await second is None
    assert await subsystem.run_in_process(_write, "c", mode="w") is None, "release stops holding new calls"


@allure.story("Fake subsystem")
async def test_run_in_process_fail_with_raises_once() -> None:
    subsystem = FakeSubsystem()
    subsystem.fail_with(OSError("disk full"))

    with pytest.raises(OSError, match="disk full"):
        await subsystem.run_in_process(_write, "a", mode="w")
    assert await subsystem.run_in_process(_write, "b", mode="w") is None
