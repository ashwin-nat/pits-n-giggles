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

"""
Integration tests for lib/openf1 — hit the real OpenF1 API.

Run with:
    poetry run pytest tests/tests_openf1/tests_openf1_integration.py -m openf1 -v -n 0

These are excluded from the default suite to avoid network calls in CI.
They exist to catch OpenF1 API schema changes.
"""

import asyncio
import logging
import sys
from typing import Dict, Optional

import pytest

from lib.f1_types import TrackID
from lib.openf1.api import MostRecentPoleLap, getMostRecentPoleLap

pytestmark = [pytest.mark.openf1, pytest.mark.serial]

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

_LOGGER = logging.getLogger("test_openf1_integration")

# Circuits with enough history that a pole lap is virtually guaranteed to exist
_WELL_KNOWN_CIRCUITS = [
    TrackID.Silverstone,
    TrackID.Spa,
    TrackID.Monza,
]

# ----------------------------------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def pole_laps() -> Dict[TrackID, Optional[MostRecentPoleLap]]:
    """Fetch pole lap data for all test circuits once; share across all tests in module."""
    async def _fetch_all():
        results = {}
        for track_id in _WELL_KNOWN_CIRCUITS:
            results[track_id] = await getMostRecentPoleLap(track_id, _LOGGER, num_recent_years=5)
        return results

    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_fetch_all())
    finally:
        loop.close()


class TestOpenF1ApiSchema:
    """Verify the real API still returns the fields we depend on."""

    @pytest.mark.parametrize("track_id", _WELL_KNOWN_CIRCUITS)
    def test_returns_result(self, pole_laps, track_id):
        assert pole_laps[track_id] is not None, (
            f"getMostRecentPoleLap returned None for {track_id} — "
            "API may be down or starting_grid/sessions endpoint changed"
        )

    @pytest.mark.parametrize("track_id", _WELL_KNOWN_CIRCUITS)
    def test_field_types(self, pole_laps, track_id):
        result = pole_laps[track_id]
        assert result is not None
        assert isinstance(result.circuit_id, TrackID)
        assert isinstance(result.year, int) and result.year > 2000
        assert isinstance(result.driver_name, str) and result.driver_name
        assert isinstance(result.driver_num, int)
        assert isinstance(result.team_name, str) and result.team_name
        assert isinstance(result.lap_ms, int) and result.lap_ms > 0
        assert isinstance(result.s1_ms, int) and result.s1_ms > 0
        assert isinstance(result.s2_ms, int) and result.s2_ms > 0
        assert isinstance(result.s3_ms, int) and result.s3_ms > 0
        assert isinstance(result.speed_trap_kmph, int) and result.speed_trap_kmph > 0

    @pytest.mark.parametrize("track_id", _WELL_KNOWN_CIRCUITS)
    def test_sector_times_sum_to_lap_time(self, pole_laps, track_id):
        result = pole_laps[track_id]
        assert result is not None
        sector_sum = result.s1_ms + result.s2_ms + result.s3_ms
        assert abs(sector_sum - result.lap_ms) <= 1000, (
            f"Sector sum {sector_sum}ms does not match lap time {result.lap_ms}ms for {track_id}"
        )

    @pytest.mark.parametrize("track_id", _WELL_KNOWN_CIRCUITS)
    def test_circuit_id_preserved(self, pole_laps, track_id):
        result = pole_laps[track_id]
        assert result is not None
        assert result.circuit_id == track_id

    def test_unsupported_circuit_returns_none(self):
        async def _run():
            return await getMostRecentPoleLap(TrackID.Hanoi, _LOGGER)
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(_run())
        finally:
            loop.close()
        assert result is None
