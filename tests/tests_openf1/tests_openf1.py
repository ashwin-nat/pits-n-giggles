# MIT License
#
# Copyright (c) [2025] [Ashwin Natarajan]
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

import asyncio
import logging
import sys
from unittest.mock import AsyncMock, MagicMock, patch

from lib.f1_types import TrackID
from lib.openf1.api import MostRecentPoleLap, getMostRecentPoleLap

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# ----------------------------------------------------------------------------------------------------------------------

_LOGGER = logging.getLogger("test_openf1")

_SESSIONS_RESPONSE = [
    {"session_key": 9999, "session_name": "Practice 1"},
    {"session_key": 10000, "session_name": "Qualifying"},
]
_STARTING_GRID_RESPONSE = [{"driver_number": 44, "position": 1}]
_DRIVERS_RESPONSE = [
    {"driver_number": 44, "broadcast_name": "L HAMILTON", "team_name": "Ferrari"}
]
_LAPS_RESPONSE = [
    {"driver_number": 44, "lap_duration": 80.5, "duration_sector_1": 25.1, "duration_sector_2": 28.3, "duration_sector_3": 27.1, "st_speed": 310},
    {"driver_number": 44, "lap_duration": 79.2, "duration_sector_1": 24.8, "duration_sector_2": 27.9, "duration_sector_3": 26.5, "st_speed": 315},
    {"driver_number": 44, "lap_duration": None,  "duration_sector_1": None, "duration_sector_2": None, "duration_sector_3": None, "st_speed": None},
]

def _make_request_side_effect(sessions=_SESSIONS_RESPONSE, grid=_STARTING_GRID_RESPONSE,
                               drivers=_DRIVERS_RESPONSE, laps=_LAPS_RESPONSE):
    """Returns an AsyncMock side_effect that dispatches by endpoint name."""
    async def _side_effect(endpoint, params, logger):
        if endpoint == "sessions":
            return sessions
        if endpoint == "starting_grid":
            return grid
        if endpoint == "drivers":
            return drivers
        if endpoint == "laps":
            return laps
        return None
    return _side_effect


class TestMostRecentPoleLapDataclass:

    def test_to_json_contains_all_keys(self):
        pole = MostRecentPoleLap(
            circuit_id=TrackID.Silverstone,
            year=2025,
            driver_name="L. Hamilton",
            driver_num=44,
            team_name="Ferrari",
            lap_ms=79200,
            s1_ms=24800,
            s2_ms=27900,
            s3_ms=26500,
            speed_trap_kmph=315,
        )
        j = pole.toJSON()
        assert j["circuit"] == str(TrackID.Silverstone)
        assert j["year"] == 2025
        assert j["driver-name"] == "L. Hamilton"
        assert j["driver-num"] == 44
        assert j["team-name"] == "Ferrari"
        assert j["lap-ms"] == 79200
        assert j["s1-ms"] == 24800
        assert j["s2-ms"] == 27900
        assert j["s3-ms"] == 26500
        assert j["speed-trap-kmph"] == 315

    def test_to_json_optional_fields_none(self):
        pole = MostRecentPoleLap(circuit_id=TrackID.Silverstone)
        j = pole.toJSON()
        assert j["year"] is None
        assert j["driver-name"] is None
        assert j["lap-ms"] is None


class TestGetMostRecentPoleLap:

    async def test_returns_fastest_lap_for_current_year(self):
        with patch("lib.openf1.api._make_openf1_request", side_effect=_make_request_side_effect()):
            result = await getMostRecentPoleLap(TrackID.Silverstone, _LOGGER)

        assert result is not None
        assert result.year is not None
        assert result.lap_ms == 79200
        assert result.s1_ms == 24800
        assert result.s2_ms == 27900
        assert result.s3_ms == 26500
        assert result.speed_trap_kmph == 315
        assert result.driver_name == "L. HAMILTON"
        assert result.team_name == "Ferrari"
        assert result.driver_num == 44

    async def test_unsupported_circuit_returns_none(self):
        result = await getMostRecentPoleLap(TrackID.Hanoi, _LOGGER)
        assert result is None

    async def test_falls_back_to_previous_year_when_current_year_has_no_sessions(self):
        call_count = {"n": 0}

        async def _side_effect(endpoint, params, logger):
            if endpoint == "sessions":
                call_count["n"] += 1
                if call_count["n"] == 1:
                    return None
                return _SESSIONS_RESPONSE
            return await _make_request_side_effect()(endpoint, params, logger)

        with patch("lib.openf1.api._make_openf1_request", side_effect=_side_effect):
            result = await getMostRecentPoleLap(TrackID.Silverstone, _LOGGER)

        assert result is not None
        assert call_count["n"] == 2

    async def test_falls_back_when_no_qualifying_session(self):
        sessions_no_quali = [{"session_key": 9999, "session_name": "Practice 1"}]
        call_count = {"n": 0}

        async def _side_effect(endpoint, params, logger):
            if endpoint == "sessions":
                call_count["n"] += 1
                if call_count["n"] == 1:
                    return sessions_no_quali
                return _SESSIONS_RESPONSE
            return await _make_request_side_effect()(endpoint, params, logger)

        with patch("lib.openf1.api._make_openf1_request", side_effect=_side_effect):
            result = await getMostRecentPoleLap(TrackID.Silverstone, _LOGGER)

        assert result is not None

    async def test_falls_back_when_starting_grid_returns_none(self):
        call_count = {"sessions": 0}

        async def _side_effect(endpoint, params, logger):
            if endpoint == "sessions":
                call_count["sessions"] += 1
                return _SESSIONS_RESPONSE
            if endpoint == "starting_grid":
                if call_count["sessions"] == 1:
                    return None
                return _STARTING_GRID_RESPONSE
            return await _make_request_side_effect()(endpoint, params, logger)

        with patch("lib.openf1.api._make_openf1_request", side_effect=_side_effect):
            result = await getMostRecentPoleLap(TrackID.Silverstone, _LOGGER)

        assert result is not None

    async def test_falls_back_when_laps_returns_none(self):
        call_count = {"sessions": 0}

        async def _side_effect(endpoint, params, logger):
            if endpoint == "sessions":
                call_count["sessions"] += 1
                return _SESSIONS_RESPONSE
            if endpoint == "laps":
                if call_count["sessions"] == 1:
                    return None
                return _LAPS_RESPONSE
            return await _make_request_side_effect()(endpoint, params, logger)

        with patch("lib.openf1.api._make_openf1_request", side_effect=_side_effect):
            result = await getMostRecentPoleLap(TrackID.Silverstone, _LOGGER)

        assert result is not None

    async def test_returns_none_when_all_years_fail(self):
        async def _always_none(endpoint, params, logger):
            return None

        with patch("lib.openf1.api._make_openf1_request", side_effect=_always_none):
            result = await getMostRecentPoleLap(TrackID.Silverstone, _LOGGER)

        assert result is None

    async def test_ignores_laps_with_null_duration(self):
        laps_all_null = [
            {"driver_number": 44, "lap_duration": None, "duration_sector_1": None,
             "duration_sector_2": None, "duration_sector_3": None, "st_speed": None},
        ]
        with patch("lib.openf1.api._make_openf1_request",
                   side_effect=_make_request_side_effect(laps=laps_all_null)):
            result = await getMostRecentPoleLap(TrackID.Silverstone, _LOGGER)

        assert result is None

    async def test_picks_fastest_lap_not_first(self):
        laps = [
            {"driver_number": 44, "lap_duration": 85.0, "duration_sector_1": 27.0, "duration_sector_2": 30.0, "duration_sector_3": 28.0, "st_speed": 300},
            {"driver_number": 44, "lap_duration": 79.2, "duration_sector_1": 24.8, "duration_sector_2": 27.9, "duration_sector_3": 26.5, "st_speed": 315},
            {"driver_number": 44, "lap_duration": 82.1, "duration_sector_1": 26.0, "duration_sector_2": 29.0, "duration_sector_3": 27.1, "st_speed": 308},
        ]
        with patch("lib.openf1.api._make_openf1_request",
                   side_effect=_make_request_side_effect(laps=laps)):
            result = await getMostRecentPoleLap(TrackID.Silverstone, _LOGGER)

        assert result is not None
        assert result.lap_ms == 79200

    async def test_driver_name_formatting(self):
        drivers = [{"driver_number": 44, "broadcast_name": "L HAMILTON", "team_name": "Ferrari"}]
        with patch("lib.openf1.api._make_openf1_request",
                   side_effect=_make_request_side_effect(drivers=drivers)):
            result = await getMostRecentPoleLap(TrackID.Silverstone, _LOGGER)

        assert result is not None
        assert result.driver_name == "L. HAMILTON"

    async def test_circuit_id_preserved_in_result(self):
        with patch("lib.openf1.api._make_openf1_request",
                   side_effect=_make_request_side_effect()):
            result = await getMostRecentPoleLap(TrackID.Spa, _LOGGER)

        assert result is not None
        assert result.circuit_id == TrackID.Spa
