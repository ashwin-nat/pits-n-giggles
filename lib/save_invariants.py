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

"""Invariant checks over a saved session JSON.

An *invariant* is something that must hold for any session, regardless of what happened
in it - a relationship, not a value. That is what makes this cheap: there is no recorded
baseline to store, re-record or review, so a growing corpus of recordings costs nothing
and every new rule applies retroactively to all of them.

It catches *impossible* states, not *changed* ones. A refactor that moves a wear value
from 34.21 to 34.19 leaves both monotonic and both pass; only an A/B comparison catches
that. This is a bug detector, not a regression detector.

Two things systematically have no wear data, and checking them would either raise false
alarms or pass vacuously:

- **Time trial sessions** have no tyre wear or temperatures at all.
- **Drivers with restricted telemetry** report zero wear, and never reach the tyre set
  history at all (``updateTyreSetData`` returns early for them).

Both are skipped for wear rules, on the *declared* fields rather than by sniffing for
zero values - a public driver on lap 1 legitimately has near-zero wear, and a driver
whose wear got corrupted to zero is exactly the case this exists to catch. Skips are
counted and reported, since otherwise "all passed" could mean nothing was checked.
"""

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from lib.f1_types import SessionType, SessionType23, SessionType24

# -------------------------------------- GLOBALS -----------------------------------------------------------------------

# The app does not support anything before F1 23
MIN_SUPPORTED_GAME_YEAR = 23

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------

@dataclass(frozen=True)
class Violation:
    """A single invariant failure.

    Attributes:
        rule (str): Short identifier of the rule that failed
        detail (str): What was actually seen
        driver (Optional[str]): Driver the failure belongs to, if driver-scoped
    """

    rule: str
    detail: str
    driver: Optional[str] = None

    def __str__(self) -> str:
        """Human readable one-liner.

        Returns:
            str: The formatted violation
        """

        where = f" [{self.driver}]" if self.driver else ""
        return f"{self.rule}{where}: {self.detail}"

@dataclass
class CheckReport:
    """Outcome of checking one save file.

    Attributes:
        violations (List[Violation]): Every invariant failure found
        drivers_checked (int): Drivers that were eligible for wear rules
        drivers_skipped (Dict[str, int]): Count of skipped drivers by reason
        session_type (Optional[str]): Resolved session type, for reporting
    """

    violations: List[Violation] = field(default_factory=list)
    drivers_checked: int = 0
    drivers_skipped: Dict[str, int] = field(default_factory=dict)
    session_type: Optional[str] = None

    @property
    def ok(self) -> bool:
        """Whether the file passed every applicable invariant.

        Returns:
            bool: True if no violations were found
        """

        return not self.violations

    def recordSkip(self, reason: str) -> None:
        """Record a driver skipped for wear rules, against the given reason.

        Args:
            reason (str): Why the driver was skipped
        """

        self.drivers_skipped[reason] = self.drivers_skipped.get(reason, 0) + 1

    def summary(self) -> str:
        """One-line summary of what was and was not checked.

        Returns:
            str: The summary line
        """

        skipped = ", ".join(f"{n} {reason}" for reason, n in sorted(self.drivers_skipped.items()))
        return (f"session={self.session_type or '?'} "
                f"wear-checked={self.drivers_checked} "
                f"skipped={skipped or 'none'} "
                f"violations={len(self.violations)}")

# -------------------------------------- HELPER FUNCTIONS --------------------------------------------------------------

def resolveSessionType(save: Dict[str, Any]) -> Optional[SessionType]:
    """Resolve the session type enum from a save file.

    The concrete enum is season specific, so the game year picks the class and the stored
    string is mapped back through it. The map is built from the enum itself rather than
    hardcoding names, so it follows any change to the members or their str().

    Args:
        save (Dict[str, Any]): The loaded save file

    Returns:
        Optional[SessionType]: The session type, or None if it could not be resolved
    """

    game_year = save.get("game-year")
    if not isinstance(game_year, int) or game_year < MIN_SUPPORTED_GAME_YEAR:
        return None

    cls = SessionType23 if game_year == MIN_SUPPORTED_GAME_YEAR else SessionType24
    return {str(member): member for member in cls}.get(save.get("session-info", {}).get("session-type"))

def _isWearCheckable(driver: Dict[str, Any]) -> Tuple[bool, str]:
    """Whether wear rules can be applied to this driver.

    Args:
        driver (Dict[str, Any]): One entry from classification-data

    Returns:
        Tuple[bool, str]: (checkable, reason-if-not)
    """

    if str(driver.get("telemetry-settings")) == "Restricted":
        return False, "restricted-telemetry"
    return True, ""

# -------------------------------------- RULES -------------------------------------------------------------------------

def _checkMetadata(save: Dict[str, Any], report: CheckReport) -> Optional[SessionType]:
    """Game year present and supported, and the session type resolvable."""

    game_year = save.get("game-year")
    if not isinstance(game_year, int):
        report.violations.append(Violation("metadata", f"game-year missing or not an int: {game_year!r}"))
        return None

    if game_year < MIN_SUPPORTED_GAME_YEAR:
        report.violations.append(Violation("metadata", f"unsupported game year {game_year}"))
        return None

    session_type = resolveSessionType(save)
    if session_type is None:
        raw = save.get("session-info", {}).get("session-type")
        report.violations.append(Violation("metadata", f"unrecognised session-type {raw!r} for game year {game_year}"))
    else:
        report.session_type = str(session_type)
    return session_type

def _checkStintStructure(name: str, stints: List[Dict[str, Any]], report: CheckReport) -> None:
    """Stints are ordered, non-overlapping and contiguous.

    A stalled tyre change completion shows up here: it lands the new stint's start_lap a
    lap late, leaving a gap against the previous stint's end_lap.
    """

    for stint in stints:
        start, end = stint.get("start-lap"), stint.get("end-lap")
        if start is None:
            report.violations.append(Violation("stint-bounds", "stint with no start-lap", name))
        elif end is not None and end < start:
            report.violations.append(Violation("stint-bounds", f"end-lap {end} before start-lap {start}", name))

    for prev, curr in zip(stints, stints[1:]):
        prev_end, curr_start = prev.get("end-lap"), curr.get("start-lap")
        if prev_end is None or curr_start is None:
            continue
        if curr_start != prev_end + 1:
            report.violations.append(Violation(
                "stint-continuity",
                f"stint ends at lap {prev_end} but next starts at lap {curr_start}", name))

def _checkStintWear(name: str, stints: List[Dict[str, Any]], report: CheckReport) -> None:
    """Wear is present, in range, and never decreases within a stint.

    A decrease is physically impossible on a single set, so it means one of the several
    parallel copies of tyre wear disagreed - the failure mode the delayed tyre change
    machinery exists to prevent.
    """

    for index, stint in enumerate(stints):
        history = stint.get("tyre-wear-history") or []
        if not history:
            report.violations.append(Violation("stint-wear-empty", f"stint {index} has no wear history", name))
            continue

        for entry in history:
            average = entry.get("average")
            if average is None or not 0.0 <= average <= 100.0:
                report.violations.append(Violation(
                    "wear-range", f"stint {index} lap {entry.get('lap-number')} average={average!r}", name))

        for prev, curr in zip(history, history[1:]):
            prev_avg, curr_avg = prev.get("average"), curr.get("average")
            if prev_avg is None or curr_avg is None:
                continue
            if curr_avg < prev_avg:
                report.violations.append(Violation(
                    "wear-monotonic",
                    f"stint {index}: lap {prev.get('lap-number')} avg={prev_avg:.3f} -> "
                    f"lap {curr.get('lap-number')} avg={curr_avg:.3f}", name))

def _checkPerLapInfo(name: str, per_lap: List[Dict[str, Any]], report: CheckReport) -> None:
    """Per-lap entries carry distinct lap numbers."""

    seen = set()
    for entry in per_lap:
        lap = entry.get("lap-number")
        if lap in seen:
            report.violations.append(Violation("lap-duplicate", f"lap {lap} appears more than once", name))
        seen.add(lap)

def _checkClassification(drivers: List[Dict[str, Any]], report: CheckReport) -> None:
    """Track positions and driver indices are unique across the field."""

    for key, rule in (("track-position", "position-unique"), ("index", "index-unique")):
        seen = {}
        for driver in drivers:
            value = driver.get(key)
            if value is None:
                continue
            if value in seen:
                report.violations.append(Violation(
                    rule, f"{key} {value} shared by {seen[value]!r} and {driver.get('driver-name')!r}"))
            seen[value] = driver.get("driver-name")

# -------------------------------------- PUBLIC API --------------------------------------------------------------------

def checkSaveFile(save: Dict[str, Any]) -> CheckReport:
    """Run every applicable invariant over a loaded save file.

    Args:
        save (Dict[str, Any]): The loaded save file JSON

    Returns:
        CheckReport: Violations found, plus what was checked and skipped
    """

    report = CheckReport()
    session_type = _checkMetadata(save, report)

    drivers = save.get("classification-data") or []
    _checkClassification(drivers, report)

    # Time trial has no tyre wear or temperatures at all. An unresolvable session type is
    # reported separately - lumping it in with time trial would hide a malformed save behind
    # a legitimate-looking skip.
    if session_type is None:
        wear_skip_reason = "unknown-session-type"
    elif session_type.isTimeTrialTypeSession():
        wear_skip_reason = "time-trial"
    else:
        wear_skip_reason = None

    for driver in drivers:
        name = driver.get("driver-name") or f"index-{driver.get('index')}"
        stints = driver.get("tyre-set-history") or []

        _checkStintStructure(name, stints, report)
        _checkPerLapInfo(name, driver.get("per-lap-info") or [], report)

        if wear_skip_reason:
            report.recordSkip(wear_skip_reason)
            continue

        checkable, reason = _isWearCheckable(driver)
        if not checkable:
            report.recordSkip(reason)
            continue

        report.drivers_checked += 1
        _checkStintWear(name, stints, report)

    return report
