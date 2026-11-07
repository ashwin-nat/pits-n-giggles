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

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

MANDATORY_TELEMETRY_KEYS = ("lap_distance", "lap_time_ms")
SESSION_DATA_DIR = "session_data"

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class SensorType(Enum):
    """How the viewer must interpolate this sensor's values between samples."""
    CONTINUOUS = "continuous"
    DISCRETE = "discrete"

@dataclass(frozen=True)
class SensorConfig:
    """A sensor registry entry: manifest.json's {key: {label, unit, type, range?}}. Every
    sensor's values are stored float32 on disk; there is no dtype field. `range`, when
    given, is the sensor's known-fixed (min, max) -- e.g. throttle/brake are 0-100 -- and
    is a hint for viewers (axis scaling); it is not enforced against recorded values."""
    key: str
    label: str
    unit: str
    type: SensorType
    range: Optional[tuple[float, float]] = None
    should_display: Optional[bool] = True

    def __post_init__(self) -> None:
        if not isinstance(self.type, SensorType):
            raise ValueError(f"Invalid sensor type {self.type!r} for sensor {self.key!r}; expected a SensorType")
        if self.range is not None and self.range[0] >= self.range[1]:
            raise ValueError(f"Invalid range {self.range!r} for sensor {self.key!r}; expected (min, max) with min < max")

@dataclass(frozen=True)
class SessionDataEntry:
    """An opaque caller-owned blob, stored as `session_data/<file_name>` (the `session_data` section).
    `file_name` is a plain file name like "<stem>.json"; the library never parses `payload`."""
    file_name: str
    payload: bytes

    def __post_init__(self) -> None:
        if not self.file_name or self.file_name in {".", ".."} or "/" in self.file_name or "\\" in self.file_name:
            raise ValueError(f"Invalid session data file name {self.file_name!r}; expected a plain file name")

    @property
    def entry_name(self) -> str:
        """The entry's path inside the archive."""
        return f"{SESSION_DATA_DIR}/{self.file_name}"

@dataclass(frozen=True)
class LapTelemetryPaths:
    """Where the lap_telemetry section's entries are in the archive. header.json lists them under
    `contents.lap_telemetry` for completeness; readers use these fixed names, not the header's.

    Attributes:
        session (str): Session metadata JSON.
        sensor_manifest (str): Sensor registry JSON.
        drivers (str): Driver list JSON.
        drivers_dir (str): Directory of per-driver folders, each holding laps.json and the lap_NNN.npz files.
    """
    session: str = "session.json"
    sensor_manifest: str = "manifest.json"
    drivers: str = "drivers.json"
    drivers_dir: str = "drivers"

    def driver_dir(self, driver_index: int) -> str:
        return f"{self.drivers_dir}/{driver_index:02d}"

    def laps_entry(self, driver_index: int) -> str:
        return f"{self.driver_dir(driver_index)}/laps.json"

    def lap_entry(self, driver_index: int, lap_number: int) -> str:
        return f"{self.driver_dir(driver_index)}/lap_{lap_number:03d}.npz"

@dataclass(frozen=True)
class PngtContents:
    """Which sections a .pngt file holds.

    Attributes:
        has_lap_telemetry (bool): The file holds a lap recording.
        session_data_entry (Optional[str]): Archive entry name of the session JSON, None if the file has none.
    """
    has_lap_telemetry: bool
    session_data_entry: Optional[str]

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
    """Caller-filled session identity. laps_count/session_best are write_session()-
    derived, not part of this input type -- see ParsedSessionMetadata."""
    session_uid: int
    session_name: str
    session_type: str
    app_version: str
    game_year: int
    formula: str
    game_version: str
    timestamp: str  # ISO-8601, passed through verbatim, never parsed
    track: TrackInfo
    # Lap length in metres. kw_only so ParsedSessionMetadata can keep adding required
    # fields after it; None in files written before this existed, or when unknown.
    track_length_m: Optional[int] = field(default=None, kw_only=True)
    # The recording player's driver index, the lap distances where sectors 2 and 3 start,
    # and the battery size in joules. None when unknown.
    player_index: Optional[int] = field(default=None, kw_only=True)
    sector_starts_m: Optional[tuple[float, float]] = field(default=None, kw_only=True)
    ers_max_capacity_j: Optional[float] = field(default=None, kw_only=True)

@dataclass(frozen=True)
class DriverRecord:
    """Caller-filled driver identity. is_telemetry_public is write_session()-derived
    from whether driver_index is a key in driver_data -- see ParsedDriver."""
    driver_index: int
    name: str
    team: str
    car_number: int
    nationality: Optional[str]
    platform: Optional[str]

@dataclass(frozen=True)
class LapMetadata:
    """Caller-filled lap facts. num_points/is_good are write_session()-derived --
    see ParsedLap."""
    lap_number: int
    lap_time_ms: Optional[int]
    valid: bool
    tyre_compound: str
    tyre_laps: int
    pit_in_lap: bool
    pit_out_lap: bool
    ers_harvest_limit_j: Optional[float]  # None in recordings made before this field existed
    # Official elapsed time (ms) at the end of sectors 1 and 2; None when the lap has no trustworthy splits.
    sector_ends_ms: Optional[tuple[int, int]] = field(default=None, kw_only=True)

@dataclass(frozen=True)
class CompletedLap:
    metadata: LapMetadata
    telemetry: dict[str, list]  # "lap_distance" + "lap_time_ms" + sensor keys, all equal length

    def __post_init__(self) -> None:
        lengths = {key: len(values) for key, values in self.telemetry.items()}
        if len(set(lengths.values())) > 1:
            raise ValueError(f"Mismatched telemetry array lengths for lap {self.metadata.lap_number}: {lengths}")

@dataclass(frozen=True)
class DriverExportData:
    driver_index: int
    completed_laps: list[CompletedLap]
    in_progress_lap: Optional[CompletedLap] = None

    def __post_init__(self) -> None:
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
    new_session_best: Optional[SessionBest]

@dataclass(frozen=True)
class MarkLapGoodResult:
    driver_index: int
    lap_number: int
    already_good: bool

# -------------------------------------- READ-SIDE TYPES ----------------------------------------------------------------

@dataclass(frozen=True)
class ParsedSessionMetadata(SessionMetadata):
    """SessionMetadata plus the fields write_session() derives and persists."""
    laps_count: int
    session_best: Optional[SessionBest]

@dataclass(frozen=True)
class ParsedDriver(DriverRecord):
    """DriverRecord plus the field write_session() derives and persists."""
    is_telemetry_public: bool

@dataclass(frozen=True)
class ParsedLap(LapMetadata):
    """LapMetadata plus the fields write_session() derives and persists."""
    num_points: int
    is_good: bool
    # Distance coverage, persisted at write time. None in files written before these
    # existed; consumers fall back to measuring the lap's own lap_distance array.
    start_distance_m: Optional[float] = None
    end_distance_m: Optional[float] = None
    max_gap_m: Optional[float] = None
