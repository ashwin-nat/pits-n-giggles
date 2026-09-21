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
from typing import Optional

from ..dtypes import SensorDtype
from .dto import (
    BaseTelemetrySnapshot,
    IngestCompletedLap,
    IngestDriverExportData,
    IngestLapMetadata,
    TelemetryRecorderConfig,
)
from .mapper import SensorMapper

# -------------------------------------- CLASSES -----------------------------------------------------------------------

@dataclass
class _InternalCompletedLap:
    """Completed-lap storage with frame_ids attached -- needed for Case B flashback
    rollback (unwinding the last completed lap back into the current buffers). Internal
    only: export() maps this to IngestCompletedLap, dropping frame_ids."""
    metadata: IngestLapMetadata
    telemetry: dict[str, list]
    frame_ids: list[int]

class DriverTelemetryRecorder:
    """Accumulates one driver's telemetry history for a session. One instance per driver;
    internal state is opaque. No I/O, no knowledge of the .pngt format -- see
    plans/telemetry_recording/telemetry-ingest-spec.md for the full behavioural spec this
    implements.

    `_current_lap_number` note: the spec's own internal-state list says it's "set on
    first update() or on_lap_change()", but update()'s behaviour steps never actually
    describe how -- the snapshot carries no lap number at all, so update() has
    nothing to derive one from. Resolution: on_lap_change() is the only real source of
    truth (lap_number + 1, per spec); the first update() call, if it happens before any
    on_lap_change(), seeds _current_lap_number to 1 as a labelling default for whatever
    partial lap recording started mid-session on. It's a label for export(), not a claim
    about which lap this actually is -- the caller's on_lap_change() metadata is what
    matters once it arrives.
    """

    def __init__(
        self,
        driver_index: int,
        config: TelemetryRecorderConfig,
        mapper: SensorMapper,
    ) -> None:
        self._driver_index = driver_index
        self._config = config
        self._mapper = mapper

        # Resolved once here, not per-sample in the 60 Hz update() loop. Also doubles as
        # the spec's construction-time fail-fast validation: an unresolvable key raises
        # straight out of get_dtype() before any packets are ever recorded.
        self._dtypes: dict[str, SensorDtype] = {key: mapper.get_dtype(key) for key in config.sensors}

        self._last_frame_id: Optional[int] = None
        self._current_lap_number: Optional[int] = None
        self._current_buffers: dict[str, list] = self._new_buffers()
        self._frame_id_buffer: list[int] = []
        self._completed_laps: list[_InternalCompletedLap] = []

    def update(self, snapshot: BaseTelemetrySnapshot, frame_id: int) -> None:
        """Called on every telemetry packet (~60 Hz). A frame_id lower than the last one
        seen is unambiguously a flashback (lower layers already discard out-of-order
        packets, so this can't be a late one) -- rewind recorded state to it before
        processing this snapshot as a normal sample against the now-truncated buffers."""
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

    def on_lap_change(self, completed_lap: IngestLapMetadata) -> None:
        """Called when the sim's lap number increments by 1. Mutates completed_lap.num_points
        in place -- the caller has no way to know that count itself, only this recorder does."""
        if not self._current_buffers["lap_distance"]:
            return  # No update() calls since init/last lap change -- discard, no empty entry.

        completed_lap.num_points = len(self._current_buffers["lap_distance"])
        self._completed_laps.append(
            _InternalCompletedLap(
                metadata=completed_lap,
                telemetry=self._copy_buffers(self._current_buffers),
                frame_ids=list(self._frame_id_buffer),
            )
        )
        self._current_buffers = self._new_buffers()
        self._frame_id_buffer = []
        self._current_lap_number = completed_lap.lap_number + 1

    def export(self) -> IngestDriverExportData:
        """May be called multiple times safely -- never mutates internal state."""
        completed_laps = [
            IngestCompletedLap(
                metadata=internal.metadata,
                telemetry=self._copy_buffers(internal.telemetry),
            )
            for internal in self._completed_laps
        ]
        return IngestDriverExportData(
            driver_index=self._driver_index,
            completed_laps=completed_laps,
            in_progress_lap_number=self._current_lap_number if self._current_lap_number is not None else 1,
            in_progress_telemetry=self._copy_buffers(self._current_buffers),
            in_progress_num_points=len(self._current_buffers["lap_distance"]),
        )

    def _new_buffers(self) -> dict[str, list]:
        buffers: dict[str, list] = {"lap_distance": []}
        for key in self._config.sensors:
            buffers[key] = []
        return buffers

    @staticmethod
    def _copy_buffers(buffers: dict[str, list]) -> dict[str, list]:
        return {key: list(values) for key, values in buffers.items()}

    def _append_sample(self, snapshot: BaseTelemetrySnapshot, frame_id: int) -> None:
        self._current_buffers["lap_distance"].append(snapshot.lap_distance)
        for key in self._config.sensors:
            self._current_buffers[key].append(self._sample_value(snapshot, key))
        self._frame_id_buffer.append(frame_id)

    def _overwrite_last_sample(self, snapshot: BaseTelemetrySnapshot, frame_id: int) -> None:
        self._current_buffers["lap_distance"][-1] = snapshot.lap_distance
        for key in self._config.sensors:
            self._current_buffers[key][-1] = self._sample_value(snapshot, key)
        self._frame_id_buffer[-1] = frame_id

    def _sample_value(self, snapshot: BaseTelemetrySnapshot, key: str):
        value = self._mapper.get_value(snapshot, key)
        if value is not None:
            return value
        return float("nan") if self._dtypes[key] is SensorDtype.FLOAT32 else -1

    def _rollback(self, target_frame_id: int) -> None:
        """The sim's flashback buffer is 20-30 seconds, so the rewind target is always
        within the current lap or at most one completed lap back -- no deeper rollback
        is possible. Case A/B below per the spec's Flashback Handling section."""
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
        """Target predates the current lap -- discard it, unwind the last completed lap
        back into _current_buffers, truncated to target_frame_id within that lap. The
        restored lap's metadata is discarded; it's no longer a completed lap and will be
        re-finalised when on_lap_change() fires again."""
        if not self._completed_laps:
            # No earlier lap to restore from -- target predates all recorded data.
            self._current_buffers = self._new_buffers()
            self._frame_id_buffer = []
            return

        restored = self._completed_laps.pop()
        keep = bisect.bisect_right(restored.frame_ids, target_frame_id)
        self._frame_id_buffer = restored.frame_ids[:keep]
        self._current_buffers = {key: values[:keep] for key, values in restored.telemetry.items()}
        self._current_lap_number = restored.metadata.lap_number
