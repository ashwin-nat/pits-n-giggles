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

"""The .pngt save gate and scope: which sessions get a .pngt on FINAL_CLASSIFICATION, a just-in-case save or a
manual save, and what goes into it. The JSON save beside it follows CaptureSettings, which leaves every session
type on (a manual save has no JSON gate)."""

# Fixtures that take other fixtures as arguments are how pytest works, not shadowing
# pylint: disable=redefined-outer-name

# ------------------------- IMPORTS ------------------------------------------------------------------------------------

from typing import List

import allure
import pytest

from apps.backend.intf_layer.ipc.command_handlers import handleManualSave
from apps.backend.state_mgmt_layer import SessionState
from apps.backend.telemetry_layer.telemetry_handler import F1TelemetryHandler
from lib.config import LapAnalyzerSensorSettings, PngSettings
from lib.f1_types import PacketSessionData, SessionType24, TelemetrySetting, TrackID

from .harness import (ALL_SESSIONS, FP, LAP_TRACK_LENGTHS, LAP_TRACKS, QUALI,
                      RACE, SAVE_FORMATS, TT, InjectingTelemetryManager, SaveRecorder,
                      SaveRequestRecord, racing_status, title)
from .packet_helpers import (ALL_FORMATS, DriverSpec, Packets, ai, car,
                             classified, lap_time, player)

# ------------------------- CONSTANTS ----------------------------------------------------------------------------------

UID, NEXT_UID = 100, 200
TRIGGERS = ["final_classification", "just_in_case", "manual"]
RECORD_IN = {FP: "record_in_fp", QUALI: "record_in_quali", RACE: "record_in_race", TT: "record_in_tt"}
FormulaType = PacketSessionData.FormulaType

pytestmark = [allure.feature("pngt save gate"), SAVE_FORMATS]

# ------------------------- FIXTURES -----------------------------------------------------------------------------------

@pytest.fixture(params=LAP_TRACKS)
def track(request: pytest.FixtureRequest) -> TrackID:
    """Both track topologies."""
    return request.param

# ------------------------- HELPERS ------------------------------------------------------------------------------------

async def _session_with_a_lap(manager: InjectingTelemetryManager, packets: Packets, session: SessionType24,
                              drivers: List[DriverSpec], *, track: TrackID = TrackID.Silverstone,
                              formula: FormulaType = FormulaType.F1_MODERN, is_spectating: bool = False) -> None:
    """A session on UID 100 in which every driver completes lap 1, with a lap history each."""
    length = LAP_TRACK_LENGTHS[track]
    await manager.inject(packets.session(session_uid=UID, session_type=session.name, track=track, total_laps=5,
                                         track_length=length, formula=formula, is_spectating=is_spectating))
    await manager.inject(packets.participants(*drivers, session_uid=UID))
    status = racing_status(session)
    for lap, distance in ((1, 10.0), (1, length / 2), (1, length - 10.0), (2, 5.0)):
        await manager.inject(packets.lap(*[car(index, lap=lap, lap_distance=distance, status=status)
                                           for index in range(len(drivers))], session_uid=UID))
    for index in range(len(drivers)):
        await manager.inject(packets.session_history(car_idx=index, laps=[lap_time(92_000, valid=True)],
                                                     session_uid=UID))


async def _end(handler: F1TelemetryHandler, packets: Packets, trigger: str, num_cars: int) -> None:
    """FINAL_CLASSIFICATION on UID 100, a LAP_DATA on UID 200 for a just-in-case save, or a manual save mid-session
    as the IPC route calls it."""
    manager: InjectingTelemetryManager = handler.m_manager
    if trigger == "final_classification":
        await manager.inject(packets.final_classification(
            *[classified(position=index + 1, num_laps=1) for index in range(num_cars)], session_uid=UID))
    elif trigger == "just_in_case":
        await manager.inject(packets.lap(car(0, lap=1, lap_distance=10), session_uid=NEXT_UID))
    else:
        with allure.step("Manual save"):
            await handleManualSave(handler.m_logger, handler.m_session_state_ref, handler)


def _saves(trigger: str, pngt: bool) -> List[SaveRequestRecord]:
    return [SaveRequestRecord(trigger, "json", UID)] + ([SaveRequestRecord(trigger, "pngt", UID)] if pngt else [])

# ------------------------- SPECTATING ---------------------------------------------------------------------------------

@allure.story("Spectating")
@pytest.mark.parametrize("packet_format", ALL_FORMATS, indirect=True)
@pytest.mark.parametrize("session", [RACE])
@title("A spectated session saves a .pngt with every car in it")
async def test_pngt_saved_while_spectating(manager: InjectingTelemetryManager, packets: Packets,
                                           handler: F1TelemetryHandler, saves: SaveRecorder, session: SessionType24,
                                           track: TrackID) -> None:
    """Race spectated as in f1_24_mp_spectator_bahrain: player car index 255 in every header, SESSION with
    is_spectating, and 3 human cars (2 of them Restricted) and an AI car. Each car completes lap 1, then
    FINAL_CLASSIFICATION.

    Expected: a .pngt is requested beside the JSON. Its driver list and driver data hold all 4 cars, each with
    lap 1 recorded, and its player index is None."""
    packets.player_index = 255
    drivers = [player("Host"), player("Guest 1", TelemetrySetting.RESTRICTED),
               player("Guest 2", TelemetrySetting.RESTRICTED), ai("AI", TelemetrySetting.RESTRICTED)]
    await _session_with_a_lap(manager, packets, session, drivers, track=track, is_spectating=True)
    await _end(handler, packets, "final_classification", len(drivers))

    assert saves.requests == _saves("final_classification", pngt=True)
    _, session_metadata, _, driver_records, driver_data = saves.pngt_args[0]
    assert [record.name for record in driver_records] == ["Host", "Guest 1", "Guest 2", "AI"]
    assert {index: [lap.metadata.lap_number for lap in export.completed_laps]
            for index, export in driver_data.items()} == {0: [1], 1: [1], 2: [1], 3: [1]}
    assert session_metadata.player_index is None

# ------------------------- SESSION TYPE GATE --------------------------------------------------------------------------

@allure.story("Session type gate")
@pytest.mark.parametrize("packet_format", ALL_FORMATS, indirect=True)
@pytest.mark.parametrize("trigger", TRIGGERS)
@pytest.mark.parametrize("record_in_off", list(RECORD_IN.values()))
@pytest.mark.parametrize("session", ALL_SESSIONS)
@allure.title("{record_in_off} off: .pngt on {trigger} follows it ({session}, {packet_format})")
async def test_pngt_gated_by_session_type(manager: InjectingTelemetryManager, packets: Packets,
                                          handler: F1TelemetryHandler, state: SessionState, settings: PngSettings,
                                          saves: SaveRecorder, session: SessionType24, record_in_off: str,
                                          trigger: str) -> None:
    """Any session type, with one of the four LapAnalyzer record_in_* flags off. The player completes lap 1, then
    FINAL_CLASSIFICATION, a LAP_DATA on the next UID for a just-in-case save, or a manual save.

    Expected: the JSON is saved. The .pngt is saved unless the flag that is off is this session type's."""
    state.updateLapAnalyzerSettings(settings.LapAnalyzer.model_copy(update={record_in_off: False}))
    await _session_with_a_lap(manager, packets, session, [player("Player")])
    await _end(handler, packets, trigger, num_cars=1)

    assert saves.requests == _saves(trigger, pngt=record_in_off != RECORD_IN[session])

# ------------------------- SENSORS GATE -------------------------------------------------------------------------------

@allure.story("Sensors gate")
@pytest.mark.parametrize("trigger", TRIGGERS)
@pytest.mark.parametrize("lap_analyzer", ["every sensor off", "lap analyzer off"])
@pytest.mark.parametrize("session", ALL_SESSIONS)
@allure.title("With {lap_analyzer}, {trigger} saves no .pngt ({session})")
async def test_pngt_not_saved_without_sensors(manager: InjectingTelemetryManager, packets: Packets,
                                              handler: F1TelemetryHandler, state: SessionState,
                                              settings: PngSettings, saves: SaveRecorder, session: SessionType24,
                                              lap_analyzer: str, trigger: str) -> None:
    """Any session type, with every lap analyzer sensor off, or the lap analyzer itself off. The player completes
    lap 1, then FINAL_CLASSIFICATION, a LAP_DATA on the next UID for a just-in-case save, or a manual save.

    Expected: only the JSON is saved."""
    no_sensors = LapAnalyzerSensorSettings(**{name: False for name in LapAnalyzerSensorSettings.model_fields})
    update = {"Sensors": no_sensors} if lap_analyzer == "every sensor off" else {"enable": False}
    state.updateLapAnalyzerSettings(settings.LapAnalyzer.model_copy(update=update))
    await _session_with_a_lap(manager, packets, session, [player("Player")])
    await _end(handler, packets, trigger, num_cars=1)

    assert saves.requests == _saves(trigger, pngt=False)

# ------------------------- SESSION FACTS ------------------------------------------------------------------------------

@allure.story("Session facts")
@pytest.mark.parametrize("formula, ers_max_capacity_j", [
    (FormulaType.F1_MODERN, 4_000_000.0),   # F1 25 and earlier
    (FormulaType.F1_26, 4_000_000.0),
    (FormulaType.F2, None),
    (FormulaType.F2_2021, None),
], ids=["F1 modern", "F1 26", "F2", "F2 2021"])
@allure.title("The .pngt records an ERS capacity only for F1 cars ({formula})")
async def test_pngt_ers_capacity_only_for_f1(manager: InjectingTelemetryManager, packets: Packets,
                                             handler: F1TelemetryHandler, saves: SaveRecorder,
                                             formula: FormulaType, ers_max_capacity_j: float) -> None:
    """Race with formula in SESSION, the player on car 3 of 4. Every car completes lap 1, then
    FINAL_CLASSIFICATION.

    Expected: the .pngt's ers_max_capacity_j is 4 MJ for an F1 formula and None for F2. Its player index is 3."""
    packets.player_index = 3
    drivers = [ai("AI 1"), ai("AI 2"), ai("AI 3"), player("Player")]
    await _session_with_a_lap(manager, packets, RACE, drivers, formula=formula)
    await _end(handler, packets, "final_classification", len(drivers))

    _, session_metadata, _, _, _ = saves.pngt_args[0]
    assert session_metadata.ers_max_capacity_j == ers_max_capacity_j
    assert session_metadata.player_index == 3
