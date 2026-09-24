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

import os
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Union

import numpy as np

from .archive import HEADER_FORMAT, HEADER_VERSION, recompute_totals, write_json
from .dto import (CompletedLap, DriverExportData, DriverRecord, SensorConfig,
                  SessionMetadata)

# -------------------------------------- FUNCTIONS ----------------------------------------------------------------------

def write_session(
    dest_path: Union[Path, str],
    session: SessionMetadata,
    sensors: list[SensorConfig],
    drivers: list[DriverRecord],
    driver_data: dict[int, DriverExportData],
) -> Path:
    """Writes a complete .pngt file to dest_path.

    `sensors` is a top-level parameter, not part of `session` -- it maps to its own
    manifest.json entry. Every sensor is stored float32; NaN is the only missing
    value. `drivers` must include every driver, including restricted-telemetry
    ones; `driver_data` must have an entry for each driver whose telemetry was
    recorded -- that presence is what makes a driver "public" on disk, there is no
    separate flag to set.

    Derives and persists what the caller doesn't supply: each driver's
    is_telemetry_public (`driver_index in driver_data`), each lap's num_points
    (`len(telemetry["lap_distance"])`) and is_good (the fastest valid completed
    lap, unless overridden later via mark_lap_good()), and the session's
    laps_count/session_best (recompute_totals() over every driver's laps).

    Raises ValueError for anything that spans two independently-constructed
    arguments and so can't be caught by a constructor: a duplicate sensor key, an
    unregistered sensor key in a lap's telemetry, or a driver_data entry for a
    driver_index not present in `drivers`. session_type and tyre_compound are NOT
    validated against a fixed set -- see _validate_lap.
    """
    dest_path = Path(dest_path)

    _validate_sensors(sensors)
    _validate_driver_data(sensors, drivers, driver_data)

    driver_laps: dict[int, list[tuple[CompletedLap, bool]]] = {}
    driver_lap_dicts: dict[int, list[dict]] = {}
    for driver_index, data in driver_data.items():
        good_flags = _default_good_flags(data.completed_laps)
        laps = list(zip(data.completed_laps, good_flags))
        if data.in_progress_lap is not None:
            laps.append((data.in_progress_lap, False))
        driver_laps[driver_index] = laps
        driver_lap_dicts[driver_index] = [_lap_dict(lap, is_good) for lap, is_good in laps]

    laps_count, session_best = recompute_totals(driver_lap_dicts.items())

    tmp_path = dest_path.with_name(dest_path.name + ".tmp")
    with zipfile.ZipFile(tmp_path, "w") as zf:
        write_json(zf, "header.json", {"format": HEADER_FORMAT, "version": HEADER_VERSION})
        write_json(zf, "manifest.json", {
            "sensors": {
                sensor.key: {"label": sensor.label, "unit": sensor.unit, "type": sensor.type.value}
                for sensor in sensors
            }
        })
        write_json(zf, "session.json", _session_to_dict(session, laps_count, session_best))
        write_json(zf, "drivers.json", {
            "drivers": [_driver_to_dict(d, d.driver_index in driver_data) for d in drivers]
        })

        for driver_index, laps in driver_laps.items():
            folder = f"drivers/{driver_index:02d}"
            write_json(zf, f"{folder}/laps.json", {"laps": driver_lap_dicts[driver_index]})
            for lap, _ in laps:
                _write_lap_npz(zf, f"{folder}/lap_{lap.metadata.lap_number:03d}.npz", lap)

    os.replace(tmp_path, dest_path)
    return dest_path


def _default_good_flags(laps: list[CompletedLap]) -> list[bool]:
    """Marks the fastest valid+timed lap good; every other lap is not good."""
    valid_laps = [lap for lap in laps if lap.metadata.valid and lap.metadata.lap_time_ms is not None]
    if not valid_laps:
        return [False] * len(laps)
    fastest = min(valid_laps, key=lambda lap: lap.metadata.lap_time_ms)
    return [lap is fastest for lap in laps]


def _validate_sensors(sensors: list[SensorConfig]) -> None:
    # sensor.type's own validity is enforced by SensorConfig.__post_init__. Duplicate
    # keys are a property of the whole list, not any one SensorConfig, so that's all
    # that's left to check here.
    seen_keys = set()
    for sensor in sensors:
        if sensor.key in seen_keys:
            raise ValueError(f"Duplicate sensor key {sensor.key!r} in sensors")
        seen_keys.add(sensor.key)


def _validate_driver_data(
    sensors: list[SensorConfig],
    drivers: list[DriverRecord],
    driver_data: dict[int, DriverExportData],
) -> None:
    sensor_keys = {s.key for s in sensors}
    driver_indices = {d.driver_index for d in drivers}

    unknown = driver_data.keys() - driver_indices
    if unknown:
        raise ValueError(f"driver_data has entries for driver_index(es) not in drivers: {sorted(unknown)}")

    for data in driver_data.values():
        for lap in data.completed_laps:
            _validate_lap(lap, sensor_keys)
        if data.in_progress_lap is not None:
            _validate_lap(data.in_progress_lap, sensor_keys)


def _validate_lap(lap: CompletedLap, sensor_keys: set) -> None:
    # tyre_compound is deliberately NOT validated against a fixed set -- the format spec
    # gives it as illustrative examples, not a closed enum, keeping real-sim domain
    # knowledge out of this format-agnostic library (see _validate_sensors for the same
    # reasoning on session_type).
    unknown_keys = set(lap.telemetry.keys()) - sensor_keys - {"lap_distance", "lap_time_ms"}
    if unknown_keys:
        raise ValueError(
            f"Unregistered sensor key(s) in telemetry for lap {lap.metadata.lap_number}: {sorted(unknown_keys)}"
        )


def _session_to_dict(session: SessionMetadata, laps_count: int, session_best) -> dict:
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
            "count": laps_count,
            "session_best": None if session_best is None else {
                "driver_index": session_best.driver_index,
                "lap_number": session_best.lap_number,
                "lap_time_ms": session_best.lap_time_ms,
            },
        },
    }


def _driver_to_dict(driver: DriverRecord, is_telemetry_public: bool) -> dict:
    return {
        "driver_index": driver.driver_index,
        "name": driver.name,
        "team": driver.team,
        "car_number": driver.car_number,
        "nationality": driver.nationality,
        "platform": driver.platform,
        "is_telemetry_public": is_telemetry_public,
    }


def _lap_dict(lap: CompletedLap, is_good: bool) -> dict:
    metadata = lap.metadata
    return {
        "lap_number": metadata.lap_number,
        "lap_time_ms": metadata.lap_time_ms,
        "valid": metadata.valid,
        "tyre_compound": metadata.tyre_compound,
        "tyre_laps": metadata.tyre_laps,
        "pit_in_lap": metadata.pit_in_lap,
        "pit_out_lap": metadata.pit_out_lap,
        "num_points": len(lap.telemetry.get("lap_distance", [])),
        "is_good": is_good,
    }


def _write_lap_npz(zf: zipfile.ZipFile, name: str, lap: CompletedLap) -> None:
    arrays = {key: np.asarray(values, dtype=np.float32) for key, values in lap.telemetry.items()}
    buf = BytesIO()
    np.savez_compressed(buf, **arrays)
    zf.writestr(name, buf.getvalue(), compress_type=zipfile.ZIP_STORED)
