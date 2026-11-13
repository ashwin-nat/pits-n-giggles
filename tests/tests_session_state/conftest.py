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
from typing import AsyncIterator

import pytest

from apps.backend.app_ctx import AppCtx
from apps.backend.state_mgmt_layer import SessionState
from apps.backend.telemetry_layer import telemetry_handler as telemetry_handler_module
from apps.backend.telemetry_layer.telemetry_handler import F1TelemetryHandler
from lib.config import PngSettings
from lib.logger import PngLogger

from .packet_helpers import Packets
from .harness import (FakeSubsystem, InjectingTelemetryManager, SaveRecorder,
                      TokenRecorder)

# ------------------------- CONSTANTS ----------------------------------------------------------------------------------

# The report_*_from_child tokens telemetry_handler imports by name
HANDLER_TOKENS = ["report_session_save_skipped_from_child"]

# ------------------------- FIXTURES -----------------------------------------------------------------------------------

@pytest.fixture
def packet_format(request: pytest.FixtureRequest) -> int:
    """2026 unless a test sweeps formats with @pytest.mark.parametrize("packet_format", ALL_FORMATS, indirect=True)."""
    return getattr(request, "param", 2026)


@pytest.fixture
def packets(packet_format: int) -> Packets:
    """Packet helpers bound to the test's packet format."""
    return Packets(packet_format)


@pytest.fixture
def settings() -> PngSettings:
    """Default settings."""
    return PngSettings()


@pytest.fixture
def logger(caplog: pytest.LogCaptureFixture) -> PngLogger:
    """A real PngLogger wired into caplog. Not taken from the logging registry, so tests never share one."""
    png_logger = PngLogger("session_state_harness")
    png_logger.setLevel(logging.DEBUG)
    png_logger.propagate = False
    png_logger.addHandler(caplog.handler)
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
async def handler(ctx: AppCtx, state: SessionState) -> AsyncIterator[F1TelemetryHandler]:
    """The real F1TelemetryHandler, registered on an InjectingTelemetryManager. Stopped at teardown,
    which also waits for any save task it started."""
    telemetry_handler = F1TelemetryHandler(
        ctx=ctx,
        session_state=state,
        manager=InjectingTelemetryManager(ctx.logger),
        packet_forward_queue=asyncio.Queue(),
    )
    yield telemetry_handler
    await telemetry_handler.stop()


@pytest.fixture
def manager(handler: F1TelemetryHandler) -> InjectingTelemetryManager:
    """The handler's manager. Depends on handler, so injecting always runs the full handler path."""
    return handler.m_manager


@pytest.fixture
def saves(monkeypatch: pytest.MonkeyPatch) -> SaveRecorder:
    """Records save requests instead of writing files."""
    return SaveRecorder(monkeypatch)


@pytest.fixture
def tokens(monkeypatch: pytest.MonkeyPatch) -> TokenRecorder:
    """Records the handler's report_*_from_child tokens."""
    return TokenRecorder(monkeypatch, telemetry_handler_module, HANDLER_TOKENS)
