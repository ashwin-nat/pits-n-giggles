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
from pathlib import Path

from .dto import DeleteLapsResult, MarkLapGoodResult, SessionBest
from .exceptions import DriverNotFoundError, MalformedSessionError
from .manifest import validate_pngt_zip

# -------------------------------------- FUNCTIONS ----------------------------------------------------------------------

def delete_laps(
    pngt_path: Path | str,
    driver_index: int,
    lap_numbers: list[int],
) -> DeleteLapsResult:
    """Removes the specified laps for one driver from a .pngt file.

    Full archive rebuild — ZIP has no true delete. Atomic: writes to a .tmp file,
    only replaces the original via os.replace() once the rebuild succeeds.

    Raises DriverNotFoundError if driver_index has no folder in the archive.
    Raises ValueError if lap_numbers is empty, or contains a lap number not
    present in that driver's laps.json.
    """
    path = Path(pngt_path)
    if not lap_numbers:
        raise ValueError("lap_numbers must not be empty")

    zf = validate_pngt_zip(path)
    try:
        folder = f"drivers/{driver_index:02d}"
        laps_entry = f"{folder}/laps.json"
        if laps_entry not in zf.namelist():
            raise DriverNotFoundError(path, driver_index)

        existing_laps = _read_json(zf, laps_entry, path).get("laps", [])
        existing_numbers = {lap["lap_number"] for lap in existing_laps}
        to_delete = set(lap_numbers)
        missing = sorted(to_delete - existing_numbers)
        if missing:
            raise ValueError(f"Lap number(s) not found for driver {driver_index}: {missing}")

        remaining_laps = [lap for lap in existing_laps if lap["lap_number"] not in to_delete]
        driver_folder_removed = not remaining_laps

        session_raw = _read_json(zf, "session.json", path)
        drivers_raw = _read_json(zf, "drivers.json", path)
        new_laps_count, new_session_best = _recompute_session_totals(
            zf, path, drivers_raw, driver_index, remaining_laps
        )
        all_names = zf.namelist()
    finally:
        # Must be closed before the rebuild's os.replace() -- an open handle on `path`
        # blocks renaming over it on Windows.
        zf.close()

    session_raw["laps"]["count"] = new_laps_count
    session_raw["laps"]["session_best"] = None if new_session_best is None else {
        "driver_index": new_session_best.driver_index,
        "lap_number": new_session_best.lap_number,
        "lap_time_ms": new_session_best.lap_time_ms,
    }

    skip_names = {"session.json"}
    overrides = {"session.json": session_raw}
    if driver_folder_removed:
        skip_names |= {name for name in all_names if name.startswith(f"{folder}/")}
    else:
        skip_names.add(laps_entry)
        overrides[laps_entry] = {"laps": remaining_laps}
        skip_names |= {f"{folder}/lap_{n:03d}.npz" for n in to_delete}

    tmp_path = path.with_name(path.name + ".tmp")
    _rebuild_archive(path, tmp_path, skip_names=skip_names, overrides=overrides)
    os.replace(tmp_path, path)

    return DeleteLapsResult(
        driver_index=driver_index,
        deleted_lap_numbers=sorted(to_delete),
        driver_folder_removed=driver_folder_removed,
        new_laps_count=new_laps_count,
        new_session_best=new_session_best,
    )


def mark_lap_good(
    pngt_path: Path | str,
    driver_index: int,
    lap_number: int,
) -> MarkLapGoodResult:
    """Sets is_good=True for the specified lap. No-op if already True.

    Does NOT support unmarking — there is no parameter or code path in this
    function that can set is_good back to False. If unmarking is ever needed,
    it must be a new, separate function.

    Raises DriverNotFoundError if driver_index has no folder in the archive.
    Raises ValueError if lap_number is not present in that driver's laps.json.
    """
    path = Path(pngt_path)
    zf = validate_pngt_zip(path)
    try:
        folder = f"drivers/{driver_index:02d}"
        laps_entry = f"{folder}/laps.json"
        if laps_entry not in zf.namelist():
            raise DriverNotFoundError(path, driver_index)

        laps = _read_json(zf, laps_entry, path).get("laps", [])
    finally:
        # Must be closed before the rebuild's os.replace() -- an open handle on `path`
        # blocks renaming over it on Windows.
        zf.close()

    target = next((lap for lap in laps if lap["lap_number"] == lap_number), None)
    if target is None:
        raise ValueError(f"Lap number {lap_number} not found for driver {driver_index}")

    if target.get("is_good"):
        return MarkLapGoodResult(driver_index=driver_index, lap_number=lap_number, already_good=True)

    target["is_good"] = True
    tmp_path = path.with_name(path.name + ".tmp")
    _rebuild_archive(path, tmp_path, skip_names={laps_entry}, overrides={laps_entry: {"laps": laps}})
    os.replace(tmp_path, path)

    return MarkLapGoodResult(driver_index=driver_index, lap_number=lap_number, already_good=False)


def rename_session(
    pngt_path: Path | str,
    new_name: str,
) -> None:
    """Sets session.json's session_name to new_name. session_uid and every other
    field are untouched."""
    path = Path(pngt_path)
    zf = validate_pngt_zip(path)
    try:
        session_raw = _read_json(zf, "session.json", path)
    finally:
        zf.close()

    session_raw["session_name"] = new_name
    tmp_path = path.with_name(path.name + ".tmp")
    _rebuild_archive(path, tmp_path, skip_names={"session.json"}, overrides={"session.json": session_raw})
    os.replace(tmp_path, path)


def _read_json(zf: zipfile.ZipFile, name: str, path) -> dict:
    try:
        raw = zf.read(name)
    except KeyError as exc:
        raise MalformedSessionError(path, f"{name} is missing") from exc
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise MalformedSessionError(path, f"{name} is not valid JSON: {exc}") from exc


def _write_json(zf: zipfile.ZipFile, name: str, data: dict) -> None:
    zf.writestr(name, json.dumps(data).encode("utf-8"), compress_type=zipfile.ZIP_DEFLATED)


def _recompute_session_totals(
    zf: zipfile.ZipFile,
    path,
    drivers_raw: dict,
    changed_driver_index: int,
    changed_driver_laps: list[dict],
) -> tuple[int, SessionBest | None]:
    """Recomputes laps.count and session_best across every driver, using
    changed_driver_laps in place of changed_driver_index's on-disk laps.json
    (which hasn't been rewritten yet) and reading every other driver's laps.json
    from the still-open archive."""
    total = 0
    best_driver = None
    best_lap = None
    best_time = None

    for driver in drivers_raw.get("drivers", []):
        idx = driver["driver_index"]
        if idx == changed_driver_index:
            laps = changed_driver_laps
        else:
            entry = f"drivers/{idx:02d}/laps.json"
            if entry not in zf.namelist():
                continue
            laps = _read_json(zf, entry, path).get("laps", [])

        total += len(laps)
        for lap in laps:
            if lap.get("valid") and lap.get("lap_time_ms") is not None:
                if best_time is None or lap["lap_time_ms"] < best_time:
                    best_time = lap["lap_time_ms"]
                    best_driver = idx
                    best_lap = lap["lap_number"]

    session_best = None if best_time is None else SessionBest(
        driver_index=best_driver, lap_number=best_lap, lap_time_ms=best_time
    )
    return total, session_best


def _rebuild_archive(
    src_path: Path,
    dest_path: Path,
    *,
    skip_names: set,
    overrides: dict,
) -> None:
    """Copies every entry from src_path into a new archive at dest_path, skipping
    skip_names entirely and replacing the content of any entry named in overrides
    with its (JSON-serialized) value. Every other entry is copied byte-for-byte,
    preserving its original compression type."""
    with zipfile.ZipFile(src_path) as src_zf, zipfile.ZipFile(dest_path, "w") as dst_zf:
        for name in src_zf.namelist():
            if name in overrides:
                _write_json(dst_zf, name, overrides[name])
            elif name not in skip_names:
                info = src_zf.getinfo(name)
                dst_zf.writestr(name, src_zf.read(name), compress_type=info.compress_type)
