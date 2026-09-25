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
from pathlib import Path
from typing import Iterable, Optional, Union

from .dto import SessionBest
from .exceptions import (InvalidHeaderError, MalformedSessionError,
                         NotAZipFileError, UnsupportedFormatError,
                         UnsupportedVersionError)

# -------------------------------------- CONSTANTS ----------------------------------------------------------------------

HEADER_FORMAT = "pngt"
HEADER_VERSION = 1
HEADER_ENTRY = "header.json"
SENSOR_MANIFEST_ENTRY = "manifest.json"
ZIP_MAGIC = b"PK\x03\x04"

# -------------------------------------- FUNCTIONS ----------------------------------------------------------------------

def validate_pngt_zip(path: Union[Path, str]) -> zipfile.ZipFile:
    """Sniffs ZIP magic bytes, opens as a ZipFile, reads header.json, checks format
    then version. Returns the open ZipFile; the caller is responsible for closing it.

    Raises NotAZipFileError / InvalidHeaderError / UnsupportedFormatError /
    UnsupportedVersionError.
    """
    path = Path(path)

    with open(path, "rb") as f:
        magic = f.read(4)
    if magic != ZIP_MAGIC:
        raise NotAZipFileError(path)

    try:
        zf = zipfile.ZipFile(path)  # pylint: disable=consider-using-with
    except zipfile.BadZipFile as exc:
        raise NotAZipFileError(path) from exc

    try:
        raw = zf.read(HEADER_ENTRY)
    except KeyError as exc:
        zf.close()
        raise InvalidHeaderError(path, f"{HEADER_ENTRY} is missing") from exc
    except zipfile.BadZipFile as exc:
        zf.close()
        raise NotAZipFileError(path) from exc

    try:
        header = json.loads(raw)
    except json.JSONDecodeError as exc:
        zf.close()
        raise InvalidHeaderError(path, f"{HEADER_ENTRY} is not valid JSON: {exc}") from exc

    if not isinstance(header, dict) or "format" not in header or "version" not in header:
        zf.close()
        raise InvalidHeaderError(path, f"{HEADER_ENTRY} is missing required keys 'format'/'version'")

    actual_format = header["format"]
    if actual_format != HEADER_FORMAT:
        zf.close()
        raise UnsupportedFormatError(path, actual_format)

    actual_version = header["version"]
    if actual_version != HEADER_VERSION:
        zf.close()
        raise UnsupportedVersionError(path, actual_version, HEADER_VERSION)

    return zf


def recompute_totals(driver_laps: Iterable[tuple[int, list[dict]]]) -> tuple[int, Optional[SessionBest]]:
    """Given each driver's lap dicts (as written to laps.json), returns the total
    lap count across all drivers and the fastest valid+timed lap as SessionBest (or
    None if no lap qualifies). Used by both write_session() and delete_laps(), so
    laps.count always means the same thing regardless of which one last touched
    the file."""
    total = 0
    best_driver = best_lap = best_time = None

    for driver_index, laps in driver_laps:
        total += len(laps)
        for lap in laps:
            if lap.get("valid") and lap.get("lap_time_ms") is not None:
                if best_time is None or lap["lap_time_ms"] < best_time:
                    best_time = lap["lap_time_ms"]
                    best_driver = driver_index
                    best_lap = lap["lap_number"]

    session_best = None if best_time is None else SessionBest(
        driver_index=best_driver, lap_number=best_lap, lap_time_ms=best_time
    )
    return total, session_best


def session_best_to_dict(best: Optional[SessionBest]) -> Optional[dict]:
    """session.json's laps.session_best shape. Shared by write_session() and
    delete_laps() so the two can't drift into writing different shapes for it."""
    return None if best is None else {
        "driver_index": best.driver_index,
        "lap_number": best.lap_number,
        "lap_time_ms": best.lap_time_ms,
    }


def read_json(zf: zipfile.ZipFile, name: str, path) -> dict:
    try:
        raw = zf.read(name)
    except KeyError as exc:
        raise MalformedSessionError(path, f"{name} is missing") from exc
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise MalformedSessionError(path, f"{name} is not valid JSON: {exc}") from exc


def write_json(zf: zipfile.ZipFile, name: str, data: dict) -> None:
    zf.writestr(name, json.dumps(data).encode("utf-8"), compress_type=zipfile.ZIP_DEFLATED)


def rebuild_archive(
    src_path: Path,
    dest_path: Path,
    *,
    skip_names: set,
    overrides: dict,
) -> None:
    """Copies every entry from src_path into a new archive at dest_path, skipping
    skip_names and replacing the content of any entry named in overrides with its
    (JSON-serialized) value. Every other entry is copied byte-for-byte, preserving
    its original compression type."""
    with zipfile.ZipFile(src_path) as src_zf, zipfile.ZipFile(dest_path, "w") as dst_zf:
        for name in src_zf.namelist():
            if name in overrides:
                write_json(dst_zf, name, overrides[name])
            elif name not in skip_names:
                info = src_zf.getinfo(name)
                dst_zf.writestr(name, src_zf.read(name), compress_type=info.compress_type)
