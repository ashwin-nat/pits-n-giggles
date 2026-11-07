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


# -------------------------------------- recording <-> session links ---------------------------------------------------

from apps.web.save_viewer_routes import link_recordings_to_sessions


def test_container_links_to_its_own_session():
    slug_map = {"race-spa": "2026_11_03/Race_Spa_2026_11_03_10_00_00.pngt"}
    assert link_recordings_to_sessions(["2026_11_03/Race_Spa_2026_11_03_10_00_00.pngt"], slug_map) == {
        "2026_11_03/Race_Spa_2026_11_03_10_00_00.pngt": "race-spa"}


def test_loose_recording_pairs_with_the_json_of_the_same_name():
    slug_map = {"race-spa": "race-info/Race_Spa_2026_11_03_10_00_00.json"}
    links = link_recordings_to_sessions(["telemetry/Race_Spa_2026_11_03_10_00_00.pngt"], slug_map)
    assert links == {"telemetry/Race_Spa_2026_11_03_10_00_00.pngt": "race-spa"}


def test_just_in_case_and_manual_markers_are_ignored_when_pairing():
    slug_map = {"jic": "race-info/Race_Spa_Just_in_case_2026_11_03_10_00_00.json",
                "man": "race-info/Quali_Spa_Manual_2026_11_03_11_00_00.json"}
    links = link_recordings_to_sessions(
        ["telemetry/Race_Spa_2026_11_03_10_00_00.pngt", "telemetry/Quali_Spa_2026_11_03_11_00_00.pngt"], slug_map)
    assert list(links.values()) == ["jic", "man"]


def test_save_stamped_a_few_seconds_later_still_pairs():
    slug_map = {"man": "race-info/Race_Suzuka_Manual_2026_10_17_10_34_14.json"}
    links = link_recordings_to_sessions(["telemetry/Race_Suzuka_2026_10_17_10_34_13.pngt"], slug_map)
    assert links == {"telemetry/Race_Suzuka_2026_10_17_10_34_13.pngt": "man"}


def test_a_nearby_session_is_not_taken_from_a_recording_that_matches_it_exactly():
    slug_map = {"s": "race-info/Race_Suzuka_2026_10_17_10_34_14.json"}
    links = link_recordings_to_sessions(
        ["telemetry/Race_Suzuka_2026_10_17_10_34_13.pngt", "telemetry/Race_Suzuka_2026_10_17_10_34_14.pngt"], slug_map)
    assert links == {"telemetry/Race_Suzuka_2026_10_17_10_34_14.pngt": "s"}


def test_unrelated_recording_and_a_far_stamp_do_not_pair():
    slug_map = {"s": "race-info/Race_Spa_2026_11_03_10_00_00.json"}
    assert link_recordings_to_sessions(
        ["telemetry/Race_Spa_2026_11_03_10_00_06.pngt", "telemetry/Race_Monza_2026_11_03_10_00_00.pngt"], slug_map) == {}
