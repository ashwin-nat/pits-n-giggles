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

"""Unified save scenarios (Capture.unified_save_format): one SaveRequest snapshot per save, written as one .pngt
container by a task in m_save_tasks. Writes are read back from FakeSubsystem.run_in_process, which records each
write_container call and can hold or fail it."""

# Fixtures that take other fixtures as arguments are how pytest works, not shadowing
# pylint: disable=redefined-outer-name
# [write] = _writes(...) asserts there is exactly one write
# pylint: disable=unbalanced-tuple-unpacking

# ------------------------- IMPORTS ------------------------------------------------------------------------------------

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import allure
import pytest

from apps.backend.intf_layer.ipc.command_handlers import handleManualSave
from apps.backend.state_mgmt_layer import SessionState
from apps.backend.state_mgmt_layer import save_request as save_request_module
from apps.backend.state_mgmt_layer.save_request import SaveReason
from apps.backend.telemetry_layer.telemetry_handler import F1TelemetryHandler
from lib.config import LapAnalyzerSensorSettings, PngSettings
from lib.f1_types import PacketEventData, SessionType24, TrackID

from .harness import (ALL_SESSIONS, FP, QUALI, RACE, TT, FakeSubsystem,
                      InjectingTelemetryManager, SaveRecorder,
                      SaveRequestRecord, TokenRecorder, racing_status)
from .packet_helpers import Packets, ai, car, classified, lap_time, player

# ------------------------- CONSTANTS ----------------------------------------------------------------------------------

UID, NEXT_UID, THIRD_UID = 100, 200, 300
FROZEN_NOW = datetime(2026, 11, 15, 12, 0, 0).astimezone()
DATE_DIR, STAMP, NEXT_STAMP = "2026_11_15", "2026_11_15_12_00_00", "2026_11_15_12_00_01"
AUTOSAVE = {FP: "post_fp_data_autosave", QUALI: "post_quali_data_autosave", RACE: "post_race_data_autosave",
            TT: "post_tt_data_autosave"}
# (session data gate, lap telemetry gate)
GATES = pytest.mark.parametrize("session_data_gate, lap_telemetry_gate",
                                [(True, True), (True, False), (False, True), (False, False)],
                                ids=["both gates", "session data gate only", "lap telemetry gate only", "no gate"])
UNIFIED = pytest.mark.parametrize("unified_save", [True], indirect=True)
SAVED, SKIPPED, SAVE_END = ("report_session_saved_from_child", "report_session_save_skipped_from_child",
                            "report_pngt_save_end_from_child")

pytestmark = allure.feature("Unified save")

# ------------------------- HELPERS ------------------------------------------------------------------------------------

@dataclass(frozen=True)
class ContainerWrite:
    """One write_container() call: the destination, whether it holds lap telemetry, and its session data JSON."""
    dest_path: Path
    lap_telemetry: bool
    session_data_name: Optional[str]
    session_data: Optional[Dict[str, Any]]

    @property
    def holds(self) -> Tuple[bool, bool]:
        """(lap telemetry, session data), as str(SaveRequest) reads them."""
        return self.lap_telemetry, self.session_data is not None


def _writes(fake_subsystem: FakeSubsystem) -> List[ContainerWrite]:
    writes = []
    for call in fake_subsystem.process_calls:
        assert call.fn_name == "write_container"
        dest_path, lap_telemetry_args, entry = call.args
        writes.append(ContainerWrite(dest_path, lap_telemetry_args is not None,
                                     entry.file_name if entry else None,
                                     json.loads(entry.payload) if entry else None))
    return writes


@pytest.fixture
def frozen_clock(monkeypatch: pytest.MonkeyPatch) -> datetime:
    """save_request's clock stopped at FROZEN_NOW, so every save in a test lands on the same second."""
    class FrozenDatetime(datetime):
        """datetime with now() stopped."""
        @classmethod
        def now(cls, tz: Any = None) -> datetime:
            return FROZEN_NOW
    monkeypatch.setattr(save_request_module, "datetime", FrozenDatetime)
    return FROZEN_NOW


async def _session(manager: InjectingTelemetryManager, packets: Packets, session: SessionType24, *,
                   session_uid: int = UID, with_session: bool = True, with_participants: bool = True) -> None:
    """A session at Silverstone on session_uid: two cars complete lap 1, with a lap history each."""
    if with_session:
        await manager.inject(packets.session(session_uid=session_uid, session_type=session.name,
                                             track=TrackID.Silverstone, total_laps=5, track_length=5891))
    if with_participants:
        await manager.inject(packets.participants(player("Player"), ai("AI"), session_uid=session_uid))
    for lap, distance in ((1, 10.0), (1, 3000.0), (1, 5880.0), (2, 5.0)):
        await manager.inject(packets.lap(car(0, lap=lap, lap_distance=distance, status=racing_status(session)),
                                         car(1, lap=lap, lap_distance=distance - 5, status=racing_status(session)),
                                         session_uid=session_uid))
    for index in (0, 1):
        await manager.inject(packets.session_history(car_idx=index, laps=[lap_time(92_000, valid=True)],
                                                     session_uid=session_uid))


async def _final_classification(manager: InjectingTelemetryManager, packets: Packets) -> None:
    await manager.inject(packets.final_classification(classified(position=1, num_laps=1),
                                                      classified(position=2, num_laps=1), session_uid=UID))


async def _uid_change(manager: InjectingTelemetryManager, packets: Packets, session_uid: int = NEXT_UID) -> None:
    await manager.inject(packets.lap(car(0, lap=1, lap_distance=10), session_uid=session_uid))


async def _manual_save(handler: F1TelemetryHandler) -> Dict[str, Any]:
    with allure.step("Manual save"):
        return await handleManualSave(handler.m_logger, handler.m_session_state_ref, handler)


def _set_gates(handler: F1TelemetryHandler, state: SessionState, settings: PngSettings, session: SessionType24, *,
               session_data_gate: bool = True, lap_telemetry_gate: bool = True) -> None:
    """Turn off this session type's JSON autosave and/or the lap analyzer, through their hot-swap paths."""
    if not session_data_gate:
        handler.updateCaptureSettings(settings.Capture.model_copy(update={AUTOSAVE[session]: False}))
    if not lap_telemetry_gate:
        state.updateLapAnalyzerSettings(settings.LapAnalyzer.model_copy(update={"enable": False}))


def _no_sensors(state: SessionState, settings: PngSettings) -> None:
    no_sensors = LapAnalyzerSensorSettings(**{name: False for name in LapAnalyzerSensorSettings.model_fields})
    state.updateLapAnalyzerSettings(settings.LapAnalyzer.model_copy(update={"Sensors": no_sensors}))


async def _writes_finish(handler: F1TelemetryHandler) -> None:
    await asyncio.wait_for(asyncio.gather(*list(handler.m_save_tasks)), timeout=2.0)


def _tokens(tokens: TokenRecorder, name: str) -> List[Any]:
    return [arg for token, arg in tokens.records if token == name]


def _claims_under(root: Path) -> List[Path]:
    return [dest for dest in save_request_module._claimed_dests if root in dest.parents]

# ------------------------- GATING -------------------------------------------------------------------------------------

@allure.story("Gating")
@UNIFIED
@pytest.mark.parametrize("session", ALL_SESSIONS)
@pytest.mark.usefixtures("frozen_clock")
@allure.title("A final classification autosave writes one container ({session})")
async def test_unified_autosave_writes_one_container(manager: InjectingTelemetryManager, packets: Packets,
                                                     state: SessionState, handler: F1TelemetryHandler,
                                                     fake_subsystem: FakeSubsystem, saves: SaveRecorder,
                                                     tokens: TokenRecorder, user_data_dir: Path,
                                                     session: SessionType24) -> None:
    """Any session type to FINAL_CLASSIFICATION, both gates on, the clock frozen.

    Expected: one container at data/<date>/<event><timestamp>.pngt, holding lap telemetry and the session data as
    <stem>.json. No separate JSON or .pngt task is started: the recorder sees the container's two halves. The
    JSON's debug block names the auto-save reason, the container and its own file name. The session-saved token
    reports the container."""
    await _session(manager, packets, session)
    stem = f"{state.getEventInfoStr()}{STAMP}"
    await _final_classification(manager, packets)
    await _writes_finish(handler)

    dest = user_data_dir / "data" / DATE_DIR / f"{stem}.pngt"
    [write] = _writes(fake_subsystem)
    assert (write.dest_path, write.holds, write.session_data_name) == (dest, (True, True), f"{stem}.json")
    debug = write.session_data["debug"]
    assert (debug["reason"], debug["container"], debug["file-name"]) == \
        ("Auto-save after final classification", f"{stem}.pngt", f"{stem}.json")
    assert (handler.m_json_save_task, handler.m_lap_telemetry_save_task) == (None, None)
    assert saves.requests == [SaveRequestRecord("final_classification", "json", UID),
                              SaveRequestRecord("final_classification", "pngt", UID)]
    assert _tokens(tokens, SAVED) == [str(dest)]


@allure.story("Gating")
@UNIFIED
@GATES
@pytest.mark.parametrize("session", ALL_SESSIONS)
@allure.title("A final classification autosave holds what its gates allow ({session_data_gate}, {lap_telemetry_gate}, "
              "{session})")
async def test_unified_autosave_follows_each_gate(manager: InjectingTelemetryManager, packets: Packets,
                                                  state: SessionState, handler: F1TelemetryHandler,
                                                  settings: PngSettings, fake_subsystem: FakeSubsystem,
                                                  tokens: TokenRecorder, session: SessionType24,
                                                  session_data_gate: bool, lap_telemetry_gate: bool) -> None:
    """Any session type to FINAL_CLASSIFICATION, with this session type's JSON autosave and the lap analyzer each
    on or off.

    Expected: one container holding the halves whose gates are on. With neither, nothing is written and a skipped
    token is reported."""
    _set_gates(handler, state, settings, session, session_data_gate=session_data_gate,
               lap_telemetry_gate=lap_telemetry_gate)
    await _session(manager, packets, session)
    await _final_classification(manager, packets)
    await _writes_finish(handler)

    if session_data_gate or lap_telemetry_gate:
        assert [write.holds for write in _writes(fake_subsystem)] == [(lap_telemetry_gate, session_data_gate)]
    else:
        assert not _writes(fake_subsystem)
        assert [arg.split(":")[0] for arg in _tokens(tokens, SKIPPED)] == ["autosave-disabled"]


@allure.story("Gating")
@UNIFIED
@pytest.mark.parametrize("session", [RACE])
@allure.title("Sensors hot-swapped to none after the gate drop the lap telemetry half ({session})")
async def test_sensors_hot_swapped_to_none_drops_the_lap_half(manager: InjectingTelemetryManager, packets: Packets,
                                                              state: SessionState, handler: F1TelemetryHandler,
                                                              settings: PngSettings, fake_subsystem: FakeSubsystem,
                                                              session: SessionType24) -> None:
    """Race. The lap telemetry gate has passed, then every sensor is turned off before the save is built: the save
    starts with include_lap_telemetry=True and no sensors.

    Expected: the container holds session data only."""
    await _session(manager, packets, session)
    _no_sensors(state, settings)
    handler.startUnifiedSave(SaveReason.AUTO, include_session_data=True, include_lap_telemetry=True)
    await _writes_finish(handler)

    assert [write.holds for write in _writes(fake_subsystem)] == [(False, True)]


@allure.story("Gating")
@UNIFIED
@pytest.mark.parametrize("session", [RACE])
@allure.title("A save with no event name yet builds no request ({session})")
async def test_no_event_info_builds_no_request(manager: InjectingTelemetryManager, packets: Packets,
                                               handler: F1TelemetryHandler, fake_subsystem: FakeSubsystem,
                                               user_data_dir: Path, session: SessionType24) -> None:
    """UID 100 arrives on an SSTA, then PARTICIPANTS, laps and lap histories, but no SESSION packet, so there's no
    event name. Then a save is started with both halves.

    Expected: no request is built, nothing is written and no container name is left claimed."""
    await manager.inject(packets.event(PacketEventData.EventPacketType.SESSION_STARTED, None, session_uid=UID))
    await _session(manager, packets, session, with_session=False)

    assert handler.startUnifiedSave(SaveReason.MANUAL, include_session_data=True, include_lap_telemetry=True) is None
    assert not _writes(fake_subsystem)
    assert _claims_under(user_data_dir) == []


@allure.story("Gating")
@UNIFIED
@pytest.mark.parametrize("session", [RACE])
@allure.title("The session-saved token is reported only for a container with session data ({session})")
async def test_session_saved_token_only_with_session_data(manager: InjectingTelemetryManager, packets: Packets,
                                                          state: SessionState, handler: F1TelemetryHandler,
                                                          settings: PngSettings, fake_subsystem: FakeSubsystem,
                                                          tokens: TokenRecorder, session: SessionType24) -> None:
    """Race with its JSON autosave off to FINAL_CLASSIFICATION, which saves lap telemetry only. Then a manual save,
    which holds both.

    Expected: two containers. The session-saved token is reported for the manual one only, as the integration
    runner expects."""
    _set_gates(handler, state, settings, session, session_data_gate=False)
    await _session(manager, packets, session)
    await _final_classification(manager, packets)
    await _writes_finish(handler)
    await _manual_save(handler)
    await _writes_finish(handler)

    auto, manual = _writes(fake_subsystem)
    assert (auto.holds, manual.holds) == ((True, False), (True, True))
    assert _tokens(tokens, SAVED) == [str(manual.dest_path)]

# ------------------------- JUST IN CASE -------------------------------------------------------------------------------

@allure.story("Just-in-case")
@UNIFIED
@GATES
@pytest.mark.parametrize("session", ALL_SESSIONS)
@allure.title("A just-in-case save holds what its gates allow ({session_data_gate}, {lap_telemetry_gate}, {session})")
async def test_jic_each_gate_combination(manager: InjectingTelemetryManager, packets: Packets, state: SessionState,
                                         handler: F1TelemetryHandler, settings: PngSettings,
                                         fake_subsystem: FakeSubsystem, session: SessionType24,
                                         session_data_gate: bool, lap_telemetry_gate: bool) -> None:
    """Any session type on UID 100 with lap data and no FINAL_CLASSIFICATION, the two gates each on or off, then
    a LAP_DATA on UID 200.

    Expected: as the autosave: one container holding the halves whose gates are on, or nothing with neither. Its
    name carries the Just_in_case token, and so does its debug reason."""
    _set_gates(handler, state, settings, session, session_data_gate=session_data_gate,
               lap_telemetry_gate=lap_telemetry_gate)
    await _session(manager, packets, session)
    name = state.getEventInfoStr()
    await _uid_change(manager, packets)
    await _writes_finish(handler)

    writes = _writes(fake_subsystem)
    if not (session_data_gate or lap_telemetry_gate):
        assert not writes
        return
    [write] = writes
    assert write.holds == (lap_telemetry_gate, session_data_gate)
    assert write.dest_path.name.startswith(f"{name}Just_in_case_")
    if session_data_gate:
        assert write.session_data["debug"]["reason"] == "Just_in_case"


@allure.story("Just-in-case")
@UNIFIED
@pytest.mark.parametrize("session", [RACE])
@allure.title("A just-in-case save with no session data keeps the lap telemetry half ({session})")
async def test_jic_without_session_data_keeps_the_lap_half(manager: InjectingTelemetryManager, packets: Packets,
                                                           handler: F1TelemetryHandler,
                                                           fake_subsystem: FakeSubsystem,
                                                           caplog: pytest.LogCaptureFixture,
                                                           session: SessionType24) -> None:
    """Race on UID 100 with SESSION, lap data and lap histories but no PARTICIPANTS, so there's no session data to
    build (is_data_available is false). Both gates on. Then a LAP_DATA on UID 200.

    Expected: the save isn't aborted. One container holding lap telemetry only, and a warning that the JSON was
    left out."""
    await _session(manager, packets, session, with_participants=False)
    with caplog.at_level(logging.WARNING):
        await _uid_change(manager, packets)
    await _writes_finish(handler)

    assert [write.holds for write in _writes(fake_subsystem)] == [(True, False)]
    assert "No session data available for the JSON. Saving without it." in caplog.messages


@allure.story("Just-in-case")
@UNIFIED
@pytest.mark.parametrize("session", [RACE])
@allure.title("A just-in-case snapshot survives the state clear ({session})")
async def test_jic_snapshot_survives_the_state_clear(manager: InjectingTelemetryManager, packets: Packets,
                                                     state: SessionState, handler: F1TelemetryHandler,
                                                     fake_subsystem: FakeSubsystem, session: SessionType24) -> None:
    """Race on UID 100 at packet count 4321, then a LAP_DATA on UID 200 while the write is held. The state is
    cleared, and a SESSION for a race at Austria arrives on UID 200. Then the write is let go.

    Expected: the container is the outgoing session's: its session data has UID 100, packet count 4321 and the old
    session's name, and its lap telemetry is for UID 100."""
    await _session(manager, packets, session)
    state.m_pkt_count = 4321
    name = state.getEventInfoStr()
    fake_subsystem.block()
    await _uid_change(manager, packets)
    await manager.inject(packets.session(session_uid=NEXT_UID, session_type=RACE.name, track=TrackID.Austria,
                                         total_laps=5, track_length=4318))
    assert state.m_session_info.m_session_uid == NEXT_UID
    fake_subsystem.release()
    await _writes_finish(handler)

    [call] = fake_subsystem.process_calls
    [write] = _writes(fake_subsystem)
    debug = write.session_data["debug"]
    assert (debug["session-uid"], debug["packet-count"], debug["file-name"].startswith(name)) == (UID, 4321, True)
    assert call.args[1][1].session_uid == UID


@allure.story("Just-in-case")
@UNIFIED
@pytest.mark.parametrize("session", [RACE])
@allure.title("A just-in-case save runs while a manual save is writing ({session})")
async def test_jic_runs_while_a_manual_save_is_writing(manager: InjectingTelemetryManager, packets: Packets,
                                                       state: SessionState, handler: F1TelemetryHandler,
                                                       fake_subsystem: FakeSubsystem, session: SessionType24) -> None:
    """Race on UID 100. A manual save's write is held, then a LAP_DATA on UID 200.

    Expected: a just-in-case container is built and written beside the manual one. A unified save owns its
    snapshot, so the "a save task is already running" guard doesn't skip it."""
    await _session(manager, packets, session)
    name = state.getEventInfoStr()
    fake_subsystem.block()
    await _manual_save(handler)
    await _uid_change(manager, packets)
    fake_subsystem.release()
    await _writes_finish(handler)

    assert [write.dest_path.name.startswith(name + token) for write, token in
            zip(_writes(fake_subsystem), ("Manual_", "Just_in_case_"))] == [True, True]


@allure.story("Just-in-case")
@pytest.mark.parametrize("unified_save", [False], indirect=True)
@pytest.mark.parametrize("session", [RACE])
@allure.title("With unified save off, a just-in-case save is skipped while a separate-files save runs ({session})")
async def test_jic_skipped_while_a_separate_files_save_runs(manager: InjectingTelemetryManager, packets: Packets,
                                                            fake_subsystem: FakeSubsystem, saves: SaveRecorder,
                                                            session: SessionType24) -> None:
    """Unified save off (the default). Race on UID 100, then UID 200: its just-in-case JSON and .pngt tasks are
    created but haven't run. UID 200 gets a session with lap data, then UID 300 arrives before those tasks run.

    Expected: only UID 100's just-in-case saves. UID 200's is skipped by the separate-files "a save task is already
    running" guard, and nothing goes through the unified path."""
    await _session(manager, packets, session)
    await _uid_change(manager, packets)
    await _session(manager, packets, session, session_uid=NEXT_UID)
    await _uid_change(manager, packets, session_uid=THIRD_UID)

    assert saves.requests == [SaveRequestRecord("just_in_case", "json", UID),
                              SaveRequestRecord("just_in_case", "pngt", UID)]
    assert fake_subsystem.process_calls == []

# ------------------------- MANUAL SAVE --------------------------------------------------------------------------------

@allure.story("Manual save")
@UNIFIED
@pytest.mark.parametrize("lap_telemetry_gate", [True, False], ids=["lap telemetry gate on", "lap telemetry gate off"])
@pytest.mark.parametrize("session", [RACE])
@allure.title("A manual save replies with its container, and ignores the autosave gate ({lap_telemetry_gate}, "
              "{session})")
async def test_manual_save_response_and_gates(manager: InjectingTelemetryManager, packets: Packets,
                                              state: SessionState, handler: F1TelemetryHandler,
                                              settings: PngSettings, fake_subsystem: FakeSubsystem,
                                              session: SessionType24, lap_telemetry_gate: bool) -> None:
    """Race with its JSON autosave off and the lap analyzer on or off. Then a manual save.

    Expected: the reply is success with the container's path. The container holds session data anyway, and lap
    telemetry only with the lap analyzer on."""
    _set_gates(handler, state, settings, session, session_data_gate=False, lap_telemetry_gate=lap_telemetry_gate)
    await _session(manager, packets, session)
    response = await _manual_save(handler)
    await _writes_finish(handler)

    [write] = _writes(fake_subsystem)
    assert response == {"status": "success", "message": str(write.dest_path)}
    assert write.holds == (lap_telemetry_gate, True)


@allure.story("Manual save")
@UNIFIED
@pytest.mark.parametrize("nothing_to_save", ["no event name", "no session data and no sensors"])
@pytest.mark.parametrize("session", [RACE])
@allure.title("A manual save with nothing to save replies with an error ({nothing_to_save}, {session})")
async def test_manual_save_without_data(manager: InjectingTelemetryManager, packets: Packets, state: SessionState,
                                        handler: F1TelemetryHandler, settings: PngSettings,
                                        fake_subsystem: FakeSubsystem, session: SessionType24,
                                        nothing_to_save: str) -> None:
    """Race with no SESSION packet yet, or with SESSION and laps but no PARTICIPANTS and every sensor off. Then a
    manual save.

    Expected: the reply is exactly {"status": "error", "message": "No data available to save"}, and nothing is
    written."""
    if nothing_to_save == "no event name":
        await _session(manager, packets, session, with_session=False)
    else:
        _no_sensors(state, settings)
        await _session(manager, packets, session, with_participants=False)
    response = await _manual_save(handler)

    assert response == {"status": "error", "message": "No data available to save"}
    assert not _writes(fake_subsystem)


@allure.story("Manual save")
@UNIFIED
@pytest.mark.parametrize("session", [RACE])
@allure.title("A manual save doesn't wait for its write ({session})")
async def test_manual_save_does_not_wait_for_the_write(manager: InjectingTelemetryManager, packets: Packets,
                                                       handler: F1TelemetryHandler, fake_subsystem: FakeSubsystem,
                                                       session: SessionType24) -> None:
    """Race, then a manual save whose write is held.

    Expected: the handler replies while the write is still in flight, then the write finishes on release."""
    await _session(manager, packets, session)
    fake_subsystem.block()
    response = await _manual_save(handler)

    assert response["status"] == "success"
    assert len(handler.m_save_tasks) == 1
    fake_subsystem.release()
    await _writes_finish(handler)
    assert handler.m_save_tasks == set()

# ------------------------- CONCURRENCY AND NAMES ----------------------------------------------------------------------

@allure.story("Concurrency and names")
@UNIFIED
@pytest.mark.parametrize("session", [RACE])
@allure.title("Two saves in one second get different containers ({session})")
async def test_two_saves_in_one_second_get_different_containers(manager: InjectingTelemetryManager,
                                                                packets: Packets, state: SessionState,
                                                                handler: F1TelemetryHandler,
                                                                fake_subsystem: FakeSubsystem,
                                                                frozen_clock: datetime,
                                                                session: SessionType24) -> None:
    """Race, the clock frozen on one second. Two manual saves, the first still writing when the second starts.

    Expected: the second container's name is a second later, so neither overwrites the other. Both JSONs' debug
    timestamp is the real save time."""
    await _session(manager, packets, session)
    name = state.getEventInfoStr()
    fake_subsystem.block()
    await _manual_save(handler)
    await _manual_save(handler)
    fake_subsystem.release()
    await _writes_finish(handler)

    writes = _writes(fake_subsystem)
    assert [write.dest_path.name for write in writes] == [f"{name}Manual_{STAMP}.pngt",
                                                          f"{name}Manual_{NEXT_STAMP}.pngt"]
    assert {write.session_data["debug"]["timestamp"] for write in writes} == \
        {frozen_clock.strftime("%Y-%m-%d %H:%M:%S %Z")}


@allure.story("Concurrency and names")
@UNIFIED
@pytest.mark.parametrize("session", [RACE])
@pytest.mark.usefixtures("frozen_clock")
@allure.title("A save that writes nothing gives its name back ({session})")
async def test_claim_released_when_nothing_is_written(manager: InjectingTelemetryManager, packets: Packets,
                                                      state: SessionState, handler: F1TelemetryHandler,
                                                      settings: PngSettings, fake_subsystem: FakeSubsystem,
                                                      user_data_dir: Path, session: SessionType24) -> None:
    """Race with SESSION and laps but no PARTICIPANTS and every sensor off, the clock frozen. A manual save builds
    nothing. Then PARTICIPANTS arrive, and a second manual save in the same second.

    Expected: the first claims a name and gives it back. The second gets the unshifted name."""
    _no_sensors(state, settings)
    await _session(manager, packets, session, with_participants=False)
    assert (await _manual_save(handler))["status"] == "error"
    assert _claims_under(user_data_dir) == []

    await manager.inject(packets.participants(player("Player"), ai("AI"), session_uid=UID))
    await _manual_save(handler)
    await _writes_finish(handler)

    assert [write.dest_path.name for write in _writes(fake_subsystem)] == \
        [f"{state.getEventInfoStr()}Manual_{STAMP}.pngt"]


@allure.story("Concurrency and names")
@UNIFIED
@pytest.mark.parametrize("session", [RACE])
@pytest.mark.usefixtures("frozen_clock")
@allure.title("A failed write is logged, and gives its name back ({session})")
async def test_claim_released_after_a_failed_write(manager: InjectingTelemetryManager, packets: Packets,
                                                   state: SessionState, handler: F1TelemetryHandler,
                                                   fake_subsystem: FakeSubsystem, tokens: TokenRecorder,
                                                   caplog: pytest.LogCaptureFixture, session: SessionType24) -> None:
    """Race, the clock frozen. A manual save whose write raises OSError, then a second manual save in the same
    second.

    Expected: the failure is logged, not raised. The save-ended token is still reported, the task leaves
    m_save_tasks, and the second save gets the unshifted name."""
    await _session(manager, packets, session)
    fake_subsystem.fail_with(OSError("disk full"))
    with caplog.at_level(logging.ERROR):
        await _manual_save(handler)
        await _writes_finish(handler)

    failed = _writes(fake_subsystem)[0].dest_path
    assert any(record.message.startswith(f"Failed to write {failed}") for record in caplog.records)
    assert _tokens(tokens, SAVE_END) == [str(failed)]
    assert handler.m_save_tasks == set()

    await _manual_save(handler)
    await _writes_finish(handler)
    assert [write.dest_path.name for write in _writes(fake_subsystem)] == \
        [f"{state.getEventInfoStr()}Manual_{STAMP}.pngt"] * 2


@allure.story("Concurrency and names")
@UNIFIED
@pytest.mark.parametrize("session", [RACE])
@allure.title("A final classification while a manual save is writing runs beside it ({session})")
async def test_final_classification_while_a_manual_save_is_writing(manager: InjectingTelemetryManager,
                                                                   packets: Packets, handler: F1TelemetryHandler,
                                                                   fake_subsystem: FakeSubsystem,
                                                                   session: SessionType24) -> None:
    """Race. A manual save's write is held, then FINAL_CLASSIFICATION.

    Expected: both save tasks are in m_save_tasks. Both finish on release, and the set ends empty."""
    await _session(manager, packets, session)
    fake_subsystem.block()
    await _manual_save(handler)
    await _final_classification(manager, packets)

    assert len(handler.m_save_tasks) == 2
    fake_subsystem.release()
    await _writes_finish(handler)
    assert len(_writes(fake_subsystem)) == 2
    assert handler.m_save_tasks == set()


@allure.story("Concurrency and names")
@UNIFIED
@pytest.mark.parametrize("session", [RACE])
@allure.title("stop() waits for every save ({session})")
async def test_stop_waits_for_every_save(manager: InjectingTelemetryManager, packets: Packets,
                                         handler: F1TelemetryHandler, fake_subsystem: FakeSubsystem,
                                         tokens: TokenRecorder, session: SessionType24) -> None:
    """Race. Two manual saves are held, then stop(), then the writes are let go within the 5 s wait.

    Expected: stop() doesn't return while they're held. Both containers finish writing before it returns."""
    await _session(manager, packets, session)
    fake_subsystem.block()
    await _manual_save(handler)
    await _manual_save(handler)
    stopping = asyncio.ensure_future(handler.stop())
    for _ in range(5):
        await asyncio.sleep(0)
    assert not stopping.done()

    fake_subsystem.release()
    await asyncio.wait_for(stopping, timeout=2.0)
    assert len(_tokens(tokens, SAVE_END)) == 2
    assert handler.m_save_tasks == set()


@allure.story("Concurrency and names")
@UNIFIED
@pytest.mark.parametrize("session", [RACE])
@pytest.mark.parametrize("save_task_stop_timeout_s", [0.01], indirect=True, ids=["10 ms wait"])
@allure.title("stop() cancels a save that outlasts its wait ({session})")
async def test_stop_cancels_a_save_that_exceeds_the_wait(manager: InjectingTelemetryManager, packets: Packets,
                                                         handler: F1TelemetryHandler, fake_subsystem: FakeSubsystem,
                                                         tokens: TokenRecorder, session: SessionType24) -> None:
    """Race. A manual save is held and never let go, then stop(), with its 5 s wait cut to 10 ms.

    Expected: the save task is cancelled, stop() returns, and nothing raises. The save-ended token is still
    reported."""
    await _session(manager, packets, session)
    fake_subsystem.block()
    await _manual_save(handler)
    [task] = handler.m_save_tasks

    await asyncio.wait_for(handler.stop(), timeout=2.0)

    assert task.cancelled()
    assert handler.m_save_tasks == set()
    assert len(_tokens(tokens, SAVE_END)) == 1

# ------------------------- UNIFIED SAVE OFF (THE DEFAULT) -------------------------------------------------------------

@allure.story("Unified save off")
@pytest.mark.parametrize("unified_save", [False], indirect=True)
@pytest.mark.parametrize("trigger", ["final_classification", "just_in_case", "manual"])
@pytest.mark.parametrize("session", ALL_SESSIONS)
@allure.title("With unified save off, {trigger} uses the separate-files writers ({session})")
async def test_unified_off_uses_the_separate_files_writers(manager: InjectingTelemetryManager, packets: Packets,
                                                           handler: F1TelemetryHandler,
                                                           fake_subsystem: FakeSubsystem, saves: SaveRecorder,
                                                           user_data_dir: Path, session: SessionType24,
                                                           trigger: str) -> None:
    """Unified save off (the default). Any session type, then FINAL_CLASSIFICATION, a LAP_DATA on UID 200, or a
    manual save.

    Expected: no unified write and no save task in m_save_tasks. A separate JSON and .pngt are requested, and the
    .pngt goes flat in data/<date>/."""
    await _session(manager, packets, session)
    if trigger == "final_classification":
        await _final_classification(manager, packets)
    elif trigger == "just_in_case":
        await _uid_change(manager, packets)
    else:
        await _manual_save(handler)

    assert fake_subsystem.process_calls == []
    assert handler.m_save_tasks == set()
    assert saves.requests == [SaveRequestRecord(trigger, "json", UID), SaveRequestRecord(trigger, "pngt", UID)]
    assert saves.pngt_args[0][0].parent.parent == user_data_dir / "data"


@allure.story("Unified save off")
@pytest.mark.parametrize("unified_save", [False], indirect=True)
@pytest.mark.parametrize("trigger, token", [("final_classification", ""), ("just_in_case", "Just_in_case_"),
                                            ("manual", "Manual_")])
@pytest.mark.parametrize("session", [RACE])
@allure.title("With unified save off, the {trigger} save tasks write their files ({session})")
async def test_unified_off_save_tasks_write_their_files(manager: InjectingTelemetryManager, packets: Packets,
                                                        state: SessionState, handler: F1TelemetryHandler,
                                                        fake_subsystem: FakeSubsystem, tokens: TokenRecorder,
                                                        user_data_dir: Path, session: SessionType24,
                                                        trigger: str, token: str) -> None:
    """Unified save off (the default), and no save recorder, so the real save tasks run. A race on UID 100, then
    FINAL_CLASSIFICATION, a LAP_DATA on UID 200, or a manual save.

    Expected: the JSON is written under data/<date>/, named for the session and the save's token, with UID 100 in
    its debug block. Final classification and just-in-case write the .pngt through run_in_process(write_session) and
    clear both task slots. A manual save fires its .pngt write instead."""
    await _session(manager, packets, session)
    name = state.getEventInfoStr()
    if trigger == "final_classification":
        await _final_classification(manager, packets)
    elif trigger == "just_in_case":
        await _uid_change(manager, packets)
    else:
        await _manual_save(handler)
    await asyncio.wait_for(asyncio.gather(*(task for task in (handler.m_json_save_task,
                                                              handler.m_lap_telemetry_save_task) if task)), 2.0)

    [json_file] = user_data_dir.glob("data/*/*.json")
    assert json_file.name.startswith(f"{name}{token}")
    assert json.loads(json_file.read_text(encoding="utf-8"))["debug"]["session-uid"] == UID
    if trigger == "manual":
        assert "Manual Save Lap Telemetry Write" in fake_subsystem.fired_names
        return
    [call] = fake_subsystem.process_calls
    assert (call.fn_name, call.args[0].suffix, call.args[0].parent) == ("write_session", ".pngt", json_file.parent)
    assert (handler.m_json_save_task, handler.m_lap_telemetry_save_task) == (None, None)
    assert [name_ for name_, _ in tokens.records if name_ != SKIPPED] == [
        "report_pngt_save_start_from_child", SAVE_END]
