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
import json
from dataclasses import dataclass
from logging import Logger
from pathlib import Path
from types import ModuleType
from typing import (Any, Awaitable, Callable, Coroutine, Dict, List, Optional,
                    Sequence, Tuple)

import allure
import pytest

from apps.backend.state_mgmt_layer import SessionState
from apps.backend.state_mgmt_layer.data_per_driver.data_per_driver import DataPerDriver
from apps.backend.state_mgmt_layer.intf import ManualSaveRsp
from apps.backend.telemetry_layer.telemetry_handler import F1TelemetryHandler
from lib.f1_types import F1PacketBase, PacketEventData, TrackID
from lib.f1_types.packet_2_lap_data import LapData
from lib.telemetry_manager import F1TelemetryManagerBase

from .packet_helpers import Packets, car, player

# ------------------------- LABELS -------------------------------------------------------------------------------------

def track_param(track: TrackID, kind: str) -> Any:
    """A fixture param for track, with id kind ("normal", "weird", "unknown"). Tagged "<kind> track" in the
    report, and selectable with --allure-label track=<kind>."""
    # Raw allure marks: allure.tag()/label() return plain functions, not marks, when --alluredir is unset
    # (e.g. VSCode discovery), which breaks pytest.param.
    return pytest.param(track, id=kind, marks=[pytest.mark.allure_label(f"{kind} track", label_type="tag"),
                                               pytest.mark.allure_label(kind, label_type="track")])


def title(text: str) -> Any:
    """allure.title for a test that takes track and packet_format: text, then the track and format the case
    ran on."""
    return allure.title(text + " ({track.name}, {packet_format})")

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
        block() or fail_with() says otherwise. Same signature as AsyncSubsystem.run_in_process."""
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
    """One save the handler asked for, on the separate-files path (Capture.unified_save_format off).

    Attributes:
        trigger (str): "final_classification", "just_in_case" or "manual"
        content (str): "json" or "pngt"
        session_uid (int): The session being saved
    """
    trigger: str
    content: str
    session_uid: int


class SaveRecorder:
    """Records the handler's save requests on the separate-files path without writing anything. Everything
    the handler does synchronously before the write (ManualSaveRsp, prepareLapTelemetryWrite) stays real.
    Unified saves are recorded by FakeSubsystem.run_in_process instead."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self.requests: List[SaveRequestRecord] = []
        recorder = self

        # Patched as plain functions, so the request is recorded when the task is created, not when it runs
        def auto_json(handler: F1TelemetryHandler, _final_json: Dict[str, Any], _file_name: str,
                      session_uid: int) -> Coroutine:
            recorder.requests.append(SaveRequestRecord("final_classification", "json", session_uid))
            return _clear_task_slot(handler, "m_json_save_task")

        def just_in_case_json(handler: F1TelemetryHandler, session_uid: int, _save_rsp: ManualSaveRsp) -> Coroutine:
            recorder.requests.append(SaveRequestRecord("just_in_case", "json", session_uid))
            return _clear_task_slot(handler, "m_json_save_task")

        def auto_lap_telemetry(handler: F1TelemetryHandler, _dest_path: Path, _args: tuple,
                               session_uid: int) -> Coroutine:
            # Final classification sets the flag before scheduling this; just-in-case only runs without it
            trigger = "final_classification" if handler.m_final_classification_processed else "just_in_case"
            recorder.requests.append(SaveRequestRecord(trigger, "pngt", session_uid))
            return _clear_task_slot(handler, "m_lap_telemetry_save_task")

        def manual_lap_telemetry(_handler: F1TelemetryHandler, lap_telemetry_write: Optional[Tuple[Path, tuple]],
                                 session_uid: int) -> None:
            if lap_telemetry_write is not None:
                recorder.requests.append(SaveRequestRecord("manual", "pngt", session_uid))

        monkeypatch.setattr(F1TelemetryHandler, "_autoSaveJsonTask", auto_json)
        monkeypatch.setattr(F1TelemetryHandler, "_saveJustInCaseJsonTask", just_in_case_json)
        monkeypatch.setattr(F1TelemetryHandler, "_autoSaveLapTelemetryTask", auto_lap_telemetry)
        monkeypatch.setattr(F1TelemetryHandler, "fireLapTelemetryWrite", manual_lap_telemetry)


async def _clear_task_slot(handler: F1TelemetryHandler, slot: str) -> None:
    # The real task clears its handle when it finishes, which is what lets the next save start
    setattr(handler, slot, None)


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

# ------------------------- LAP SCENARIOS ------------------------------------------------------------------------------

# Silverstone: finish line before the pit garage. Monaco: pit garage before the finish line
LAP_TRACKS = [track_param(TrackID.Silverstone, "normal"), track_param(TrackID.Monaco, "weird")]
LAP_TRACK_LENGTHS = {TrackID.Silverstone: 5891, TrackID.Monaco: 3337}


class Run:
    """The player's car (index 0) in one session on a LAP_TRACKS track. Lap distances read back are rounded to
    0.1 m: they're float32 on the wire, so 0.6 comes back as 0.6000000238."""

    def __init__(self, manager: InjectingTelemetryManager, packets: Packets, state: SessionState, track: TrackID,
                 session_uid: int = 100) -> None:
        self.manager = manager
        self.packets = packets
        self.state = state
        self.track = track
        self.session_uid = session_uid

    @property
    def driver(self) -> DataPerDriver:
        """The player's DataPerDriver."""
        return self.state.m_driver_data[0]

    async def session(self, session_type: str) -> None:
        """SESSION and PARTICIPANTS for a session_type session (a SessionType member name) on this track."""
        with allure.step(f"{session_type} at {self.track.name}"):
            await self.manager.inject(self.packets.session(
                session_uid=self.session_uid, session_type=session_type, track=self.track, total_laps=5,
                track_length=LAP_TRACK_LENGTHS[self.track]))
            await self.manager.inject(self.packets.participants(player("Player"), session_uid=self.session_uid))

    async def drive(self, status: LapData.DriverStatus, lap: int, *distances: float) -> None:
        """One LAP_DATA per distance, in status on lap."""
        with allure.step(f"{status.name} lap {lap}: {', '.join(str(d) for d in distances)}"):
            for packet in self.packets.drive(0, lap=lap, distances=list(distances), session_uid=self.session_uid,
                                             status=status):
                await self.manager.inject(packet)

    async def flashback(self, status: LapData.DriverStatus, lap: int, distance: float) -> None:
        """A FLBK event, then the LAP_DATA the car lands in: status, on lap, at distance. The landing's frame
        goes back to just after the flashback's target frame. Its overall frame keeps counting up."""
        target_frame = self.manager.injected[-1].m_header.m_frameIdentifier // 2
        with allure.step(f"Flashback, landing {status.name} lap {lap} at {distance}"):
            await self.manager.inject(self.packets.event(
                PacketEventData.EventPacketType.FLASHBACK,
                PacketEventData.Flashback.from_values(frame_identifier=target_frame), session_uid=self.session_uid))
            await self.manager.inject(self.packets.lap(car(0, lap=lap, lap_distance=distance, status=status),
                                                       session_uid=self.session_uid, frame=target_frame + 1))

    def completed_laps(self) -> Dict[int, List[float]]:
        """The lap recorder's completed laps, as lap number -> lap distances."""
        return {lap.metadata.lap_number: _distances(lap.telemetry["lap_distance"])
                for lap in self.driver.m_tel_rec.export().completed_laps}

    def in_progress_lap(self) -> Optional[Tuple[int, List[float]]]:
        """The lap recorder's in-progress lap as (lap number, lap distances), or None if it holds no samples."""
        lap = self.driver.m_tel_rec.export().in_progress_lap
        return None if lap is None else (lap.metadata.lap_number, _distances(lap.telemetry["lap_distance"]))

    def delta_laps(self) -> Dict[int, List[float]]:
        """The delta manager's laps, as lap number -> lap distances."""
        # Its only read of the stored laps is this debug dump
        dump = self.driver.m_delta_mgr._dump_state()  # pylint: disable=protected-access
        return {lap: _distances([distance for distance, _ in points]) for lap, points in dump.items()}


def _distances(distances: List[float]) -> List[float]:
    return [round(distance, 1) for distance in distances]
