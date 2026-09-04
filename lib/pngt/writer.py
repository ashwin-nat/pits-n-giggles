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

import json
import os
import zipfile
from dataclasses import replace
from io import BytesIO
from pathlib import Path

import numpy as np

from .dto import (CompletedLap, DriverExportData, DriverRecord, SensorConfig,
                  SessionMetadata)
from .dtypes import SensorDtype, numpy_dtype
from .manifest import HEADER_FORMAT, HEADER_VERSION

# -------------------------------------- FUNCTIONS ----------------------------------------------------------------------

def write_session(
    dest_path: Path | str,
    session: SessionMetadata,
    sensors: list[SensorConfig],
    dtypes: dict[str, SensorDtype],
    drivers: list[DriverRecord],
    driver_data: dict[int, DriverExportData],
) -> Path:
    """Writes a complete .pngt file to dest_path.

    `sensors` is a top-level parameter, not part of `session` — it maps to its own
    manifest.json entry, distinct from session.json, so the Python API mirrors the
    on-disk split. `dtypes` maps each sensor's `key` to the NumPy dtype its telemetry
    values are cast to on write — a separate argument, not a field on SensorConfig,
    since dtype has no on-disk representation to give back on read; every sensor in
    `sensors` must have an entry here or write_session() fails fast with ValueError.
    `drivers` must include every driver, including restricted-telemetry ones.
    `driver_data` must have an entry for every driver with `is_telemetry_public ==
    True` and must not contain an entry for one with it `== False`.

    Validation is split by where the invariant actually lives: a single object's own
    invariant (sensor `type`, a lap's telemetry array lengths, an in_progress_lap
    claiming a final time/validity) raises ValueError from that object's own
    constructor, before write_session() is ever called — SensorConfig, CompletedLap,
    and DriverExportData all validate themselves. What's left for write_session() to
    check here is only what spans two independently-constructed arguments and so can't
    be caught any earlier: a sensor missing from `dtypes`, an unregistered sensor key
    in a lap's telemetry, or a driver_data/drivers mismatch. Either way, nothing is
    silently dropped or defaulted — every failure is a ValueError. session_type and
    tyre_compound are NOT validated against a fixed set — see the comments on
    _validate_sensors and _validate_lap.
    """
    dest_path = Path(dest_path)

    _validate_sensors(sensors, dtypes)
    _validate_driver_data(sensors, drivers, driver_data)

    tmp_path = dest_path.with_name(dest_path.name + ".tmp")
    with zipfile.ZipFile(tmp_path, "w") as zf:
        _write_json(zf, "header.json", {"format": HEADER_FORMAT, "version": HEADER_VERSION})
        _write_json(zf, "manifest.json", {
            "sensors": {
                sensor.key: {
                    "label": sensor.label,
                    "unit": sensor.unit, "type":
                    sensor.type.value,
                }
                for sensor in sensors
            }
        })
        _write_json(zf, "session.json", _session_to_dict(session))
        _write_json(zf, "drivers.json", {"drivers": [_driver_to_dict(d) for d in drivers]})

        for driver_index, data in driver_data.items():
            folder = f"drivers/{driver_index:02d}"
            completed_laps = _apply_default_good_lap(data.completed_laps)
            all_laps = list(completed_laps)
            if data.in_progress_lap is not None:
                all_laps.append(data.in_progress_lap)

            _write_json(zf, f"{folder}/laps.json", {"laps": [_lap_metadata_to_dict(lap.metadata) for lap in all_laps]})
            for lap in all_laps:
                _write_lap_npz(zf, f"{folder}/lap_{lap.metadata.lap_number:03d}.npz", dtypes, lap)

    os.replace(tmp_path, dest_path)
    return dest_path


def _apply_default_good_lap(laps: list[CompletedLap]) -> list[CompletedLap]:
    """Marks the fastest valid lap as good if no lap in this set is already
    marked good. Returns a new list; does not mutate the input."""
    if any(lap.metadata.is_good for lap in laps):
        return laps

    valid_laps = [lap for lap in laps if lap.metadata.valid and lap.metadata.lap_time_ms is not None]
    if not valid_laps:
        return laps

    fastest = min(valid_laps, key=lambda lap: lap.metadata.lap_time_ms)
    return [
        lap if lap is not fastest
        else CompletedLap(metadata=replace(lap.metadata, is_good=True), telemetry=lap.telemetry)
        for lap in laps
    ]


def _validate_sensors(sensors: list[SensorConfig], dtypes: dict[str, SensorDtype]) -> None:
    # sensor.type's own validity is enforced by SensorConfig's own __post_init__ -- it's
    # an invariant of that object alone. What's left here can't move to a constructor:
    # `sensors` and `dtypes` are two independent write_session() arguments, so agreement
    # between them can only be checked once both exist together.
    for sensor in sensors:
        if sensor.key not in dtypes:
            raise ValueError(f"Sensor {sensor.key!r} has no entry in dtypes; dtype is required for write_session()")


def _validate_driver_data(
    sensors: list[SensorConfig],
    drivers: list[DriverRecord],
    driver_data: dict[int, DriverExportData],
) -> None:
    sensor_keys = {s.key for s in sensors}
    restricted = {d.driver_index for d in drivers if not d.is_telemetry_public}
    public = {d.driver_index for d in drivers if d.is_telemetry_public}

    missing = public - driver_data.keys()
    if missing:
        raise ValueError(f"driver_data is missing entries for public-telemetry drivers: {sorted(missing)}")

    restricted_present = restricted & driver_data.keys()
    if restricted_present:
        raise ValueError(f"driver_data must not contain restricted-telemetry drivers: {sorted(restricted_present)}")

    for data in driver_data.values():
        for lap in data.completed_laps:
            _validate_lap(lap, sensor_keys)
        if data.in_progress_lap is not None:
            _validate_lap(data.in_progress_lap, sensor_keys)


def _validate_lap(lap: CompletedLap, sensor_keys: set) -> None:
    # tyre_compound is deliberately NOT validated against a fixed set here -- the format
    # spec gives it as illustrative examples ("e.g. Soft, Medium, Hard, Inter, Wet"), not a
    # closed enum. Enforcing a compound list would bake real-sim domain knowledge into
    # this format-agnostic library (see _validate_sensors for the same reasoning on
    # session_type). The in_progress_lap time/valid constraint and telemetry array-length
    # agreement are invariants of a single object (DriverExportData, CompletedLap
    # respectively) and are enforced by their own __post_init__ instead of here. What's
    # left is a genuinely cross-object check: a telemetry key must exist in the sensor
    # registry, which is a separate write_session() argument this lap doesn't know about.
    unknown_keys = set(lap.telemetry.keys()) - sensor_keys - {"lap_distance"}
    if unknown_keys:
        raise ValueError(
            f"Unregistered sensor key(s) in telemetry for lap {lap.metadata.lap_number}: {sorted(unknown_keys)}"
        )


def _session_to_dict(session: SessionMetadata) -> dict:
    return {
        "session_uid": session.session_uid,
        "session_name": session.session_name,
        "session_type": session.session_type,
        "app_version": session.app_version,
        "game_year": session.game_year,
        "formula": session.formula,
        "game_version": session.game_version,
        "timestamp": session.timestamp,
        "track": {
            "id": session.track.id,
            "name": session.track.name,
        },
        "laps": {
            "count": session.laps_count,
            "session_best": None if session.session_best is None else {
                "driver_index": session.session_best.driver_index,
                "lap_number": session.session_best.lap_number,
                "lap_time_ms": session.session_best.lap_time_ms,
            },
        },
    }


def _driver_to_dict(driver: DriverRecord) -> dict:
    return {
        "driver_index": driver.driver_index,
        "name": driver.name,
        "team": driver.team,
        "is_ai": driver.is_ai,
        "car_number": driver.car_number,
        "nationality": driver.nationality,
        "platform": driver.platform,
        "is_telemetry_public": driver.is_telemetry_public,
    }


def _lap_metadata_to_dict(metadata) -> dict:
    return {
        "lap_number": metadata.lap_number,
        "lap_time_ms": metadata.lap_time_ms,
        "valid": metadata.valid,
        "tyre_compound": metadata.tyre_compound,
        "tyre_laps": metadata.tyre_laps,
        "pit_in_lap": metadata.pit_in_lap,
        "pit_out_lap": metadata.pit_out_lap,
        "num_points": metadata.num_points,
        "is_good": metadata.is_good,
    }


def _write_json(zf: zipfile.ZipFile, name: str, data: dict) -> None:
    zf.writestr(name, json.dumps(data).encode("utf-8"), compress_type=zipfile.ZIP_DEFLATED)


def _write_lap_npz(zf: zipfile.ZipFile, name: str, dtypes: dict[str, SensorDtype], lap: CompletedLap) -> None:
    arrays = {}
    for key, values in lap.telemetry.items():
        dtype = np.float32 if key == "lap_distance" else numpy_dtype(dtypes[key])
        arrays[key] = np.asarray(values, dtype=dtype)

    buf = BytesIO()
    np.savez(buf, **arrays)
    zf.writestr(name, buf.getvalue(), compress_type=zipfile.ZIP_STORED)
