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

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

import bisect
from dataclasses import dataclass
from typing import Callable, Generic, Optional, Sequence, TypeVar

from .dto import CompletedLap, DriverExportData, LapMetadata, SensorConfig

# -------------------------------------- CLASSES -----------------------------------------------------------------------

@dataclass(slots=True)
class BaseTelemetrySnapshot:
    """The mandatory fields every real snapshot carries, regardless of which sensors
    A real snapshot subclasses this and adds its own sensor fields -- also with `slots=True`"""
    lap_distance: float  # metres from start line
    lap_time_ms: int      # elapsed time this lap, milliseconds

S = TypeVar("S", bound=BaseTelemetrySnapshot)

@dataclass(frozen=True)
class RecordedSensor(Generic[S]):
    """One sensor: its manifest entry (`config`) plus how to read its value off a
    real snapshot (`get`). `get` returning None means "unavailable this packet" --
    stored as NaN, not raised. The lib only knows a sensor has a config and a
    getter; which snapshot field backs which key is decided entirely by whoever
    builds the `RecordedSensor` list (e.g. apps/backend's F1_SENSORS)."""
    config: SensorConfig
    get: Callable[[S], Optional[float]]

@dataclass
class _InternalCompletedLap:
    """A completed lap plus the frame_ids needed for Case B flashback rollback
    (unwinding it back into the current buffers). Internal only -- export() copies
    out just the CompletedLap, dropping frame_ids."""
    lap: CompletedLap
    frame_ids: list[int]

class DriverTelemetryRecorder(Generic[S]):
    """Accumulates one driver's telemetry history for a session. One instance per
    driver; internal state is opaque. No I/O, no knowledge of the .pngt format --
    see plans/telemetry_recording/telemetry-ingest-spec.md for the full behavioural
    spec this implements.

    `_current_lap_number`'s only real source of truth is on_lap_change() (lap_number
    + 1). A snapshot carries no lap number at all, so the first update() call, if it
    happens before any on_lap_change(), seeds it to 1 -- a label for export(), not a
    claim about which lap it actually is.
    """

    def __init__(self, driver_index: int, sensors: Sequence[RecordedSensor[S]]) -> None:
        self._driver_index = driver_index
        self._sensors = tuple(sensors)

        keys = [sensor.config.key for sensor in self._sensors]
        if len(keys) != len(set(keys)):
            raise ValueError(f"sensors must have unique keys, got duplicates in {keys!r}")

        self._last_frame_id: Optional[int] = None
        self._current_lap_number: Optional[int] = None
        self._current_buffers: dict[str, list] = self._new_buffers()
        self._frame_id_buffer: list[int] = []
        self._completed_laps: list[_InternalCompletedLap] = []

    def update(self, snapshot: S, frame_id: int) -> None:
        """Called on every lap data packet. A frame_id lower than the last
        one seen is unambiguously a flashback"""
        if self._last_frame_id is not None and frame_id < self._last_frame_id:
            self._rollback(frame_id)

        lap_distance_buffer = self._current_buffers["lap_distance"]

        if not lap_distance_buffer:
            self._append_sample(snapshot, frame_id)
            if self._current_lap_number is None:
                self._current_lap_number = 1
        else:
            last_distance = lap_distance_buffer[-1]
            if snapshot.lap_distance > last_distance:
                self._append_sample(snapshot, frame_id)
            elif snapshot.lap_distance == last_distance:
                self._overwrite_last_sample(snapshot, frame_id)
            # else: lap_distance < last_distance -- drop, a sim reporting edge case.

        self._last_frame_id = frame_id

    def on_lap_change(self, metadata: LapMetadata) -> None:
        """Called when the sim's lap number increments by 1."""
        if not self._current_buffers["lap_distance"]:
            return  # No update() calls since init/last lap change -- discard, no empty entry.

        lap = CompletedLap(metadata=metadata, telemetry=self._copy_buffers(self._current_buffers))
        self._completed_laps.append(
            _InternalCompletedLap(lap=lap, frame_ids=list(self._frame_id_buffer))
        )
        self._current_buffers = self._new_buffers()
        self._frame_id_buffer = []
        self._current_lap_number = metadata.lap_number + 1

    def export(self) -> DriverExportData:
        """May be called multiple times safely -- never mutates internal state."""
        completed_laps = [
            CompletedLap(metadata=internal.lap.metadata, telemetry=self._copy_buffers(internal.lap.telemetry))
            for internal in self._completed_laps
        ]

        in_progress_lap = None
        if self._current_buffers["lap_distance"]:
            in_progress_lap = CompletedLap(
                metadata=LapMetadata(
                    lap_number=self._current_lap_number if self._current_lap_number is not None else 1,
                    lap_time_ms=None,
                    valid=False,
                    tyre_compound="",
                    tyre_laps=0,
                    pit_in_lap=False,
                    pit_out_lap=False,
                ),
                telemetry=self._copy_buffers(self._current_buffers),
            )

        return DriverExportData(
            driver_index=self._driver_index,
            completed_laps=completed_laps,
            in_progress_lap=in_progress_lap,
        )

    def _new_buffers(self) -> dict[str, list]:
        buffers: dict[str, list] = {"lap_distance": [], "lap_time_ms": []}
        for sensor in self._sensors:
            buffers[sensor.config.key] = []
        return buffers

    @staticmethod
    def _copy_buffers(buffers: dict[str, list]) -> dict[str, list]:
        return {key: list(values) for key, values in buffers.items()}

    def _append_sample(self, snapshot: S, frame_id: int) -> None:
        self._current_buffers["lap_distance"].append(snapshot.lap_distance)
        self._current_buffers["lap_time_ms"].append(snapshot.lap_time_ms)
        for sensor in self._sensors:
            self._current_buffers[sensor.config.key].append(self._sample_value(snapshot, sensor))
        self._frame_id_buffer.append(frame_id)

    def _overwrite_last_sample(self, snapshot: S, frame_id: int) -> None:
        self._current_buffers["lap_distance"][-1] = snapshot.lap_distance
        self._current_buffers["lap_time_ms"][-1] = snapshot.lap_time_ms
        for sensor in self._sensors:
            self._current_buffers[sensor.config.key][-1] = self._sample_value(snapshot, sensor)
        self._frame_id_buffer[-1] = frame_id

    @staticmethod
    def _sample_value(snapshot: S, sensor: RecordedSensor[S]):
        value = sensor.get(snapshot)
        return float("nan") if value is None else value

    def _rollback(self, target_frame_id: int) -> None:
        """The sim's flashback buffer is 20-30 seconds, so the rewind target is
        always within the current lap or at most one completed lap back."""
        if not self._frame_id_buffer or target_frame_id < self._frame_id_buffer[0]:
            self._rollback_case_b(target_frame_id)
        else:
            self._rollback_case_a(target_frame_id)

    def _rollback_case_a(self, target_frame_id: int) -> None:
        """Target is within the current (in-progress) lap -- truncate every buffer to
        just past the last sample at or before target_frame_id."""
        keep = bisect.bisect_right(self._frame_id_buffer, target_frame_id)
        self._frame_id_buffer = self._frame_id_buffer[:keep]
        for key, values in self._current_buffers.items():
            self._current_buffers[key] = values[:keep]

    def _rollback_case_b(self, target_frame_id: int) -> None:
        """Target predates the current lap -- discard it, unwind the last completed
        lap back into _current_buffers, truncated to target_frame_id within that
        lap. The restored lap's metadata is discarded; it's re-finalised as a new
        object when on_lap_change() fires again."""
        if not self._completed_laps:
            # No earlier lap to restore from -- target predates all recorded data.
            self._current_buffers = self._new_buffers()
            self._frame_id_buffer = []
            return

        restored = self._completed_laps.pop()
        keep = bisect.bisect_right(restored.frame_ids, target_frame_id)
        self._frame_id_buffer = restored.frame_ids[:keep]
        self._current_buffers = {key: values[:keep] for key, values in restored.lap.telemetry.items()}
        self._current_lap_number = restored.lap.metadata.lap_number
