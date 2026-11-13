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

import asyncio
from dataclasses import dataclass
from types import ModuleType
from typing import (Any, Awaitable, Callable, Coroutine, Dict, List, Optional,
                    Sequence, Tuple)

import pytest

from apps.backend.state_mgmt_layer.intf import ManualSaveRsp
from apps.backend.telemetry_layer.telemetry_handler import F1TelemetryHandler
from lib.f1_types import F1PacketBase
from lib.telemetry_manager import F1TelemetryManagerBase

# ------------------------- MANAGER ------------------------------------------------------------------------------------

class InjectingTelemetryManager(F1TelemetryManagerBase):
    """Telemetry manager with no transport. Tests hand it parsed packets through inject()."""

    async def inject(self, packet: F1PacketBase) -> None:
        """Dispatch a parsed packet exactly as production does after parsing (frame gate, any-packet
        callback, typed callback). The raw-packet path is skipped.

        Args:
            packet (F1PacketBase): The packet to dispatch
        """
        await self._dispatch(packet)

# ------------------------- SUBSYSTEM ----------------------------------------------------------------------------------

class FakeDealer:
    """Records dealer.fire() calls instead of sending them."""

    def __init__(self) -> None:
        self.fires: List[Tuple[str, str, Dict[str, Any]]] = []

    def fire(self, target: str, topic: str, payload: Dict[str, Any]) -> Coroutine:
        """Record the call. Returns a coroutine, as the real dealer does, for fire_and_forget to close."""
        self.fires.append((target, topic, payload))
        return _noop()


@dataclass(frozen=True)
class ProcessCall:
    """One run_in_process() call."""
    fn_name: str
    args: Tuple[Any, ...]
    kwargs: Dict[str, Any]


class FakeSubsystem:
    """Stands in for the backend's AsyncSubsystem: records fire_and_forget names and run_in_process calls, and
    runs nothing."""

    version = "test"

    def __init__(self) -> None:
        self.dealer = FakeDealer()
        self.fired_names: List[Optional[str]] = []
        self.process_calls: List[ProcessCall] = []
        self._blocked = False
        self._blocked_futures: List[asyncio.Future] = []
        self._fail_next: Optional[BaseException] = None

    def fire_and_forget(self, coro: Coroutine, name: Optional[str] = None) -> None:
        """Record the name and close the coroutine without running it."""
        self.fired_names.append(name)
        coro.close()

    def run_in_process(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Awaitable[Any]:
        """Record the call without running fn. Returns a future that resolves to None straight away, unless
        block() or fail_with() says otherwise. Same signature as AsyncSubsystem.run_in_process on the feature
        branch."""
        self.process_calls.append(ProcessCall(fn_name=fn.__name__, args=args, kwargs=kwargs))
        future = asyncio.get_running_loop().create_future()
        if self._fail_next is not None:
            future.set_exception(self._fail_next)
            self._fail_next = None
        elif self._blocked:
            self._blocked_futures.append(future)
        else:
            future.set_result(None)
        return future

    def block(self) -> None:
        """Hold every run_in_process() call from now on until release()."""
        self._blocked = True

    def release(self) -> None:
        """Complete every held run_in_process() call, and stop holding new ones."""
        self._blocked = False
        for future in self._blocked_futures:
            if not future.done():
                future.set_result(None)
        self._blocked_futures.clear()

    def fail_with(self, exc: BaseException) -> None:
        """Make the next run_in_process() call raise exc."""
        self._fail_next = exc

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
