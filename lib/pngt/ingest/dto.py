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

@dataclass
class TelemetrySnapshot:
    """A strongly typed snapshot of all available sensor values at a single point in
    time, passed to DriverTelemetryRecorder.update() on every telemetry packet. The
    caller populates whatever fields the sim reported for this packet; the recorder
    filters internally to the sensors it was configured to record via SensorMapper.

    Ordered-int sensors (e.g. ERS deploy mode) are typed plain `int`, not an IntEnum --
    the enum itself is owned by whoever builds this snapshot from real sim packets, not
    by this layer. This layer never inspects the int's meaning, only stores it.
    """
    # Mandatory -- the x-axis for all sensor data
    lap_distance: float  # metres from start line

    # Driver inputs
    throttle: Optional[float] = None   # 0.0-1.0
    brake: Optional[float] = None      # 0.0-1.0
    steering: Optional[float] = None   # -1.0 (full left) to 1.0 (full right)
    clutch: Optional[float] = None     # 0.0-1.0

    # Vehicle state
    speed: Optional[float] = None      # km/h
    gear: Optional[int] = None         # 0 = reverse, 1-8 = forward
    engine_rpm: Optional[float] = None
    drs: Optional[int] = None          # 0 = off, 1 = on

    # ERS
    ers_deploy_mode: Optional[int] = None  # ERSDeployMode.value; enum owned by the producer
    ers_store_energy: Optional[float] = None
    ers_deployed_this_lap: Optional[float] = None
    ers_harvested_mguk: Optional[float] = None

    # Fuel
    fuel_mix: Optional[int] = None
    fuel_in_tank: Optional[float] = None
    fuel_remaining_laps: Optional[float] = None

    # Tyre temperatures
    tyre_inner_temp_fl: Optional[float] = None
    tyre_inner_temp_fr: Optional[float] = None
    tyre_inner_temp_rl: Optional[float] = None
    tyre_inner_temp_rr: Optional[float] = None
    tyre_surface_temp_fl: Optional[float] = None
    tyre_surface_temp_fr: Optional[float] = None
    tyre_surface_temp_rl: Optional[float] = None
    tyre_surface_temp_rr: Optional[float] = None

    # Tyre pressures
    tyre_pressure_fl: Optional[float] = None
    tyre_pressure_fr: Optional[float] = None
    tyre_pressure_rl: Optional[float] = None
    tyre_pressure_rr: Optional[float] = None

    # Tyre wear
    tyre_wear_fl: Optional[float] = None
    tyre_wear_fr: Optional[float] = None
    tyre_wear_rl: Optional[float] = None
    tyre_wear_rr: Optional[float] = None

    # Tyre damage
    tyre_damage_fl: Optional[float] = None
    tyre_damage_fr: Optional[float] = None
    tyre_damage_rl: Optional[float] = None
    tyre_damage_rr: Optional[float] = None

    # Brake temperatures
    brake_temp_fl: Optional[float] = None
    brake_temp_fr: Optional[float] = None
    brake_temp_rl: Optional[float] = None
    brake_temp_rr: Optional[float] = None

    # Suspension
    suspension_position_fl: Optional[float] = None
    suspension_position_fr: Optional[float] = None
    suspension_position_rl: Optional[float] = None
    suspension_position_rr: Optional[float] = None

    # G-forces
    g_force_lateral: Optional[float] = None
    g_force_longitudinal: Optional[float] = None
    g_force_vertical: Optional[float] = None

    # Engine
    engine_temperature: Optional[float] = None

    # Aero
    front_brake_bias: Optional[float] = None

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
    configured key against the mapper at construction, failing fast on an unknown one."""
    sensors: list[str]

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
