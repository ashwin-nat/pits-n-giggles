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

"""Tests for the save file invariant checker.

These test the *rules*, against hand-built fixtures - no recordings, no replay, no app.
That is deliberate: a checker whose rules are not themselves covered is a checker that
quietly reports "all passed" forever once a rule stops firing.
"""

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

from typing import Any, Dict, List, Optional

import pytest

from lib.f1_types import SessionType23, SessionType24
from lib.save_invariants import checkSaveFile, resolveSessionType

# -------------------------------------- HELPERS -----------------------------------------------------------------------

def wear(lap: int, average: float) -> Dict[str, Any]:
    """One tyre wear history entry."""

    return {"lap-number": lap, "average": average, "desc": f"lap {lap}"}

def stint(start: int, end: Optional[int], wears: List[Dict[str, Any]]) -> Dict[str, Any]:
    """One tyre stint."""

    return {"start-lap": start, "end-lap": end, "tyre-wear-history": wears}

def driver(name: str = "TEST", index: int = 0, position: int = 1,
           telemetry: str = "Public", stints: Optional[List[Dict[str, Any]]] = None,
           per_lap: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """One classification-data entry."""

    return {
        "driver-name": name,
        "index": index,
        "track-position": position,
        "telemetry-settings": telemetry,
        "tyre-set-history": stints if stints is not None else [stint(1, 2, [wear(1, 1.0), wear(2, 2.0)])],
        "per-lap-info": per_lap or [],
    }

def save(drivers: Optional[List[Dict[str, Any]]] = None, game_year: Any = 25,
         session_type: str = "Race") -> Dict[str, Any]:
    """A minimal save file."""

    return {
        "game-year": game_year,
        "session-info": {"session-type": session_type},
        "classification-data": drivers if drivers is not None else [driver()],
    }

def rules(report) -> List[str]:
    """The set of rule names that fired."""

    return sorted({v.rule for v in report.violations})

# -------------------------------------- TESTS -------------------------------------------------------------------------

class TestSessionTypeResolution:
    """The concrete SessionType enum is season specific, picked by game year."""

    def test_f1_23_resolves_via_session_type_23(self):
        assert resolveSessionType(save(game_year=23)) is SessionType23.RACE

    @pytest.mark.parametrize("game_year", [24, 25, 26])
    def test_after_f1_23_resolves_via_session_type_24(self, game_year):
        assert resolveSessionType(save(game_year=game_year)) is SessionType24.RACE

    @pytest.mark.parametrize("game_year", [21, 22])
    def test_unsupported_game_year_does_not_resolve(self, game_year):
        assert resolveSessionType(save(game_year=game_year)) is None

    @pytest.mark.parametrize("game_year", [None, "25"])
    def test_malformed_game_year_does_not_resolve(self, game_year):
        assert resolveSessionType(save(game_year=game_year)) is None

    def test_unknown_session_type_string_does_not_resolve(self):
        assert resolveSessionType(save(session_type="Brunch")) is None

    def test_time_trial_round_trips(self):
        """The gate for the wear rules depends on this exact round trip."""

        resolved = resolveSessionType(save(session_type="Time Trial"))
        assert resolved is not None and resolved.isTimeTrialTypeSession()

class TestMetadata:
    """A save we cannot classify is reported, never silently skipped."""

    def test_clean_save_passes(self):
        assert checkSaveFile(save()).ok

    def test_missing_game_year_is_a_violation(self):
        assert "metadata" in rules(checkSaveFile(save(game_year=None)))

    def test_unsupported_game_year_is_a_violation(self):
        assert "metadata" in rules(checkSaveFile(save(game_year=22)))

    def test_unknown_session_type_is_a_violation(self):
        assert "metadata" in rules(checkSaveFile(save(session_type="Brunch")))

    def test_unknown_session_type_is_not_reported_as_time_trial(self):
        """Otherwise a malformed save hides behind a legitimate-looking skip."""

        report = checkSaveFile(save(session_type="Brunch"))
        assert "unknown-session-type" in report.drivers_skipped
        assert "time-trial" not in report.drivers_skipped

class TestStintStructure:
    """Structural rules apply to every driver, whatever their telemetry setting."""

    def test_contiguous_stints_pass(self):
        stints = [stint(1, 5, [wear(1, 1.0)]), stint(6, 9, [wear(6, 1.0)])]
        assert checkSaveFile(save([driver(stints=stints)])).ok

    def test_gap_between_stints_is_a_violation(self):
        """A stalled tyre change completion lands the new stint's start_lap a lap late."""

        stints = [stint(1, 5, [wear(1, 1.0)]), stint(7, 9, [wear(7, 1.0)])]
        assert "stint-continuity" in rules(checkSaveFile(save([driver(stints=stints)])))

    def test_overlapping_stints_are_a_violation(self):
        stints = [stint(1, 5, [wear(1, 1.0)]), stint(4, 9, [wear(4, 1.0)])]
        assert "stint-continuity" in rules(checkSaveFile(save([driver(stints=stints)])))

    def test_end_before_start_is_a_violation(self):
        assert "stint-bounds" in rules(checkSaveFile(save([driver(stints=[stint(9, 4, [wear(9, 1.0)])])])))

    def test_missing_start_lap_is_a_violation(self):
        stints = [{"start-lap": None, "end-lap": 5, "tyre-wear-history": [wear(1, 1.0)]}]
        assert "stint-bounds" in rules(checkSaveFile(save([driver(stints=stints)])))

    def test_open_final_stint_is_tolerated(self):
        """A retirement mid-stint leaves end-lap unset; that is not a violation."""

        assert checkSaveFile(save([driver(stints=[stint(1, None, [wear(1, 1.0)])])])).ok

class TestWearRules:
    """Wear is cumulative per set, so it can never decrease within a stint."""

    def test_increasing_wear_passes(self):
        stints = [stint(1, 3, [wear(1, 1.0), wear(2, 5.0), wear(3, 9.0)])]
        assert checkSaveFile(save([driver(stints=stints)])).ok

    def test_flat_wear_passes(self):
        """Non-decreasing, not strictly increasing - a cooldown lap adds little."""

        stints = [stint(1, 3, [wear(1, 5.0), wear(2, 5.0), wear(3, 5.0)])]
        assert checkSaveFile(save([driver(stints=stints)])).ok

    def test_decreasing_wear_is_a_violation(self):
        """The observed eviction bug: the old set's final wear overwritten with the new set's."""

        stints = [stint(1, 2, [wear(1, 5.974), wear(2, 3.645)])]
        assert "wear-monotonic" in rules(checkSaveFile(save([driver(stints=stints)])))

    def test_violation_reports_both_data_points(self):
        """The rule states what it saw and nothing about why."""

        stints = [stint(1, 2, [wear(1, 5.974), wear(2, 3.645)])]
        detail = checkSaveFile(save([driver(stints=stints)])).violations[0].detail
        assert "5.974" in detail and "3.645" in detail

    @pytest.mark.parametrize("bad", [-0.1, 100.1, None])
    def test_out_of_range_wear_is_a_violation(self, bad):
        stints = [stint(1, 1, [wear(1, bad)])]
        assert "wear-range" in rules(checkSaveFile(save([driver(stints=stints)])))

    def test_empty_wear_history_is_a_violation(self):
        assert "stint-wear-empty" in rules(checkSaveFile(save([driver(stints=[stint(1, 2, [])])])))

class TestWearGating:
    """Wear rules are gated on declared fields, never on sniffing for zero values."""

    BAD_STINT = [stint(1, 2, [wear(1, 5.0), wear(2, 3.0)])]

    def test_public_driver_in_a_race_is_checked(self):
        report = checkSaveFile(save([driver(stints=self.BAD_STINT)]))
        assert "wear-monotonic" in rules(report)
        assert report.drivers_checked == 1

    def test_restricted_driver_is_skipped(self):
        """Restricted telemetry reports zero wear, so the rules would pass vacuously."""

        report = checkSaveFile(save([driver(telemetry="Restricted", stints=self.BAD_STINT)]))
        assert report.ok
        assert report.drivers_skipped == {"restricted-telemetry": 1}
        assert report.drivers_checked == 0

    def test_time_trial_is_skipped(self):
        """Time trial has no tyre wear or temperatures at all."""

        report = checkSaveFile(save([driver(stints=self.BAD_STINT)], session_type="Time Trial"))
        assert report.ok
        assert report.drivers_skipped == {"time-trial": 1}

    def test_structural_rules_still_apply_in_time_trial(self):
        """Skipping wear must not skip the driver entirely."""

        stints = [stint(1, 5, [wear(1, 1.0)]), stint(7, 9, [wear(7, 1.0)])]
        report = checkSaveFile(save([driver(stints=stints)], session_type="Time Trial"))
        assert "stint-continuity" in rules(report)

    def test_a_zero_wear_public_driver_is_still_checked(self):
        """Lap 1 wear is legitimately near zero - sniffing for zeros would skip real drivers."""

        stints = [stint(1, 2, [wear(1, 0.0), wear(2, 0.0)])]
        report = checkSaveFile(save([driver(stints=stints)]))
        assert report.ok
        assert report.drivers_checked == 1, "must not be skipped just because wear is zero"

class TestClassification:
    """Field-wide uniqueness."""

    def test_duplicate_track_position_is_a_violation(self):
        drivers = [driver(name="A", index=0, position=1), driver(name="B", index=1, position=1)]
        assert "position-unique" in rules(checkSaveFile(save(drivers)))

    def test_duplicate_index_is_a_violation(self):
        drivers = [driver(name="A", index=0, position=1), driver(name="B", index=0, position=2)]
        assert "index-unique" in rules(checkSaveFile(save(drivers)))

    def test_distinct_drivers_pass(self):
        drivers = [driver(name="A", index=0, position=1), driver(name="B", index=1, position=2)]
        assert checkSaveFile(save(drivers)).ok

class TestPerLapInfo:
    """Per-lap entries carry distinct lap numbers."""

    def test_duplicate_lap_number_is_a_violation(self):
        per_lap = [{"lap-number": 1}, {"lap-number": 2}, {"lap-number": 1}]
        assert "lap-duplicate" in rules(checkSaveFile(save([driver(per_lap=per_lap)])))

    def test_distinct_lap_numbers_pass(self):
        per_lap = [{"lap-number": 1}, {"lap-number": 2}, {"lap-number": 3}]
        assert checkSaveFile(save([driver(per_lap=per_lap)])).ok

class TestReport:
    """The report has to make clear how much was actually checked."""

    def test_summary_names_skips(self):
        report = checkSaveFile(save([driver(telemetry="Restricted")]))
        summary = report.summary()
        assert "restricted-telemetry" in summary and "wear-checked=0" in summary

    def test_summary_reports_no_skips_explicitly(self):
        assert "skipped=none" in checkSaveFile(save()).summary()

    def test_violation_str_includes_driver(self):
        stints = [stint(1, 2, [wear(1, 5.0), wear(2, 3.0)])]
        violation = checkSaveFile(save([driver(name="NORRIS", stints=stints)])).violations[0]
        assert "NORRIS" in str(violation)
