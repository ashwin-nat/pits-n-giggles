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

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

import math
from dataclasses import dataclass
from typing import Optional, Sequence

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

COMPLETE_LAP_TOLERANCE_M = 30.0

# -------------------------------------- CLASSES -----------------------------------------------------------------------

@dataclass(frozen=True)
class LapCoverage:
    """How much of a lap's distance range a recording captured. Distances are metres
    past the start line; None when nothing was recorded past it."""
    start_distance_m: Optional[float]
    end_distance_m: Optional[float]
    max_gap_m: Optional[float]


@dataclass(frozen=True)
class LapVerdict:
    complete: bool
    reason: Optional[str] = None

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def measure_lap_coverage(lap_distance: Sequence[float]) -> LapCoverage:
    """Start, end and largest sample gap of a lap's `lap_distance` array. Samples before
    the line (negative) and non-finite samples are ignored."""
    start: Optional[float] = None
    end: Optional[float] = None
    previous: Optional[float] = None
    max_gap = 0.0
    for raw in lap_distance:
        value = float(raw)
        if not math.isfinite(value) or value < 0:
            continue
        if start is None:
            start = value
        if previous is not None and value > previous:
            max_gap = max(max_gap, value - previous)
        if previous is None or value > previous:
            previous = value
        end = value if end is None else max(end, value)
    return LapCoverage(start, end, None if start is None else max_gap)


def judge_lap_coverage(
    lap_time_ms: Optional[int],
    coverage: LapCoverage,
    track_length_m: float,
    tolerance_m: float = COMPLETE_LAP_TOLERANCE_M,
) -> LapVerdict:
    """Whether a lap was captured start to finish. The exporter's `is_good` flag is
    deliberately not consulted: most beta laps it flagged started mid-lap."""
    if not lap_time_ms or lap_time_ms <= 0:
        return LapVerdict(False, "no lap time")
    start, end, gap = coverage.start_distance_m, coverage.end_distance_m, coverage.max_gap_m
    if start is None or end is None or gap is None:
        return LapVerdict(False, "not recorded past the line")
    late = start > tolerance_m
    early = end < track_length_m - tolerance_m
    if late and not early:
        return LapVerdict(False, f"last {_rounded_metres(track_length_m - start)} m only")
    if early and not late:
        return LapVerdict(False, f"first {_rounded_metres(end)} m only")
    if late and early:
        return LapVerdict(False, f"{_rounded_metres(end - start)} m mid-lap only")
    if gap > tolerance_m:
        return LapVerdict(False, f"{_rounded_metres(gap)} m gap in the trace")
    return LapVerdict(True)


def _rounded_metres(value: float) -> int:
    # floor(x + 0.5), not round(): the viewer rounds halves up and the strings must match.
    return max(10, math.floor(value / 10 + 0.5) * 10)
