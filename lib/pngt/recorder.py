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

from .dto import (MANDATORY_TELEMETRY_KEYS, CompletedLap, DriverExportData,
                  LapMetadata, SensorConfig)

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
    """A completed lap plus each sample's frame_id, kept for debugging. Internal only --
    export() copies out just the CompletedLap, dropping frame_ids."""
    lap: CompletedLap
    frame_ids: list[int]

class DriverTelemetryRecorder(Generic[S]):
    """Accumulates one driver's telemetry history for a session. One instance per
    driver; internal state is opaque. No I/O, no knowledge of the .pngt format --
    see plans/telemetry_recording/telemetry-ingest-spec.md for the full behavioural
    spec this implements.

    `_current_lap_number` is seeded from the sim's lap number by the first update(), and
    advanced by on_lap_change() (lap_number + 1). The recorder detects no lap events itself --
    the caller reports lap changes, laps that end without one, and flashbacks. It only buckets
    samples by lap: whether a lap's trace is complete is for the consumer to judge.
    """

    def __init__(self, driver_index: int, sensors: Sequence[RecordedSensor[S]]) -> None:
        self._driver_index = driver_index
        self._sensors = tuple(sensors)

        keys = [sensor.config.key for sensor in self._sensors]
        if len(keys) != len(set(keys)):
            raise ValueError(f"sensors must have unique keys, got duplicates in {keys!r}")

        self._current_lap_number: Optional[int] = None
        self._current_buffers: dict[str, list] = self._new_buffers()
        self._frame_id_buffer: list[int] = []
        self._completed_laps: list[_InternalCompletedLap] = []

    def update(self, snapshot: S, frame_id: int, lap_number: int) -> None:
        """Called on every lap data packet, with the sim's current lap number."""
        lap_distance_buffer = self._current_buffers["lap_distance"]

        if not lap_distance_buffer:
            self._append_sample(snapshot, frame_id)
            if self._current_lap_number is None:
                self._current_lap_number = lap_number
        else:
            last_distance = lap_distance_buffer[-1]
            if snapshot.lap_distance > last_distance:
                self._append_sample(snapshot, frame_id)
            elif snapshot.lap_distance == last_distance:
                self._overwrite_last_sample(snapshot, frame_id)
            # else: lap_distance < last_distance -- drop, a sim reporting edge case.

    def on_lap_change(self, metadata: LapMetadata) -> None:
        """Called when the sim's lap number increments by 1."""
        if not self._current_buffers["lap_distance"]:
            # Nothing to keep: no samples since the last lap change. Keep the lap number current.
            self._current_lap_number = metadata.lap_number + 1
            return

        lap = CompletedLap(metadata=metadata, telemetry=self._copy_buffers(self._current_buffers))
        self._completed_laps.append(
            _InternalCompletedLap(lap=lap, frame_ids=list(self._frame_id_buffer))
        )
        self._current_buffers = self._new_buffers()
        self._frame_id_buffer = []
        self._current_lap_number = metadata.lap_number + 1

    def discard_in_progress_lap(self) -> None:
        """Drop the current lap's samples, for a lap that ends without the sim's lap number
        changing (garage, out lap -> flying lap, a pause in updates). Completed laps are kept,
        and recording carries on under the same lap number."""
        self._current_buffers = self._new_buffers()
        self._frame_id_buffer = []

    def on_flashback(self, lap_number: int, landing_distance: float) -> None:
        """Called when the sim rewinds, before the update() for the packet the car landed in.
        Drops everything recorded past the landing point."""
        if self._current_lap_number is None:
            return
        if lap_number < self._current_lap_number:
            self._rollback_case_b(lap_number, landing_distance)
        else:
            self._rollback_case_a(landing_distance)

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
                    ers_harvest_limit_j=None,
                ),
                telemetry=self._copy_buffers(self._current_buffers),
            )

        return DriverExportData(
            driver_index=self._driver_index,
            completed_laps=completed_laps,
            in_progress_lap=in_progress_lap,
        )

    def _new_buffers(self) -> dict[str, list]:
        buffers: dict[str, list] = {key: [] for key in MANDATORY_TELEMETRY_KEYS}
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

    def _rollback_case_a(self, landing_distance: float) -> None:
        """Landed within the current (in-progress) lap -- truncate every buffer to the
        samples before landing_distance. Frame IDs can't be used: the sim resumes later
        than its own target frame."""
        keep = bisect.bisect_left(self._current_buffers["lap_distance"], landing_distance)
        self._frame_id_buffer = self._frame_id_buffer[:keep]
        for key, values in self._current_buffers.items():
            self._current_buffers[key] = values[:keep]

    def _rollback_case_b(self, lap_number: int, landing_distance: float) -> None:
        """Landed in an earlier lap -- discard the current one, unwind the last completed
        lap back into _current_buffers, truncated to landing_distance within that
        lap. The restored lap's metadata is discarded; it's re-finalised as a new
        object when on_lap_change() fires again."""
        if not self._completed_laps or self._completed_laps[-1].lap.metadata.lap_number != lap_number:
            # The lap being returned to was never stored -- carry on from the landing point
            self._current_buffers = self._new_buffers()
            self._frame_id_buffer = []
            self._current_lap_number = lap_number
            return

        restored = self._completed_laps.pop()
        keep = bisect.bisect_left(restored.lap.telemetry["lap_distance"], landing_distance)
        self._frame_id_buffer = restored.frame_ids[:keep]
        self._current_buffers = {key: values[:keep] for key, values in restored.lap.telemetry.items()}
        self._current_lap_number = restored.lap.metadata.lap_number
