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

# Fixtures that take other fixtures as arguments are how pytest works, not shadowing
# pylint: disable=redefined-outer-name

# ------------------------- IMPORTS ------------------------------------------------------------------------------------

import asyncio
import logging
from pathlib import Path
from typing import AsyncIterator, Iterator, List

import allure
import pytest
from allure_commons.types import LabelType

from apps.backend.app_ctx import AppCtx
from apps.backend.state_mgmt_layer import SessionState
from apps.backend.state_mgmt_layer import save_request as save_request_module
from apps.backend.telemetry_layer import telemetry_handler as telemetry_handler_module
from apps.backend.telemetry_layer.telemetry_handler import F1TelemetryHandler
from lib.config import (CaptureSettings, LapAnalyzerSensorSettings,
                        LapAnalyzerSettings, PngSettings)
from lib.f1_types import TrackID
from lib.logger import PngLogger

from .packet_helpers import Packets
from .harness import (FakeSubsystem, InjectingTelemetryManager, PlayerCar,
                      SaveRecorder, TokenRecorder)

# ------------------------- CONSTANTS ----------------------------------------------------------------------------------

# The report_*_from_child tokens telemetry_handler imports by name
HANDLER_TOKENS = [
    "report_session_save_skipped_from_child",
    "report_session_saved_from_child",
    "report_pngt_save_start_from_child",
    "report_pngt_save_end_from_child",
]

SUITE_DIR = Path(__file__).parent
CALL_REPORT = pytest.StashKey[pytest.TestReport]()

# ------------------------- HOOKS --------------------------------------------------------------------------------------

def pytest_collection_modifyitems(items: List[pytest.Item]) -> None:
    """Put every test in this suite under the "Session state" epic, and refuse one with no feature label."""
    for item in items:
        if SUITE_DIR not in item.path.parents:
            continue
        item.add_marker(allure.epic("Session state"))
        if not any(mark.kwargs.get("label_type") == LabelType.FEATURE
                   for mark in item.iter_markers(name="allure_label")):
            raise pytest.UsageError(f"{item.nodeid} has no allure.feature. Set pytestmark = allure.feature(...)")


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item: pytest.Item) -> Iterator[pytest.TestReport]:
    """Keep the call phase's report, so fixtures can tell at teardown whether the test passed."""
    report = yield
    if report.when == "call":
        item.stash[CALL_REPORT] = report
    return report

# ------------------------- FIXTURES -----------------------------------------------------------------------------------

@pytest.fixture
def packet_format(request: pytest.FixtureRequest) -> int:
    """2026 unless a test sweeps formats with @pytest.mark.parametrize("packet_format", ALL_FORMATS, indirect=True)."""
    return getattr(request, "param", 2026)


@pytest.fixture
def frame_gate_enabled(request: pytest.FixtureRequest) -> bool:
    """False (the default setting) unless a test passes @pytest.mark.parametrize("frame_gate_enabled", [True],
    indirect=True)."""
    return getattr(request, "param", False)


@pytest.fixture
def packets(packet_format: int) -> Packets:
    """Packet helpers bound to the test's packet format."""
    return Packets(packet_format)


@pytest.fixture
def unified_save(request: pytest.FixtureRequest) -> bool:
    """False (the default setting) unless a test passes @pytest.mark.parametrize("unified_save", [True],
    indirect=True)."""
    return getattr(request, "param", False)


@pytest.fixture
def settings(unified_save: bool) -> PngSettings:
    """Every session type autosaves and records laps, every lap analyzer sensor is on, and just-in-case saves
    are on. Capture.unified_save_format comes from unified_save."""
    all_sensors = LapAnalyzerSensorSettings(**{name: True for name in LapAnalyzerSensorSettings.model_fields})
    return PngSettings(
        Capture=CaptureSettings(post_race_data_autosave=True, post_quali_data_autosave=True,
                                post_fp_data_autosave=True, post_tt_data_autosave=True,
                                just_in_case_autosave=True, unified_save_format=unified_save),
        LapAnalyzer=LapAnalyzerSettings(enable=True, record_in_race=True, record_in_quali=True,
                                        record_in_fp=True, record_in_tt=True, Sensors=all_sensors),
    )


@pytest.fixture(autouse=True)
def user_data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Where saves would land. resolve_user_file points here for every module that imports it, so no
    scenario creates anything under the real data/ directory."""
    for module in (telemetry_handler_module, save_request_module):
        monkeypatch.setattr(module, "resolve_user_file", lambda name: str(tmp_path / name))
    return tmp_path


@pytest.fixture
def logger() -> PngLogger:
    """A real PngLogger, not taken from the logging registry, so tests never share one. It propagates to
    root, where pytest's per-test handlers feed both caplog and the report's captured log (Allure's "log")."""
    png_logger = PngLogger("session_state_harness")
    png_logger.setLevel(logging.DEBUG)
    png_logger.parent = logging.getLogger()
    png_logger.propagate = True
    return png_logger


@pytest.fixture
def fake_subsystem() -> FakeSubsystem:
    """Recording stand-in for the backend subsystem."""
    return FakeSubsystem()


@pytest.fixture
def ctx(logger: PngLogger, settings: PngSettings, fake_subsystem: FakeSubsystem) -> AppCtx:
    """Backend app context built from the fakes above."""
    return AppCtx(logger=logger, settings=settings, subsystem=fake_subsystem)


@pytest.fixture
def state(ctx: AppCtx) -> SessionState:
    """The real SessionState."""
    return SessionState(ctx)


@pytest.fixture
async def handler(ctx: AppCtx, state: SessionState,
                  frame_gate_enabled: bool) -> AsyncIterator[F1TelemetryHandler]:
    """The real F1TelemetryHandler, registered on an InjectingTelemetryManager. Stopped at teardown,
    which also waits for any save task it started."""
    telemetry_handler = F1TelemetryHandler(
        ctx=ctx,
        session_state=state,
        manager=InjectingTelemetryManager(ctx.logger, frame_gate_enabled=frame_gate_enabled),
        packet_forward_queue=asyncio.Queue(),
    )
    yield telemetry_handler
    await telemetry_handler.stop()


@pytest.fixture
def manager(request: pytest.FixtureRequest, handler: F1TelemetryHandler) -> Iterator[InjectingTelemetryManager]:
    """The handler's manager. Depends on handler, so injecting always runs the full handler path.
    A test that does not pass (failed, errored or xfailed) gets every injected packet attached to its report."""
    yield handler.m_manager
    call_report = request.node.stash.get(CALL_REPORT, None)
    if call_report is None or not call_report.passed:
        handler.m_manager.attach_trace()


@pytest.fixture
def player_car(manager: InjectingTelemetryManager, packets: Packets, state: SessionState,
               track: TrackID) -> PlayerCar:
    """The player's car on track. The test module provides track, e.g. a fixture with params=LAP_TRACKS. Start
    the session with await player_car.session(...)."""
    return PlayerCar(manager, packets, state, track)


@pytest.fixture
def saves(monkeypatch: pytest.MonkeyPatch) -> SaveRecorder:
    """Records save requests instead of writing files."""
    return SaveRecorder(monkeypatch)


@pytest.fixture
def tokens(monkeypatch: pytest.MonkeyPatch) -> TokenRecorder:
    """Records the handler's report_*_from_child tokens."""
    return TokenRecorder(monkeypatch, telemetry_handler_module, HANDLER_TOKENS)
