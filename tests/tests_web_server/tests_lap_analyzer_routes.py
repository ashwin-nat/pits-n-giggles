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

"""apps.web.lap_analyzer_routes: _update_cached_session_name, the one bit of pure
logic in this module worth unit testing directly (everything else is route wiring,
covered by the manual smoke script per this repo's convention -- see
apps/web/test_viewer_api.py).
"""

import logging
from http import HTTPStatus
from io import BytesIO
from types import SimpleNamespace

import numpy as np
import pytest

import apps.web.lap_analyzer_routes as routes
from apps.web.pngt_discovery import PngtSessionEntry
from lib.pngt import (CompletedLap, DriverExportData, DriverRecord,
                      LapMetadata, ParsedSessionMetadata, SensorConfig,
                      SensorType, SessionMetadata, TrackInfo, write_session)


def _entry(slug: str, name: str) -> PngtSessionEntry:
    session = ParsedSessionMetadata(
        session_uid=1, session_name=name, session_type="race", app_version="1.0",
        game_year=2026, formula="F1", game_version="1.0", timestamp="2024-01-01T00:00:00Z",
        track=TrackInfo(id=1, name="Test Track"), laps_count=1, session_best=None,
    )
    return PngtSessionEntry(
        slug=slug, rel_path=f"{slug}.pngt", session=session, drivers=[], sensors=[], laps_by_driver={},
    )


def test_update_cached_session_name_updates_by_slug_entry(monkeypatch):
    entry = _entry("spa-race", "Original Name")
    monkeypatch.setattr(routes, "_sessions_cache", [entry])
    monkeypatch.setattr(routes, "_by_slug", {"spa-race": entry})

    routes._update_cached_session_name("spa-race", "New Name")

    assert routes._by_slug["spa-race"].session.session_name == "New Name"
    assert routes._sessions_cache[0].session.session_name == "New Name"


def test_update_cached_session_name_preserves_slug(monkeypatch):
    """The slug is the dict key and the entry's own .slug field -- neither should
    ever change on a rename, only session_name."""
    entry = _entry("spa-race", "Original Name")
    monkeypatch.setattr(routes, "_sessions_cache", [entry])
    monkeypatch.setattr(routes, "_by_slug", {"spa-race": entry})

    routes._update_cached_session_name("spa-race", "New Name")

    assert routes._by_slug["spa-race"].slug == "spa-race"
    assert set(routes._by_slug.keys()) == {"spa-race"}


def test_update_cached_session_name_leaves_other_entries_untouched(monkeypatch):
    renamed = _entry("spa-race", "Original Name")
    other = _entry("monza-race", "Monza Race")
    monkeypatch.setattr(routes, "_sessions_cache", [renamed, other])
    monkeypatch.setattr(routes, "_by_slug", {"spa-race": renamed, "monza-race": other})

    routes._update_cached_session_name("spa-race", "New Name")

    assert routes._by_slug["monza-race"].session.session_name == "Monza Race"
    names = {e.slug: e.session.session_name for e in routes._sessions_cache}
    assert names == {"spa-race": "New Name", "monza-race": "Monza Race"}


def test_update_cached_session_name_does_not_mutate_original_entry(monkeypatch):
    """PngtSessionEntry/SessionMetadata are frozen -- this must build new instances,
    not attempt (and fail) to mutate the old one in place."""
    entry = _entry("spa-race", "Original Name")
    monkeypatch.setattr(routes, "_sessions_cache", [entry])
    monkeypatch.setattr(routes, "_by_slug", {"spa-race": entry})

    routes._update_cached_session_name("spa-race", "New Name")

    assert entry.session.session_name == "Original Name"


# -------------------------------------- links between the two slug namespaces -----------------------------------------

import apps.web.save_viewer_routes as viewer_routes


def test_lap_analyzer_slug_for_path_matches_the_same_file(monkeypatch):
    spa = _entry("spa-race", "Spa")
    monza = _entry("monza-race", "Monza")
    monkeypatch.setattr(routes, "_by_slug", {"spa-race": spa, "monza-race": monza})

    assert routes.lap_analyzer_slug_for_path("monza-race.pngt") == "monza-race"
    assert routes.lap_analyzer_slug_for_path("other.pngt") is None


def test_save_viewer_slug_for_path_matches_a_container(monkeypatch):
    monkeypatch.setattr(viewer_routes, "_slug_map", {"race-spa-2026": "2026_11_03/Race_Spa_2026.pngt"})

    assert viewer_routes.save_viewer_slug_for_path("2026_11_03/Race_Spa_2026.pngt") == "race-spa-2026"
    assert viewer_routes.save_viewer_slug_for_path("2026_11_03/Other.pngt") is None


def test_save_viewer_slug_for_path_never_links_a_loose_json(monkeypatch):
    monkeypatch.setattr(viewer_routes, "_slug_map", {"race-spa-2026": "2026_11_03/Race_Spa_2026.json"})

    assert viewer_routes.save_viewer_slug_for_path("2026_11_03/Race_Spa_2026.json") is None


def _write_recording(path):
    lap = CompletedLap(
        metadata=LapMetadata(lap_number=1, lap_time_ms=90000, valid=True, tyre_compound="Soft",
                             tyre_laps=1, pit_in_lap=False, pit_out_lap=False, ers_harvest_limit_j=None),
        telemetry={"lap_distance": [0.0, 100.0, 200.0], "speed": [100.0, float("nan"), 120.0]},
    )
    write_session(
        path,
        SessionMetadata(session_uid=1, session_name="S", session_type="race", app_version="1.0",
                        game_year=2026, formula="F1", game_version="1.0",
                        timestamp="2024-01-01T00:00:00Z", track=TrackInfo(id=1, name="T")),
        [SensorConfig(key="speed", label="Speed", unit="km/h", type=SensorType.CONTINUOUS)],
        [DriverRecord(driver_index=0, name="D", team="T", car_number=1, nationality=None, platform=None)],
        {0: DriverExportData(driver_index=0, completed_laps=[lap])},
    )


def test_read_lap_npz_returns_the_stored_arrays_with_nan_intact(tmp_path):
    _write_recording(tmp_path / "s.pngt")
    server = SimpleNamespace(m_session_dir=tmp_path, m_logger=logging.getLogger("t"))

    raw = routes._read_lap_npz(server, _entry("s", "S"), 0, 1)

    with np.load(BytesIO(raw)) as npz:
        assert npz["lap_distance"].tolist() == [0.0, 100.0, 200.0]
        assert np.isnan(npz["speed"][1])


def test_read_lap_npz_unknown_lap_is_lap_not_found(tmp_path):
    _write_recording(tmp_path / "s.pngt")
    server = SimpleNamespace(m_session_dir=tmp_path, m_logger=logging.getLogger("t"))

    with pytest.raises(routes._TelemetryRequestError) as exc:
        routes._read_lap_npz(server, _entry("s", "S"), 0, 9)
    assert (exc.value.code, exc.value.status) == ("LAP_NOT_FOUND", HTTPStatus.NOT_FOUND)
