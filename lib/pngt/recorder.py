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

from dataclasses import dataclass
from operator import attrgetter
from typing import Generic, Optional, Sequence, TypeVar

import numpy as np

from .dto import (MANDATORY_TELEMETRY_KEYS, CompletedLap, DriverExportData,
                  LapMetadata, SensorConfig)

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

_INITIAL_CAPACITY = 5000  # samples: over half of 9,759 saved laps fit (median 4,961). Doubles when full
_DISTANCE_COL = MANDATORY_TELEMETRY_KEYS.index("lap_distance")
_LAP_TIME_COL = MANDATORY_TELEMETRY_KEYS.index("lap_time_ms")

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
    """One sensor: its manifest entry (`config`) plus the snapshot attribute it is read from
    (`field`). A None value means "unavailable this packet" and is stored as NaN. Which snapshot
    field backs which key is decided by whoever builds the `RecordedSensor` list (e.g.
    apps/backend's F1_SENSORS). A derived value belongs in its own snapshot field."""
    config: SensorConfig
    field: str

@dataclass
class _InternalCompletedLap:
    """A completed lap plus each sample's frame_id, kept for debugging. Internal only --
    export() copies out just the CompletedLap, dropping frame_ids."""
    lap: CompletedLap
    frame_ids: list[int]

class _LapBuffer:
    """One lap's samples: a float32 row per sample, a column per key. Grows by doubling."""

    __slots__ = ("_keys", "_data", "n")

    def __init__(self, keys: tuple[str, ...]) -> None:
        self._keys = keys
        # Column-major, so each column copies out contiguous. No rows until the first sample: empty car slots get none
        self._data = np.empty((0, len(keys)), dtype=np.float32, order="F")
        self.n = 0

    def append(self, row: tuple) -> None:
        """Add a sample. None values become NaN."""
        if self.n == len(self._data):
            self._reserve(max(_INITIAL_CAPACITY, 2 * self.n))
        self._data[self.n] = row
        self.n += 1

    def overwrite_last(self, row: tuple) -> None:
        """Replace the last sample. None values become NaN."""
        self._data[self.n - 1] = row

    def last(self, col: int) -> float:
        """The last sample's value in column col."""
        return float(self._data[self.n - 1, col])

    def bisect_left(self, col: int, value: float) -> int:
        """Where value would go in column col, which must be ascending. Same as bisect.bisect_left, at float32."""
        # As float32, or numpy compares a float in float64 and keeps a stored sample equal to value
        return int(np.searchsorted(self._data[:self.n, col], np.float32(value), side="left"))

    def truncate(self, n: int) -> None:
        """Keep the first n samples."""
        self.n = n

    def columns(self) -> dict[str, np.ndarray]:
        """A read-only copy of each column, keyed by its key."""
        out = {}
        for col, key in enumerate(self._keys):
            values = self._data[:self.n, col].copy()
            values.flags.writeable = False
            # A view: numpy won't make it writeable again while its base is read-only, an owning array it would
            out[key] = values[:]
        return out

    def load(self, columns: dict[str, np.ndarray], n: int) -> None:
        """Replace the contents with the first n samples of columns, as columns() returns them."""
        # No growth needed: columns were recorded in this buffer, which never shrinks
        for col, key in enumerate(self._keys):
            self._data[:n, col] = columns[key][:n]
        self.n = n

    def _reserve(self, capacity: int) -> None:
        grown = np.empty((capacity, len(self._keys)), dtype=np.float32, order="F")
        grown[:self.n] = self._data[:self.n]
        self._data = grown

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

        # One C-level call reads a whole sample, in column order
        self._read_row = attrgetter(*MANDATORY_TELEMETRY_KEYS, *(sensor.field for sensor in self._sensors))
        self._current_lap_number: Optional[int] = None
        self._buffer = _LapBuffer((*MANDATORY_TELEMETRY_KEYS, *keys))
        # The last sample's values as the sim sent them, so update() compares them unrounded
        self._last_distance: float = 0.0
        self._last_lap_time_ms: float = 0.0
        self._frame_id_buffer: list[int] = []
        self._completed_laps: list[_InternalCompletedLap] = []

    def update(self, snapshot: S, frame_id: int, lap_number: int) -> None:
        """Called on every lap data packet, with the sim's current lap number."""
        if not self._buffer.n:
            self._append_sample(snapshot, frame_id)
            if self._current_lap_number is None:
                self._current_lap_number = lap_number
            return

        # Lap timer went back -- drop. F1 zeroes the AI cars' lap timers mid-lap when the player
        # finishes the race. A flashback landing that rewinds the timer is dropped too; accepted.
        if snapshot.lap_time_ms < self._last_lap_time_ms:
            return

        if snapshot.lap_distance > self._last_distance:
            self._append_sample(snapshot, frame_id)
        elif snapshot.lap_distance == self._last_distance:
            self._overwrite_last_sample(snapshot, frame_id)
        # else: lap_distance went back -- drop, a sim reporting edge case.

    def on_lap_change(self, metadata: LapMetadata) -> None:
        """Called when the sim's lap number increments by 1."""
        if not self._buffer.n:
            # Nothing to keep: no samples since the last lap change. Keep the lap number current.
            self._current_lap_number = metadata.lap_number + 1
            return

        lap = CompletedLap(metadata=metadata, telemetry=self._buffer.columns())
        self._completed_laps.append(
            _InternalCompletedLap(lap=lap, frame_ids=self._frame_id_buffer)
        )
        self._buffer.truncate(0)
        self._frame_id_buffer = []
        self._current_lap_number = metadata.lap_number + 1

    def discard_in_progress_lap(self, next_lap_number: Optional[int] = None) -> None:
        """Drop the current lap's samples, for a lap that ends without being driven to the line (garage,
        out lap -> flying lap, a pause in updates, the sim skipping the session to its end). Completed
        laps are kept. Recording carries on under next_lap_number if given, else the same lap number."""
        self._buffer.truncate(0)
        self._frame_id_buffer = []
        if next_lap_number is not None:
            self._current_lap_number = next_lap_number

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
        """May be called multiple times safely -- never mutates internal state. Each telemetry value is
        a read-only float32 array."""
        completed_laps = [
            CompletedLap(metadata=internal.lap.metadata, telemetry=dict(internal.lap.telemetry))
            for internal in self._completed_laps
        ]

        in_progress_lap = None
        if self._buffer.n:
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
                telemetry=self._buffer.columns(),
            )

        return DriverExportData(
            driver_index=self._driver_index,
            completed_laps=completed_laps,
            in_progress_lap=in_progress_lap,
        )

    def _append_sample(self, snapshot: S, frame_id: int) -> None:
        self._buffer.append(self._read_row(snapshot))
        self._frame_id_buffer.append(frame_id)
        self._last_distance = snapshot.lap_distance
        self._last_lap_time_ms = snapshot.lap_time_ms

    def _overwrite_last_sample(self, snapshot: S, frame_id: int) -> None:
        self._buffer.overwrite_last(self._read_row(snapshot))
        self._frame_id_buffer[-1] = frame_id
        self._last_lap_time_ms = snapshot.lap_time_ms

    def _resync_last_sample(self) -> None:
        """Re-read the last sample's values after the buffer was cut back or reloaded."""
        if self._buffer.n:
            self._last_distance = self._buffer.last(_DISTANCE_COL)
            self._last_lap_time_ms = self._buffer.last(_LAP_TIME_COL)

    def _rollback_case_a(self, landing_distance: float) -> None:
        """Landed within the current (in-progress) lap -- truncate every buffer to the
        samples before landing_distance. Frame IDs can't be used: the sim resumes later
        than its own target frame."""
        keep = self._buffer.bisect_left(_DISTANCE_COL, landing_distance)
        self._frame_id_buffer = self._frame_id_buffer[:keep]
        self._buffer.truncate(keep)
        self._resync_last_sample()

    def _rollback_case_b(self, lap_number: int, landing_distance: float) -> None:
        """Landed in an earlier lap -- discard the current one, unwind the last completed
        lap back into _current_buffers, truncated to landing_distance within that
        lap. The restored lap's metadata is discarded; it's re-finalised as a new
        object when on_lap_change() fires again."""
        if not self._completed_laps or self._completed_laps[-1].lap.metadata.lap_number != lap_number:
            # The lap being returned to was never stored -- carry on from the landing point
            self._buffer.truncate(0)
            self._frame_id_buffer = []
            self._current_lap_number = lap_number
            return

        restored = self._completed_laps.pop()
        telemetry = restored.lap.telemetry
        keep = int(np.searchsorted(telemetry["lap_distance"], np.float32(landing_distance), side="left"))
        self._frame_id_buffer = restored.frame_ids[:keep]
        self._buffer.load(telemetry, keep)
        self._resync_last_sample()
        self._current_lap_number = restored.lap.metadata.lap_number
