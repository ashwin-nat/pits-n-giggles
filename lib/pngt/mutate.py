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

"""
This module is not thread-safe or process-safe. Locking is the consumer's
responsibility, if needed.

Every function here is synchronous, blocking disk I/O (a full archive rebuild for
delete_laps/mark_lap_good/rename_session). An async caller must not call these
directly on the event loop -- wrap with asyncio.to_thread(), as
apps/web/session_discovery.py already does for its own sync disk-heavy functions.
"""

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

import os
from pathlib import Path
from typing import Iterator, Union

from .archive import read_json, rebuild_archive, recompute_totals, validate_pngt_zip
from .dto import DeleteLapsResult, MarkLapGoodResult
from .exceptions import DriverNotFoundError

# -------------------------------------- FUNCTIONS ----------------------------------------------------------------------

def delete_laps(
    pngt_path: Union[Path, str],
    driver_index: int,
    lap_numbers: list[int],
) -> DeleteLapsResult:
    """Removes the specified laps for one driver from a .pngt file.

    Full archive rebuild -- ZIP has no true delete. Atomic: writes to a .tmp file,
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

        existing_laps = read_json(zf, laps_entry, path).get("laps", [])
        existing_numbers = {lap["lap_number"] for lap in existing_laps}
        to_delete = set(lap_numbers)
        missing = sorted(to_delete - existing_numbers)
        if missing:
            raise ValueError(f"Lap number(s) not found for driver {driver_index}: {missing}")

        remaining_laps = [lap for lap in existing_laps if lap["lap_number"] not in to_delete]
        driver_folder_removed = not remaining_laps

        session_raw = read_json(zf, "session.json", path)
        drivers_raw = read_json(zf, "drivers.json", path)
        new_laps_count, new_session_best = recompute_totals(
            _other_drivers_laps(zf, path, drivers_raw, driver_index, remaining_laps)
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
    rebuild_archive(path, tmp_path, skip_names=skip_names, overrides=overrides)
    os.replace(tmp_path, path)

    return DeleteLapsResult(
        driver_index=driver_index,
        deleted_lap_numbers=sorted(to_delete),
        driver_folder_removed=driver_folder_removed,
        new_laps_count=new_laps_count,
        new_session_best=new_session_best,
    )


def mark_lap_good(
    pngt_path: Union[Path, str],
    driver_index: int,
    lap_number: int,
) -> MarkLapGoodResult:
    """Sets is_good=True for the specified lap. No-op if already True.

    Does NOT support unmarking -- there is no parameter or code path in this
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

        laps = read_json(zf, laps_entry, path).get("laps", [])
    finally:
        zf.close()

    target = next((lap for lap in laps if lap["lap_number"] == lap_number), None)
    if target is None:
        raise ValueError(f"Lap number {lap_number} not found for driver {driver_index}")

    if target.get("is_good"):
        return MarkLapGoodResult(driver_index=driver_index, lap_number=lap_number, already_good=True)

    target["is_good"] = True
    tmp_path = path.with_name(path.name + ".tmp")
    rebuild_archive(path, tmp_path, skip_names={laps_entry}, overrides={laps_entry: {"laps": laps}})
    os.replace(tmp_path, path)

    return MarkLapGoodResult(driver_index=driver_index, lap_number=lap_number, already_good=False)


def rename_session(
    pngt_path: Union[Path, str],
    new_name: str,
) -> None:
    """Sets session.json's session_name to new_name. session_uid and every other
    field are untouched."""
    path = Path(pngt_path)
    zf = validate_pngt_zip(path)
    try:
        session_raw = read_json(zf, "session.json", path)
    finally:
        zf.close()

    session_raw["session_name"] = new_name
    tmp_path = path.with_name(path.name + ".tmp")
    rebuild_archive(path, tmp_path, skip_names={"session.json"}, overrides={"session.json": session_raw})
    os.replace(tmp_path, path)


def _other_drivers_laps(zf, path, drivers_raw: dict, changed_driver_index: int, changed_driver_laps: list[dict]) -> Iterator:
    """Yields (driver_index, lap dicts) for every driver in drivers_raw, using
    changed_driver_laps in place of changed_driver_index's on-disk laps.json (which
    hasn't been rewritten yet) and reading every other driver's laps.json from the
    still-open archive. A driver with no folder (Restricted) is skipped."""
    for driver in drivers_raw.get("drivers", []):
        idx = driver["driver_index"]
        if idx == changed_driver_index:
            yield idx, changed_driver_laps
            continue
        entry = f"drivers/{idx:02d}/laps.json"
        if entry not in zf.namelist():
            continue
        yield idx, read_json(zf, entry, path).get("laps", [])
