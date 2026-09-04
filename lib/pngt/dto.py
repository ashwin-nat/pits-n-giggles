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
from enum import Enum

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class SensorType(Enum):
    """How the viewer must interpolate this sensor's values between samples. The only
    sensor property this library validates against a closed set: unlike tyre_compound/
    session_type (caller-owned labels passed straight through), this one gates behavior
    the reader/writer/viewer actually depend on, not sim-specific domain knowledge."""
    CONTINUOUS = "continuous"
    DISCRETE = "discrete"

@dataclass(frozen=True)
class SensorConfig:
    """A single entry in manifest.json's sensor registry, as stored on disk and as
    returned by read_manifest()/read_session(). No dtype field: manifest.json's sensor
    registry only ever carries label/unit/type, and dtype has no on-disk representation
    to recover on read. write_session() takes dtypes as a separate `dict[str,
    SensorDtype]` argument (keyed by sensor key) instead — the true per-array dtype
    otherwise lives implicitly in each lap's .npz file, recovered via
    read_lap_telemetry()'s returned ndarrays' own .dtype.
    """
    key: str
    label: str
    unit: str
    type: SensorType

    def __post_init__(self) -> None:
        # The one field this library validates against a closed set (see SensorType's
        # docstring) -- enforced here, at construction, rather than by write_session(),
        # since it's an invariant of this object alone. Enforced via isinstance rather
        # than a value check: SensorType being an Enum means a bad literal can only
        # reach here via duck-typed/incorrectly-constructed input.
        if not isinstance(self.type, SensorType):
            raise ValueError(f"Invalid sensor type {self.type!r} for sensor {self.key!r}; expected a SensorType")

@dataclass(frozen=True)
class TrackInfo:
    id: int  # the sim's own TrackID enum value, e.g. 10 = Spa
    name: str

@dataclass(frozen=True)
class SessionBest:
    driver_index: int
    lap_number: int
    lap_time_ms: int

@dataclass(frozen=True)
class SessionMetadata:
    session_uid: int
    session_name: str
    session_type: str
    app_version: str
    game_year: int
    formula: str
    game_version: str
    timestamp: str  # ISO-8601, passed through verbatim, never parsed
    track: TrackInfo
    laps_count: int
    session_best: SessionBest | None

@dataclass(frozen=True)
class DriverRecord:
    driver_index: int
    name: str
    team: str
    is_ai: bool
    car_number: int
    nationality: str | None
    platform: str | None
    is_telemetry_public: bool

@dataclass(frozen=True)
class LapMetadata:
    lap_number: int
    lap_time_ms: int | None
    valid: bool
    tyre_compound: str
    tyre_laps: int
    pit_in_lap: bool
    pit_out_lap: bool
    num_points: int
    is_good: bool

@dataclass(frozen=True)
class CompletedLap:
    metadata: LapMetadata
    telemetry: dict[str, list]  # "lap_distance" + sensor keys, all equal length

    def __post_init__(self) -> None:
        # Array-length agreement is an invariant of this telemetry dict alone -- doesn't
        # need the sensor registry or any other object, so it's checked here rather than
        # by write_session().
        lengths = {key: len(values) for key, values in self.telemetry.items()}
        if len(set(lengths.values())) > 1:
            raise ValueError(f"Mismatched telemetry array lengths for lap {self.metadata.lap_number}: {lengths}")

@dataclass(frozen=True)
class DriverExportData:
    driver_index: int
    completed_laps: list[CompletedLap]
    in_progress_lap: CompletedLap | None = None

    def __post_init__(self) -> None:
        # Whether a lap is "in progress" is this object's own structure (which field it's
        # assigned to), so the constraint that follows from that -- no final time, not
        # valid -- is this object's own invariant, not write_session()'s.
        if self.in_progress_lap is not None:
            meta = self.in_progress_lap.metadata
            if meta.lap_time_ms is not None or meta.valid:
                raise ValueError(
                    f"in_progress_lap {meta.lap_number} must have lap_time_ms=None and valid=False"
                )

@dataclass(frozen=True)
class DeleteLapsResult:
    driver_index: int
    deleted_lap_numbers: list[int]
    driver_folder_removed: bool
    new_laps_count: int
    new_session_best: SessionBest | None

@dataclass(frozen=True)
class MarkLapGoodResult:
    driver_index: int
    lap_number: int
    already_good: bool
