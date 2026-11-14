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

"""Session handling scenarios: F1TelemetryHandler's session UID gate, its same-UID restart check, and the saves
they request. The packet sequences are from the test_data/ recordings: every session ends with SEND, then
SESSION_HISTORY bursts and FINAL_CLASSIFICATION, all on overall frame 0.
"""

# ------------------------- IMPORTS ------------------------------------------------------------------------------------

import asyncio

import allure
import pytest

from apps.backend.state_mgmt_layer import SessionState
from apps.backend.telemetry_layer.telemetry_handler import F1TelemetryHandler
from lib.f1_types import PacketEventData, SessionType24, TrackID
from lib.f1_types.packet_2_lap_data import LapData

from .harness import (ALL_SESSIONS, FP, LAP_TRACKS, QUALI, RACE, FakeSubsystem,
                      InjectingTelemetryManager, PlayerCar, SaveRecorder,
                      SaveRequestRecord, TokenRecorder, racing_status, title)
from .packet_helpers import (ALL_FORMATS, FIRST_SOFT_IDX, Packets, ai, car,
                             classified, lap_time, player)

# ------------------------- CONSTANTS ----------------------------------------------------------------------------------

UID, NEXT_UID = 100, 200
ON_TRACK = LapData.DriverStatus.ON_TRACK

# The JSON and the .pngt, both requested on FINAL_CLASSIFICATION for UID 100
FINAL_SAVES = [SaveRequestRecord("final_classification", "json", UID),
               SaveRequestRecord("final_classification", "pngt", UID)]
JUST_IN_CASE_SAVES = [SaveRequestRecord("just_in_case", "json", UID),
                      SaveRequestRecord("just_in_case", "pngt", UID)]

pytestmark = allure.feature("Session handling")

# ------------------------- FIXTURES -----------------------------------------------------------------------------------

@pytest.fixture(params=LAP_TRACKS)
def track(request: pytest.FixtureRequest) -> TrackID:
    """Both track topologies."""
    return request.param

# ------------------------- HELPERS ------------------------------------------------------------------------------------

async def _session_in_progress(manager: InjectingTelemetryManager, packets: Packets, session_uid: int,
                               session: SessionType24 = RACE) -> None:
    """A session at Silverstone on session_uid: two cars, one lap in progress, a lap history for the player."""
    await manager.inject(packets.session(session_uid=session_uid, session_type=session.name,
                                         track=TrackID.Silverstone, total_laps=5, track_length=5891))
    await manager.inject(packets.participants(player("Player"), ai("Opponent"), session_uid=session_uid))
    await manager.inject(packets.lap(car(0, lap=1, lap_distance=1000, status=racing_status(session)),
                                     car(1, lap=1, lap_distance=900, status=racing_status(session)),
                                     session_uid=session_uid))
    await manager.inject(packets.session_history(car_idx=0, laps=[lap_time(92_000, valid=True)],
                                                 session_uid=session_uid))


async def _session_end(manager: InjectingTelemetryManager, packets: Packets, session_uid: int) -> None:
    """SEND, menu button events on UID 0, a SESSION_HISTORY for every car and FINAL_CLASSIFICATION, all on overall
    frame 0 (as in f1_25_mp_coop_quali_australia)."""
    await manager.inject(packets.event(PacketEventData.EventPacketType.SESSION_ENDED, None,
                                       session_uid=session_uid, overall_frame=0))
    for _ in range(3):
        await manager.inject(packets.event(
            PacketEventData.EventPacketType.BUTTON_STATUS,
            PacketEventData.Buttons.from_status(PacketEventData.Buttons.udp_action_flag(5)),
            session_uid=0, overall_frame=0))
    for packet in packets.session_history_burst(laps=[lap_time(92_000, valid=True)], session_uid=session_uid,
                                                overall_frame=0):
        await manager.inject(packet)
    await manager.inject(packets.final_classification(classified(position=1, num_laps=5),
                                                      classified(position=2, num_laps=5),
                                                      session_uid=session_uid, overall_frame=0))


def _is_cleared(state: SessionState) -> bool:
    return state.m_session_info.m_session_uid is None and all(driver is None for driver in state.m_driver_data)

# ------------------------- SESSION UID CHANGE -------------------------------------------------------------------------

@allure.story("Session UID change")
@pytest.mark.parametrize("packet_format", ALL_FORMATS, indirect=True)
@allure.title("A UID change clears the state and saves the old session just in case (Race, {packet_format})")
async def test_uid_change_clears_and_saves_just_in_case(manager: InjectingTelemetryManager, packets: Packets,
                                                        state: SessionState, handler: F1TelemetryHandler,
                                                        saves: SaveRecorder, tokens: TokenRecorder) -> None:
    """Race on UID 100 with lap data and no FINAL_CLASSIFICATION, then a LAP_DATA on UID 200.

    Expected: a just-in-case JSON and .pngt are requested for UID 100, then the state is cleared for UID 200."""
    await _session_in_progress(manager, packets, UID)
    assert state.has_lap_data
    assert saves.requests == []

    await manager.inject(packets.lap(car(0, lap=1, lap_distance=10), session_uid=NEXT_UID))

    assert saves.requests == JUST_IN_CASE_SAVES
    assert tokens.records == []
    assert handler.m_last_session_uid == NEXT_UID
    assert _is_cleared(state)


@allure.story("Session UID change")
@allure.title("A UID change after FINAL_CLASSIFICATION skips the just-in-case save (Race, {packet_format})")
async def test_uid_change_after_final_classification_skips_just_in_case(
        manager: InjectingTelemetryManager, packets: Packets, state: SessionState, handler: F1TelemetryHandler,
        saves: SaveRecorder, tokens: TokenRecorder) -> None:
    """Race on UID 100 to FINAL_CLASSIFICATION, and its saves finish. Then a LAP_DATA on UID 200.

    Expected: only the final classification's saves. The state is cleared for UID 200."""
    await _session_in_progress(manager, packets, UID)
    await manager.inject(packets.final_classification(classified(position=1, num_laps=5),
                                                      classified(position=2, num_laps=5), session_uid=UID))
    assert saves.requests == FINAL_SAVES
    await asyncio.sleep(0)      # the saves finish, so no save task is running when UID 200 arrives

    await manager.inject(packets.lap(car(0, lap=1, lap_distance=10), session_uid=NEXT_UID))

    assert saves.requests == FINAL_SAVES
    assert tokens.records == []
    assert handler.m_last_session_uid == NEXT_UID
    assert all(driver is None for driver in state.m_driver_data)


@allure.story("Session UID change")
@pytest.mark.parametrize("packet_format", ALL_FORMATS, indirect=True)
@pytest.mark.parametrize("session", [FP, QUALI, RACE])
@allure.title("A SESSION_HISTORY burst on UID 0 mid-session doesn't clear it ({session}, {packet_format})")
async def test_menu_packets_on_uid_0_do_not_clear(manager: InjectingTelemetryManager, packets: Packets,
                                                  state: SessionState, handler: F1TelemetryHandler,
                                                  saves: SaveRecorder, session: SessionType24) -> None:
    """Practice, quali or race on UID 100. Then a SESSION_HISTORY for every car on UID 0, and UID 100 carries on at
    the next frame, as in every multiplayer recording (f1_25_mp_coop_race_australia at overall frame 126066).

    Expected: UID 0 is ignored by the gate, so nothing is cleared or saved."""
    await _session_in_progress(manager, packets, UID, session)
    for packet in packets.session_history_burst(laps=[lap_time(92_000, valid=True)], session_uid=0,
                                                overall_frame=manager.injected[-1].m_header.m_overallFrameIdentifier):
        await manager.inject(packet)
    await manager.inject(packets.lap(car(0, lap=1, lap_distance=1100, status=racing_status(session)),
                                     session_uid=UID))

    assert saves.requests == []
    assert handler.m_last_session_uid == UID
    assert state.m_session_info.m_session_uid == UID
    assert state.m_driver_data[0].m_packet_copies.m_packet_lap_data.m_lapDistance == 1100


@allure.story("Session UID change")
@pytest.mark.parametrize("packet_format", ALL_FORMATS, indirect=True)
@pytest.mark.parametrize("session", ALL_SESSIONS)
# TODO: no capture has UID-0 button events mid-session (only after SEND). Check the UID 0 case against a new
# recording of a pause and menu navigation, and fix its session list and sequence to match.
@pytest.mark.parametrize("button_uid", [0, UID], ids=["UID 0", "session UID"])
@allure.title("Button events while paused don't clear the session (UID {button_uid}, {session}, {packet_format})")
async def test_button_events_while_paused_do_not_clear(manager: InjectingTelemetryManager, packets: Packets,
                                                       state: SessionState, handler: F1TelemetryHandler,
                                                       saves: SaveRecorder, session: SessionType24,
                                                       button_uid: int) -> None:
    """Any session type on UID 100. Then 4 BUTTON_STATUS events on the paused frame, on UID 0 (menus) or on UID 100
    (f1_26_sp_madring_ragequit at overall frame 161042), and UID 100 carries on at the next frame.

    Expected: nothing is cleared or saved."""
    await _session_in_progress(manager, packets, UID, session)
    paused_frame = manager.injected[-1].m_header.m_overallFrameIdentifier
    for _ in range(4):
        await manager.inject(packets.event(
            PacketEventData.EventPacketType.BUTTON_STATUS,
            PacketEventData.Buttons.from_status(PacketEventData.Buttons.udp_action_flag(5)),
            session_uid=button_uid, overall_frame=paused_frame))
    await manager.inject(packets.lap(car(0, lap=1, lap_distance=1100, status=racing_status(session)),
                                     session_uid=UID))

    assert saves.requests == []
    assert handler.m_last_session_uid == UID
    assert state.m_session_info.m_session_uid == UID
    assert state.m_driver_data[0].m_packet_copies.m_packet_lap_data.m_lapDistance == 1100

# ------------------------- SAME-UID RESTART ---------------------------------------------------------------------------

@allure.story("Same-UID restart")
@pytest.mark.parametrize("packet_format", ALL_FORMATS, indirect=True)
@pytest.mark.parametrize("session", [RACE])
@title("A race restarted on the same UID is cleared, saved just in case and recorded afresh")
async def test_same_uid_race_restart_clears_and_saves_the_aborted_start(
        player_car: PlayerCar, session: SessionType24, manager: InjectingTelemetryManager, packets: Packets,
        state: SessionState, saves: SaveRecorder) -> None:
    """Race, as in f1_25_mp_coop_race_australia: the aborted start runs to lap 3 on UID 100. Then a SESSION_HISTORY
    burst on UID 0, SEND on UID 100, button events on UID 0 and SSTA on UID 100, all on overall frame 0. The
    restarted race's LAP_DATA starts the overall frame count over.

    Expected: the restart's first LAP_DATA requests a just-in-case JSON and .pngt for UID 100 and clears the state.
    The restarted race's laps are then recorded with their own fuel (lap 1 ends at 48.254 kg, not 47.833)."""
    await player_car.session(session)
    await player_car.baseline(ON_TRACK, -20.4, fuel=49.5, wear=0.0, fitted_idx=FIRST_SOFT_IDX)
    await player_car.drive(ON_TRACK, 1, 2600.0)
    await player_car.car_status(fuel=47.833)
    await player_car.drive(ON_TRACK, 2, 1.2, 2600.0)
    await player_car.car_status(fuel=46.139)
    await player_car.drive(ON_TRACK, 3, 1.0, 1500.0)
    await manager.inject(packets.session_history(car_idx=0, laps=[lap_time(84_000, valid=True)] * 2, session_uid=UID))
    assert set(player_car.completed_laps()) == {1, 2}
    assert player_car.fuel(1) == 47.833

    with allure.step("Back to the grid: SEND, menu buttons and SSTA, on overall frame 0"):
        for packet in packets.session_history_burst(laps=[lap_time(92_000, valid=True)], session_uid=0,
                                                    overall_frame=manager.injected[-1].m_header.m_overallFrameIdentifier):
            await manager.inject(packet)
        await manager.inject(packets.event(PacketEventData.EventPacketType.SESSION_ENDED, None,
                                           session_uid=UID, overall_frame=0))
        for _ in range(3):
            await manager.inject(packets.event(
                PacketEventData.EventPacketType.BUTTON_STATUS,
                PacketEventData.Buttons.from_status(PacketEventData.Buttons.udp_action_flag(5)),
                session_uid=0, overall_frame=0))
        await manager.inject(packets.event(PacketEventData.EventPacketType.SESSION_STARTED, None,
                                           session_uid=UID, overall_frame=0))
    assert saves.requests == []

    packets.restart_frames()
    await player_car.drive(ON_TRACK, 1, -20.4)

    assert saves.requests == JUST_IN_CASE_SAVES
    assert _is_cleared(state)

    await player_car.session(session)
    await player_car.baseline(ON_TRACK, -20.4, fuel=49.5, wear=0.0, fitted_idx=FIRST_SOFT_IDX)
    await player_car.drive(ON_TRACK, 1, 2600.0)
    await player_car.car_status(fuel=48.254)
    await player_car.drive(ON_TRACK, 2, 0.8, 2600.0)
    await player_car.car_status(fuel=46.529)
    await player_car.drive(ON_TRACK, 3, 0.4)

    assert player_car.completed_laps() == {1: [-20.4, 2600.0], 2: [0.8, 2600.0]}
    assert (player_car.fuel(1), player_car.fuel(2)) == (48.254, 46.529)
    assert saves.requests == JUST_IN_CASE_SAVES


@allure.story("Same-UID restart")
@pytest.mark.parametrize("packet_format", ALL_FORMATS, indirect=True)
@pytest.mark.parametrize("session", ALL_SESSIONS)
@allure.title("A normal session end isn't taken for a restart ({session}, {packet_format})")
async def test_normal_session_end_does_not_clear_before_final_classification(
        manager: InjectingTelemetryManager, packets: Packets, state: SessionState, saves: SaveRecorder,
        session: SessionType24) -> None:
    """Any session type on UID 100. Then SEND, menu button events on UID 0, a SESSION_HISTORY for every car and
    FINAL_CLASSIFICATION, all on overall frame 0, twice over, as the game repeats them after the end.

    Expected: nothing is cleared. One final classification save is requested, with the session's data."""
    await _session_in_progress(manager, packets, UID, session)
    await _session_end(manager, packets, UID)
    await _session_end(manager, packets, UID)

    assert saves.requests == FINAL_SAVES
    assert state.m_session_info.m_session_uid == UID
    assert state.m_driver_data[0].m_packet_copies.m_packet_lap_data.m_lapDistance == 1000


@allure.story("Same-UID restart")
@pytest.mark.parametrize("packet_format", ALL_FORMATS, indirect=True)
@pytest.mark.parametrize("session", ALL_SESSIONS)
@allure.title("A late LAP_DATA without SEND isn't a restart ({session}, {packet_format})")
async def test_late_lap_data_without_send_is_not_a_restart(manager: InjectingTelemetryManager, packets: Packets,
                                                           state: SessionState, saves: SaveRecorder,
                                                           session: SessionType24) -> None:
    """Any session type on UID 100. LAP_DATA on overall frames 1000 and 1001, then 999, a UDP packet arriving late.

    Expected: the overall frame went back, but there was no SEND, so nothing is cleared or saved."""
    await _session_in_progress(manager, packets, UID, session)
    for frame, distance in ((1000, 1100), (1001, 1110), (999, 1090)):
        await manager.inject(packets.lap(car(0, lap=1, lap_distance=distance, status=racing_status(session)),
                                         session_uid=UID, overall_frame=frame))

    assert saves.requests == []
    assert state.m_session_info.m_session_uid == UID
    assert state.m_driver_data[0].m_packet_copies.m_packet_lap_data.m_lapDistance == 1090

# ------------------------- FINAL CLASSIFICATION -----------------------------------------------------------------------

@allure.story("Final classification")
@pytest.mark.parametrize("packet_format", ALL_FORMATS, indirect=True)
@allure.title("FINAL_CLASSIFICATION before any LAP_DATA still saves (Race, {packet_format})")
async def test_final_classification_before_any_lap_data(manager: InjectingTelemetryManager, packets: Packets,
                                                        state: SessionState, saves: SaveRecorder) -> None:
    """Race with SESSION and PARTICIPANTS only, then FINAL_CLASSIFICATION.

    Expected: no car has a speed trap reading, and the final classification save still works."""
    await manager.inject(packets.session(session_uid=UID, session_type="RACE", track=TrackID.Silverstone,
                                         total_laps=5, track_length=5891))
    await manager.inject(packets.participants(player("Player"), ai("Opponent"), session_uid=UID))
    await manager.inject(packets.final_classification(classified(position=1, num_laps=5),
                                                      classified(position=2, num_laps=5), session_uid=UID))

    assert saves.requests == FINAL_SAVES
    expected = [] if packets.packet_format == 2023 else ["Player", "Opponent"]   # 2023 has no speed trap records
    assert [r["name"] for r in state.buildFinalClassificationJSON()["speed-trap-records"]] == expected


@allure.story("Final classification")
@pytest.mark.parametrize("packet_format", ALL_FORMATS, indirect=True)
@pytest.mark.parametrize("session", ALL_SESSIONS)
@pytest.mark.parametrize("next_packet", ["SESSION", "SSTA"])
@allure.title("The final save keeps its session's name when the next UID arrives first "
              "({session}, next UID on {next_packet}, {packet_format})")
async def test_final_save_keeps_its_session_name_when_the_next_uid_arrives_first(
        manager: InjectingTelemetryManager, packets: Packets, state: SessionState, saves: SaveRecorder,
        session: SessionType24, next_packet: str) -> None:
    """Any session type at Silverstone on UID 100 to FINAL_CLASSIFICATION. Before the save tasks run, UID 200
    arrives on a Race SESSION at Austria, or on an SSTA, which carries no event info.

    Expected: UID 200 clears the state, but the saves were named and filled at FINAL_CLASSIFICATION. The JSON has
    UID 100's name, session UID and packet count, and the .pngt UID 100's name."""
    await _session_in_progress(manager, packets, UID, session)
    state.m_pkt_count = 4321        # counted on the raw-packet path, which inject() skips
    await manager.inject(packets.final_classification(classified(position=1, num_laps=5),
                                                      classified(position=2, num_laps=5), session_uid=UID))
    name = state.getEventInfoStr()

    if next_packet == "SESSION":
        await manager.inject(packets.session(session_uid=NEXT_UID, session_type="RACE", track=TrackID.Austria,
                                             total_laps=5, track_length=4318))
    else:
        await manager.inject(packets.event(PacketEventData.EventPacketType.SESSION_STARTED, None,
                                           session_uid=NEXT_UID))
    assert state.m_session_info.m_session_uid in (None, NEXT_UID)
    assert (saves.json_debug, saves.pngt_names) == ([], [])

    await asyncio.sleep(0)      # the save tasks run

    assert saves.requests == FINAL_SAVES
    assert [(debug["file-name"].startswith(name), debug["session-uid"], debug["packet-count"])
            for debug in saves.json_debug] == [(True, UID, 4321)]
    assert [pngt.startswith(name) for pngt in saves.pngt_names] == [True]

# ------------------------- HANDLER WIRING -----------------------------------------------------------------------------

@allure.story("Handler wiring")
@allure.title("register_tasks needs an async telemetry manager")
async def test_register_tasks_needs_an_async_manager(handler: F1TelemetryHandler,
                                                     fake_subsystem: FakeSubsystem) -> None:
    """The handler on the harness's InjectingTelemetryManager.

    Expected: register_tasks refuses it. The receive loop and raw-packet wiring only exist on
    AsyncF1TelemetryManager."""
    with pytest.raises(TypeError, match="needs an AsyncF1TelemetryManager, got InjectingTelemetryManager"):
        handler.register_tasks(fake_subsystem)
