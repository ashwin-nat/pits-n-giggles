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

from dataclasses import dataclass
from typing import Optional

from ..dto import CompletedLap, DriverExportData, LapMetadata
from .dto import IngestDriverExportData

# -------------------------------------- CLASSES -----------------------------------------------------------------------

@dataclass(frozen=True)
class InProgressLapContext:
    """Current-lap tyre/pit facts an in-progress lap needs that IngestDriverExportData
    doesn't carry -- DriverTelemetryRecorder only knows telemetry samples."""
    tyre_compound: str
    tyre_laps: int
    pit_in_lap: bool
    pit_out_lap: bool

# -------------------------------------- FUNCTIONS ----------------------------------------------------------------------

def adapt_driver_export(
    ingest: IngestDriverExportData,
    in_progress_context: Optional[InProgressLapContext] = None,
) -> DriverExportData:
    """Converts one driver's DriverTelemetryRecorder.export() result into the shape
    write_session() expects. `is_good` defaults to False -- write_session()'s own
    _apply_default_good_lap() marks the fastest valid lap good. Missing
    in_progress_context defaults to empty/False rather than raising."""
    completed_laps = [
        CompletedLap(
            metadata=LapMetadata(
                lap_number=lap.metadata.lap_number,
                lap_time_ms=lap.metadata.lap_time_ms,
                valid=lap.metadata.valid,
                tyre_compound=lap.metadata.tyre_compound,
                tyre_laps=lap.metadata.tyre_laps,
                pit_in_lap=lap.metadata.pit_in_lap,
                pit_out_lap=lap.metadata.pit_out_lap,
                num_points=lap.metadata.num_points,
                is_good=False,
            ),
            telemetry=lap.telemetry,
        )
        for lap in ingest.completed_laps
    ]

    in_progress_lap = None
    if ingest.in_progress_num_points > 0:
        context = in_progress_context or InProgressLapContext(
            tyre_compound="", tyre_laps=0, pit_in_lap=False, pit_out_lap=False)
        in_progress_lap = CompletedLap(
            metadata=LapMetadata(
                lap_number=ingest.in_progress_lap_number,
                lap_time_ms=None,
                valid=False,
                tyre_compound=context.tyre_compound,
                tyre_laps=context.tyre_laps,
                pit_in_lap=context.pit_in_lap,
                pit_out_lap=context.pit_out_lap,
                num_points=ingest.in_progress_num_points,
                is_good=False,
            ),
            telemetry=ingest.in_progress_telemetry,
        )

    return DriverExportData(
        driver_index=ingest.driver_index,
        completed_laps=completed_laps,
        in_progress_lap=in_progress_lap,
    )
