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
from typing import Optional

# -------------------------------------- CLASSES -----------------------------------------------------------------------

@dataclass(slots=True)
class BaseTelemetrySnapshot:
    """The core fields every real snapshot must carry, regardless of which sensors
    were configured for recording -- unlike everything else on a snapshot, these
    aren't optional, sensor-mapper-routed data.

    `lap_distance` is also the one field DriverTelemetryRecorder ever accesses
    directly, rather than through SensorMapper.get_value() -- it's the mandatory
    x-axis for all telemetry, needed unconditionally for buffering decisions
    (append/overwrite/drop) before any configured-sensor extraction happens at
    all, so it can't be routed through the same optional, per-sensor machinery as
    everything else. `lap_time_ms` is mandatory for the same "always present"
    reason, but isn't touched by the recorder's own buffering logic -- it's just
    guaranteed data for whichever consumer wants to read it.

    A real snapshot's full shape (every other sensor field an actual sim packet
    can report) is game-/domain-specific and belongs with whatever code builds it
    from real packets -- e.g. apps/backend's own TelemetrySnapshot, which
    subclasses this and adds its ~40 F1-specific fields on top -- not in this
    generic library. Subclassing (rather than a structural Protocol) makes these
    real, inherited fields with one definition, not something every consumer has
    to redeclare identically to satisfy a shape.

    `slots=True` -- one of these is built per telemetry packet, per driver
    (~60 Hz), so the __dict__ overhead a plain dataclass instance would carry
    is a real, avoidable cost at that volume. Every subclass must also declare
    `slots=True`, or its own __dict__ reappears and this saves nothing.
    """
    lap_distance: float  # metres from start line
    lap_time_ms: int      # elapsed time this lap, milliseconds

@dataclass
class IngestLapMetadata:
    """Metadata about a completed lap, passed to DriverTelemetryRecorder.on_lap_change()
    by the existing codebase. Named distinctly from the top-level lib.pngt.LapMetadata --
    both live in the same package now, and this one has no `is_good` field, since
    mark-good is a file-format-level mutation this layer has no knowledge of."""
    lap_number: int
    lap_time_ms: Optional[int]  # None if lap was not timed (e.g. out-lap)
    valid: bool                 # False if invalidated by track limits etc.
    tyre_compound: str          # e.g. "Soft", "Medium", "Hard", "Inter", "Wet"
    tyre_laps: int              # laps on this set at start of lap
    pit_in_lap: bool            # True if driver pitted at end of this lap
    pit_out_lap: bool           # True if driver exited pits at start of this lap
    num_points: int             # number of update() calls recorded for this lap

@dataclass(frozen=True)
class TelemetryRecorderConfig:
    """Passed to DriverTelemetryRecorder at construction. Frozen -- no hot reloading of
    which sensors are recorded mid-session. A plain dataclass, not a pydantic model: this
    is built internally from already-validated lib/config settings (Phase 9's
    build_recorder_config()), not from untrusted input, so it doesn't need pydantic's
    validation -- matching the repo convention that pydantic is reserved for real
    validation boundaries (see e.g. lib/track_segment_info, which validates loaded JSON).
    Also keeps this class from reading as another app-config schema; lib/config owns
    that role.

    `sensors` is just dotted keys, not (key, dtype) pairs -- SensorMapper.get_dtype() is
    the single source of truth for a sensor's storage width, so there's no second place
    for that fact to drift out of sync with. The recorder asks the injected mapper for
    dtype wherever it needs it (missing-value sentinel selection), and validates every
    configured key against the mapper at construction, failing fast on an unknown one.

    `sensors` is a `tuple`, not a `list`: `frozen=True` alone only stops `self.sensors`
    from being rebound, not the list it points at from being mutated in place after
    construction -- which would desync a recorder already built from it (its cached
    `_dtypes` and buffers snapshot `sensors` at `__init__` time). `__post_init__` coerces
    whatever iterable is passed in, so construction still accepts a plain list."""
    sensors: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "sensors", tuple(self.sensors))
        if len(self.sensors) != len(set(self.sensors)):
            raise ValueError(f"sensors must contain unique keys, got duplicates in {self.sensors!r}")

@dataclass
class IngestCompletedLap:
    """Pairs a lap's metadata with its telemetry data. All lists in `telemetry` are the
    same length; missing float values are stored as float('nan'), missing int values as
    -1, per the dtype SensorMapper.get_dtype() reports for that sensor. Named distinctly
    from the top-level lib.pngt.CompletedLap, which additionally validates array-length
    agreement -- an on-disk/write-time concern this layer doesn't have."""
    metadata: IngestLapMetadata
    telemetry: dict[str, list]  # "lap_distance" + configured sensor keys, all equal length

@dataclass
class IngestDriverExportData:
    """Returned by DriverTelemetryRecorder.export(). Everything the file writer needs for
    one driver. No NumPy dependency -- the file writer converts these lists to arrays at
    write time, using dtypes sourced from SensorMapper.get_dtype(). Named distinctly from
    the top-level lib.pngt.DriverExportData, whose in_progress_lap is a single optional
    CompletedLap rather than this layer's always-present (possibly empty) in-progress
    fields."""
    driver_index: int

    completed_laps: list[IngestCompletedLap]
    # Laps for which on_lap_change() was called and data was available.
    # Ordered by lap number ascending.

    in_progress_lap_number: int
    in_progress_telemetry: dict[str, list]
    in_progress_num_points: int
    # Telemetry accumulated since the last on_lap_change().
    # Included regardless of whether the lap is complete.
    # May be empty (num_points=0) if no update() calls received for this lap.
    # lap_time_ms is unavailable for this lap -- the file writer sets it to null.
