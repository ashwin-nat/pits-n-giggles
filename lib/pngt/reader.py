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
import orjson

from .archive import (CONTENT_SESSION_DATA, SENSOR_MANIFEST_ENTRY,
                      open_lap_telemetry_zip, read_contents_from_zip,
                      read_json, validate_pngt_zip)
from .dto import (ParsedDriver, ParsedLap, ParsedSessionMetadata,
                  PngtContents, SensorConfig, SensorType, SessionBest,
                  TrackInfo)
from .exceptions import (CorruptedTelemetryError, DriverNotFoundError,
                         InvalidManifestError, MalformedSessionError,
                         SectionNotPresentError)

# -------------------------------------- CLASSES -----------------------------------------------------------------------

@dataclass(frozen=True)
class ParsedSession:
    session: ParsedSessionMetadata
    drivers: list[ParsedDriver]
    sensors: list[SensorConfig]

# -------------------------------------- FUNCTIONS ----------------------------------------------------------------------

def read_contents(path: Union[Path, str]) -> PngtContents:
    """Which sections the file holds, from header.json alone. Raises NotAZipFileError/
    InvalidHeaderError/UnsupportedFormatError/UnsupportedVersionError."""
    zf = validate_pngt_zip(path)
    try:
        return read_contents_from_zip(zf, path)
    finally:
        zf.close()


def read_session_data(path: Union[Path, str]) -> dict:
    """The session_data section, parsed. The library enforces no schema beyond it being a JSON
    object. Raises SectionNotPresentError if the file has none, MalformedSessionError if the header
    names an entry the archive lacks or the entry is not a JSON object.

    NOTE: This function will just ensure that the JSON parses into a dict.
    It does not validate the contents of the dict against any schema.
    The caller is responsible for validating the contents if needed.
    """
    zf = validate_pngt_zip(path)
    try:
        entry = read_contents_from_zip(zf, path).session_data_entry
        if entry is None:
            raise SectionNotPresentError(path, CONTENT_SESSION_DATA)
        try:
            raw = zf.read(entry)
        except KeyError as exc:
            raise MalformedSessionError(path, f"{entry} is missing") from exc
        try:
            data = orjson.loads(raw)
        except orjson.JSONDecodeError as exc:
            raise MalformedSessionError(path, f"{entry} is not valid JSON: {exc}") from exc
        if not isinstance(data, dict):
            raise MalformedSessionError(path, f"{entry} is not a JSON object")
        return data
    finally:
        zf.close()


def read_session(path: Union[Path, str]) -> ParsedSession:
    """Reads header.json + manifest.json + session.json + drivers.json into a
    ParsedSession. Raises NotAZipFileError/InvalidHeaderError/UnsupportedFormatError/
    UnsupportedVersionError/SectionNotPresentError/InvalidManifestError/MalformedSessionError."""
    zf = open_lap_telemetry_zip(path)
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
    zf = open_lap_telemetry_zip(path)
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
    zf = open_lap_telemetry_zip(path)
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


def read_lap_npz_bytes(path: Union[Path, str], driver_index: int, lap_number: int) -> bytes:
    """Returns one lap's `.npz` exactly as stored, for clients that decode it themselves.
    Raises DriverNotFoundError when that driver/lap entry does not exist."""
    zf = validate_pngt_zip(path)
    try:
        try:
            return zf.read(f"drivers/{driver_index:02d}/lap_{lap_number:03d}.npz")
        except KeyError as exc:
            raise DriverNotFoundError(path, driver_index) from exc
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
                should_display=meta.get("should_display", True),
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
            track_length_m=raw.get("track_length_m"),
            player_index=raw.get("player_index"),
            sector_starts_m=None if raw.get("sector_starts_m") is None else tuple(raw["sector_starts_m"]),
            ers_max_capacity_j=raw.get("ers_max_capacity_j"),
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
            ers_harvest_limit_j=raw.get("ers_harvest_limit_j"),
            sector_ends_ms=None if raw.get("sector_ends_ms") is None else tuple(raw["sector_ends_ms"]),
            num_points=raw["num_points"],
            is_good=raw["is_good"],
            start_distance_m=raw.get("start_distance_m"),
            end_distance_m=raw.get("end_distance_m"),
            max_gap_m=raw.get("max_gap_m"),
        )
    except KeyError as exc:
        raise MalformedSessionError(path, f"laps.json entry missing required field {exc}") from exc
