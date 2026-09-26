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
import zipfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Union

import numpy as np

from .archive import SENSOR_MANIFEST_ENTRY, read_json, validate_pngt_zip
from .dto import (ParsedDriver, ParsedLap, ParsedSessionMetadata,
                  SensorConfig, SensorType, SessionBest, TrackInfo)
from .exceptions import (CorruptedTelemetryError, DriverNotFoundError,
                         InvalidManifestError, MalformedSessionError)

# -------------------------------------- CLASSES -----------------------------------------------------------------------

@dataclass(frozen=True)
class ParsedSession:
    session: ParsedSessionMetadata
    drivers: list[ParsedDriver]
    sensors: list[SensorConfig]

# -------------------------------------- FUNCTIONS ----------------------------------------------------------------------

def read_session(path: Union[Path, str]) -> ParsedSession:
    """Reads header.json + manifest.json + session.json + drivers.json into a
    ParsedSession. Raises NotAZipFileError/InvalidHeaderError/UnsupportedFormatError/
    UnsupportedVersionError/InvalidManifestError/MalformedSessionError."""
    zf = validate_pngt_zip(path)
    try:
        session_raw = read_json(zf, "session.json", path)
        drivers_raw = read_json(zf, "drivers.json", path)
        sensors = _read_sensor_manifest(zf, path)
        session = _dict_to_session(session_raw, path)
        drivers = [_dict_to_driver(d, path) for d in drivers_raw.get("drivers", [])]
        return ParsedSession(session=session, drivers=drivers, sensors=sensors)
    finally:
        zf.close()


def read_driver_laps(path: Union[Path, str], driver_index: int) -> list[ParsedLap]:
    """Reads lap metadata for one driver. A Restricted driver has no folder on disk --
    this is expected, documented behavior, so it returns [] rather than raising."""
    zf = validate_pngt_zip(path)
    try:
        entry = f"drivers/{driver_index:02d}/laps.json"
        if entry not in zf.namelist():
            return []
        laps_raw = read_json(zf, entry, path)
        return [_dict_to_lap_metadata(lap, path) for lap in laps_raw.get("laps", [])]
    finally:
        zf.close()


def read_lap_telemetry(path: Union[Path, str], driver_index: int, lap_number: int) -> dict:
    """Reads one lap's telemetry arrays. Returns exactly the array names present in
    that .npz file -- an older file with fewer sensors or a newer one with extra
    sensor keys both work with zero special-case code."""
    zf = validate_pngt_zip(path)
    try:
        entry = f"drivers/{driver_index:02d}/lap_{lap_number:03d}.npz"
        try:
            raw = zf.read(entry)
        except KeyError as exc:
            raise DriverNotFoundError(path, driver_index) from exc
        try:
            with np.load(BytesIO(raw)) as npz:
                return {name: npz[name] for name in npz.files}
        except (zipfile.BadZipFile, ValueError, OSError, EOFError) as exc:
            raise CorruptedTelemetryError(path, driver_index, lap_number, str(exc)) from exc
    finally:
        zf.close()


def _read_sensor_manifest(zf: zipfile.ZipFile, path) -> list[SensorConfig]:
    try:
        raw_bytes = zf.read(SENSOR_MANIFEST_ENTRY)
    except KeyError as exc:
        raise InvalidManifestError(path, f"{SENSOR_MANIFEST_ENTRY} is missing") from exc
    try:
        raw = json.loads(raw_bytes)
    except json.JSONDecodeError as exc:
        raise InvalidManifestError(path, f"{SENSOR_MANIFEST_ENTRY} is not valid JSON: {exc}") from exc
    try:
        return [
            SensorConfig(
                key=key,
                label=meta["label"],
                unit=meta["unit"],
                type=SensorType(meta["type"]),
                range=tuple(meta["range"]) if "range" in meta else None,
            )
            for key, meta in raw.get("sensors", {}).items()
        ]
    except KeyError as exc:
        raise InvalidManifestError(path, f"sensor entry missing required field {exc}") from exc
    except ValueError as exc:
        raise InvalidManifestError(path, f"sensor entry has an invalid 'type': {exc}") from exc


def _dict_to_session(raw: dict, path) -> ParsedSessionMetadata:
    try:
        track_raw = raw["track"]
        laps_raw = raw["laps"]
        session_best_raw = laps_raw.get("session_best")
        return ParsedSessionMetadata(
            session_uid=raw["session_uid"],
            session_name=raw["session_name"],
            session_type=raw["session_type"],
            app_version=raw["app_version"],
            game_year=raw["game_year"],
            formula=raw["formula"],
            game_version=raw["game_version"],
            timestamp=raw["timestamp"],
            track=TrackInfo(id=track_raw["id"], name=track_raw["name"]),
            laps_count=laps_raw["count"],
            session_best=None if session_best_raw is None else SessionBest(
                driver_index=session_best_raw["driver_index"],
                lap_number=session_best_raw["lap_number"],
                lap_time_ms=session_best_raw["lap_time_ms"],
            ),
        )
    except KeyError as exc:
        raise MalformedSessionError(path, f"session.json missing required field {exc}") from exc


def _dict_to_driver(raw: dict, path) -> ParsedDriver:
    try:
        return ParsedDriver(
            driver_index=raw["driver_index"],
            name=raw["name"],
            team=raw["team"],
            car_number=raw["car_number"],
            nationality=raw.get("nationality"),
            platform=raw.get("platform"),
            is_telemetry_public=raw["is_telemetry_public"],
        )
    except KeyError as exc:
        raise MalformedSessionError(path, f"drivers.json entry missing required field {exc}") from exc


def _dict_to_lap_metadata(raw: dict, path) -> ParsedLap:
    try:
        return ParsedLap(
            lap_number=raw["lap_number"],
            lap_time_ms=raw.get("lap_time_ms"),
            valid=raw["valid"],
            tyre_compound=raw["tyre_compound"],
            tyre_laps=raw["tyre_laps"],
            pit_in_lap=raw["pit_in_lap"],
            pit_out_lap=raw["pit_out_lap"],
            num_points=raw["num_points"],
            is_good=raw["is_good"],
        )
    except KeyError as exc:
        raise MalformedSessionError(path, f"laps.json entry missing required field {exc}") from exc
