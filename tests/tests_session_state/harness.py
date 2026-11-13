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

# ------------------------- IMPORTS ------------------------------------------------------------------------------------

import json
from dataclasses import dataclass
from logging import Logger
from types import ModuleType
from typing import (Any, Callable, Coroutine, Dict, List, Optional, Sequence,
                    Tuple)

import allure
import pytest

from apps.backend.state_mgmt_layer.intf import ManualSaveRsp
from apps.backend.telemetry_layer.telemetry_handler import F1TelemetryHandler
from lib.f1_types import F1PacketBase, TrackID
from lib.telemetry_manager import F1TelemetryManagerBase

# ------------------------- LABELS -------------------------------------------------------------------------------------

def track_param(track: TrackID, kind: str) -> Any:
    """A fixture param for track, with id kind ("normal", "weird", "unknown"). Tagged "<kind> track" in the
    report, and selectable with --allure-label track=<kind>."""
    return pytest.param(track, id=kind, marks=[allure.tag(f"{kind} track"), allure.label("track", kind)])

# ------------------------- MANAGER ------------------------------------------------------------------------------------

class InjectingTelemetryManager(F1TelemetryManagerBase):
    """Telemetry manager with no transport. Tests hand it parsed packets through inject()."""

    def __init__(self, logger: Logger, frame_gate_enabled: bool = False) -> None:
        """Same arguments as F1TelemetryManagerBase."""
        super().__init__(logger, frame_gate_enabled=frame_gate_enabled)
        self.injected: List[F1PacketBase] = []

    async def inject(self, packet: F1PacketBase) -> None:
        """Dispatch a parsed packet exactly as production does after parsing (frame gate, any-packet
        callback, typed callback). The raw-packet path is skipped.

        Each packet is a report step, and is kept in injected for attach_trace().

        Args:
            packet (F1PacketBase): The packet to dispatch
        """
        self.injected.append(packet)
        header = packet.m_header
        with allure.step(f"{header.m_packetId.name}, uid {header.m_sessionUID}, frame {header.m_frameIdentifier}"):
            await self._dispatch(packet)

    def attach_trace(self) -> None:
        """Attach every injected packet, in order, to the report as one JSON file."""
        trace = [packet.toJSON(include_header=True) for packet in self.injected]
        allure.attach(json.dumps(trace, indent=2), name="injected packets",
                      attachment_type=allure.attachment_type.JSON)

# ------------------------- SUBSYSTEM ----------------------------------------------------------------------------------

class FakeDealer:
    """Records dealer.fire() calls instead of sending them."""

    def __init__(self) -> None:
        self.fires: List[Tuple[str, str, Dict[str, Any]]] = []

    def fire(self, target: str, topic: str, payload: Dict[str, Any]) -> Coroutine:
        """Record the call. Returns a coroutine, as the real dealer does, for fire_and_forget to close."""
        self.fires.append((target, topic, payload))
        return _noop()


class FakeSubsystem:
    """Stands in for the backend's AsyncSubsystem: records fire_and_forget names and runs nothing."""

    version = "test"

    def __init__(self) -> None:
        self.dealer = FakeDealer()
        self.fired_names: List[Optional[str]] = []

    def fire_and_forget(self, coro: Coroutine, name: Optional[str] = None) -> None:
        """Record the name and close the coroutine without running it."""
        self.fired_names.append(name)
        coro.close()

    def add_task(self, *_args: Any, **_kwargs: Any) -> None:
        """Tests never call register_tasks, so nothing may register a task."""
        raise AssertionError("FakeSubsystem.add_task called - tests must not register tasks")


async def _noop() -> None:
    return None

# ------------------------- RECORDERS ----------------------------------------------------------------------------------

@dataclass(frozen=True)
class SaveRequestRecord:
    """One save the handler asked for. reason is None for the post-final-classification save."""
    kind: str
    session_uid: int
    reason: Optional[str]


class SaveRecorder:
    """Records the handler's save requests without writing anything. ManualSaveRsp construction for
    the just-in-case save stays real, because that synchronous snapshot is part of the behaviour."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self.requests: List[SaveRequestRecord] = []
        recorder = self

        def just_in_case(handler: F1TelemetryHandler, session_uid: int, save_rsp: ManualSaveRsp) -> Coroutine:
            recorder.requests.append(SaveRequestRecord(
                kind="just_in_case", session_uid=session_uid, reason=save_rsp.m_final_json["debug"]["reason"]))
            return _finish_save_task(handler)

        async def final_classification(_handler: F1TelemetryHandler, _final_json: Dict[str, Any],
                                       session_uid: int) -> None:
            recorder.requests.append(SaveRequestRecord(kind="final_classification", session_uid=session_uid,
                                                       reason=None))

        monkeypatch.setattr(F1TelemetryHandler, "_saveJustInCaseDataTask", just_in_case)
        monkeypatch.setattr(F1TelemetryHandler, "postGameDumpToFile", final_classification)


async def _finish_save_task(handler: F1TelemetryHandler) -> None:
    # The real task clears the handle when it finishes, which is what lets the next save start
    handler.m_save_task = None


class TokenRecorder:
    """Replaces the named report_*_from_child functions in a module's namespace (they are imported by
    name) with a recorder of (name, arg)."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch, module: ModuleType, names: Sequence[str]) -> None:
        self.records: List[Tuple[str, Any]] = []
        for name in names:
            monkeypatch.setattr(module, name, self._recorder(name))

    def _recorder(self, name: str) -> Callable[[Any], None]:
        def record(arg: Any = None) -> None:
            self.records.append((name, arg))
        return record
