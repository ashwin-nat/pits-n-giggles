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
# pylint: skip-file

"""apps.web.pngt_discovery: .pngt directory scan, mtime cache, and slug stability.

The slug-stability tests are the load-bearing ones here -- the API spec's "Session
Name vs Session ID" contract requires a session's slug to survive a rename, even
though a rename changes both session_name and the file's mtime (the cache's own
invalidation signal).
"""

import gzip
import logging
import os
import time
from pathlib import Path

import orjson
import pytest

from apps.web.pngt_discovery import (CACHE_FILE, build_pngt_session_list,
                                     find_pngt_files, slugify)
from lib.logger import PngLogger
from lib.pngt import (CompletedLap, DriverExportData, DriverRecord,
                      LapMetadata, SensorConfig, SensorDtype, SensorType,
                      SessionBest, SessionMetadata, TrackInfo, write_session)

logging.setLoggerClass(PngLogger)


def _logger() -> PngLogger:
    return logging.getLogger("test_pngt_discovery")


def _session(name="Test Session", timestamp="2024-06-01T14:32:00Z"):
    return SessionMetadata(
        session_uid=1,
        session_name=name,
        session_type="race",
        app_version="0.0.1-test",
        game_year=2026,
        formula="F1",
        game_version="1.00",
        timestamp=timestamp,
        track=TrackInfo(id=999, name="Fake Circuit"),
        laps_count=1,
        session_best=SessionBest(driver_index=1, lap_number=1, lap_time_ms=90000),
    )


def _sensors():
    return [SensorConfig(key="speed", label="Speed", unit="km/h", type=SensorType.CONTINUOUS)]


def _drivers():
    return [DriverRecord(driver_index=1, name="Driver A", team="Team A",
                         car_number=1, nationality="GB", platform="Steam", is_telemetry_public=True)]


def _driver_data():
    lap = CompletedLap(
        metadata=LapMetadata(lap_number=1, lap_time_ms=90000, valid=True, tyre_compound="Soft",
                             tyre_laps=1, pit_in_lap=False, pit_out_lap=False, num_points=2, is_good=True),
        telemetry={"lap_distance": [0.0, 100.0], "speed": [100.0, 110.0]},
    )
    return {1: DriverExportData(driver_index=1, completed_laps=[lap])}


def _write_pngt(path: Path, name="Test Session", timestamp="2024-06-01T14:32:00Z") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    return write_session(
        path, _session(name, timestamp), _sensors(),
        {"speed": SensorDtype.FLOAT32}, _drivers(), _driver_data(),
    )


async def _build_final(session_dir: Path):
    """Drain the async generator; return its last (entries, slug_map) yield, or
    ([], {}) if the directory had nothing to yield."""
    entries, slug_map = [], {}
    async for entries, slug_map in build_pngt_session_list(session_dir, _logger(), "0.0.1-test"):
        pass
    return entries, slug_map


# ----------------------------------------------------------------------------------------------------------------------
# find_pngt_files / slugify
# ----------------------------------------------------------------------------------------------------------------------

def test_find_pngt_files_recursive(tmp_path):
    _write_pngt(tmp_path / "a.pngt")
    _write_pngt(tmp_path / "nested" / "b.pngt")
    (tmp_path / "notes.txt").write_text("not a pngt file")

    found = {str(p) for p in find_pngt_files(tmp_path)}
    assert found == {"a.pngt", str(Path("nested") / "b.pngt")}


@pytest.mark.parametrize("name,expected", [
    ("Spa-Francorchamps Race 2024-06-01", "spa-francorchamps-race-2024-06-01"),
    ("League Race Night — Soft tyre test", "league-race-night-soft-tyre-test"),
    ("!!!", "session"),
    ("", "session"),
])
def test_slugify(name, expected):
    assert slugify(name) == expected


# ----------------------------------------------------------------------------------------------------------------------
# build_pngt_session_list
# ----------------------------------------------------------------------------------------------------------------------

async def test_missing_session_dir_yields_nothing(tmp_path):
    entries, slug_map = await _build_final(tmp_path / "does-not-exist")
    assert entries == []
    assert slug_map == {}


async def test_basic_discovery(tmp_path):
    _write_pngt(tmp_path / "session.pngt")

    entries, slug_map = await _build_final(tmp_path)

    assert len(entries) == 1
    entry = entries[0]
    assert entry.slug == "test-session"
    assert entry.rel_path == "session.pngt"
    assert entry.session.session_name == "Test Session"
    assert [d.name for d in entry.drivers] == ["Driver A"]
    assert [s.key for s in entry.sensors] == ["speed"]
    assert entry.laps_by_driver[1][0].lap_time_ms == 90000
    assert slug_map == {"test-session": "session.pngt"}


async def test_sorted_newest_first_by_session_timestamp(tmp_path):
    _write_pngt(tmp_path / "older.pngt", name="Older", timestamp="2024-01-01T00:00:00Z")
    _write_pngt(tmp_path / "newer.pngt", name="Newer", timestamp="2024-06-01T00:00:00Z")

    entries, _ = await _build_final(tmp_path)

    assert [e.session.session_name for e in entries] == ["Newer", "Older"]


async def test_slug_collision_gets_suffixed(tmp_path):
    _write_pngt(tmp_path / "a.pngt", name="Duplicate Name")
    _write_pngt(tmp_path / "b.pngt", name="Duplicate Name")

    entries, slug_map = await _build_final(tmp_path)

    slugs = sorted(e.slug for e in entries)
    assert slugs == ["duplicate-name", "duplicate-name-2"]
    assert set(slug_map) == set(slugs)


async def test_corrupt_file_skipped_without_aborting_scan(tmp_path):
    _write_pngt(tmp_path / "good.pngt")
    (tmp_path / "bad.pngt").write_bytes(b"not a zip file")

    entries, _ = await _build_final(tmp_path)

    assert len(entries) == 1
    assert entries[0].rel_path == "good.pngt"


# ----------------------------------------------------------------------------------------------------------------------
# Caching behaviour
# ----------------------------------------------------------------------------------------------------------------------

async def test_second_run_uses_cache_not_reparse(tmp_path, monkeypatch):
    _write_pngt(tmp_path / "session.pngt")
    await _build_final(tmp_path)  # first run: populates the on-disk cache

    calls = []
    import apps.web.pngt_discovery as pd
    original = pd.read_session

    def _spy(path):
        calls.append(path)
        return original(path)

    monkeypatch.setattr(pd, "read_session", _spy)

    entries, _ = await _build_final(tmp_path)

    assert len(entries) == 1
    assert calls == []  # cache hit -- read_session never called on the second run


async def test_modified_file_is_reparsed(tmp_path):
    path = tmp_path / "session.pngt"
    _write_pngt(path, name="Original Name")
    await _build_final(tmp_path)

    # Simulate a mutation (e.g. rename_session) by rewriting the file and bumping
    # its mtime forward, exactly what a real archive rewrite would do.
    time.sleep(0.01)
    _write_pngt(path, name="New Name")
    os.utime(path, (time.time() + 1, time.time() + 1))

    entries, _ = await _build_final(tmp_path)

    assert len(entries) == 1
    assert entries[0].session.session_name == "New Name"


async def test_rename_preserves_slug_across_mtime_change(tmp_path):
    path = tmp_path / "session.pngt"
    _write_pngt(path, name="Original Name")
    first_entries, _ = await _build_final(tmp_path)
    original_slug = first_entries[0].slug
    assert original_slug == "original-name"

    time.sleep(0.01)
    _write_pngt(path, name="Renamed Session")
    os.utime(path, (time.time() + 1, time.time() + 1))

    entries, slug_map = await _build_final(tmp_path)

    assert len(entries) == 1
    assert entries[0].session.session_name == "Renamed Session"
    # The whole point: slug must not follow the new name.
    assert entries[0].slug == original_slug
    assert slug_map == {original_slug: "session.pngt"}


async def test_deleted_file_pruned_from_cache(tmp_path):
    _write_pngt(tmp_path / "a.pngt")
    _write_pngt(tmp_path / "b.pngt")
    await _build_final(tmp_path)

    (tmp_path / "b.pngt").unlink()
    entries, _ = await _build_final(tmp_path)

    assert [e.rel_path for e in entries] == ["a.pngt"]

    cache_path = tmp_path / CACHE_FILE
    with open(cache_path, 'rb') as f:
        cache = orjson.loads(gzip.decompress(f.read()))
    assert "b.pngt" not in cache


async def test_app_version_change_invalidates_whole_cache(tmp_path, monkeypatch):
    _write_pngt(tmp_path / "session.pngt")
    async for _ in build_pngt_session_list(tmp_path, _logger(), "0.0.1-test"):
        pass

    calls = []
    import apps.web.pngt_discovery as pd
    original = pd.read_session

    def _spy(path):
        calls.append(path)
        return original(path)

    monkeypatch.setattr(pd, "read_session", _spy)

    entries = []
    async for entries, _ in build_pngt_session_list(tmp_path, _logger(), "0.0.2-test"):
        pass

    assert len(entries) == 1
    assert len(calls) == 1  # version bump forced a reparse despite unchanged mtime
