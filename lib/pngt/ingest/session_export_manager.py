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
from pathlib import Path
from typing import Callable, Iterable, Optional

from ..dto import DriverRecord, SessionBest, SessionMetadata
from ..writer import write_session
from .dto import IngestDriverExportData, TelemetryRecorderConfig
from .export_adapter import adapt_driver_export
from .mapper import SensorMapper

# -------------------------------------- CLASSES -----------------------------------------------------------------------

@dataclass(frozen=True)
class SessionExportScopeConfig:
    """Recording-scope knobs. Game-agnostic on its own -- an app wiring these from real
    config (e.g. Phase 9's TelemetryRecordingSettings) is what gives them meaning."""
    enabled_in_spectator_mode: bool = False
    record_other_players_cars: bool = False


@dataclass(frozen=True)
class DriverExportCandidate:
    """One driver's export-time scope facts, plus `export_fn` -- a zero-arg callable
    returning its IngestDriverExportData. Not a recorder reference directly: the caller
    may need extra work first (e.g. reconciling against Session History), so `export_fn`
    can be that wrapper method just as easily as a bare `recorder.export`."""
    driver_index: int
    export_fn: Callable[[], IngestDriverExportData]
    is_telemetry_public: bool
    is_player: bool


class SessionExportManager:
    """Two responsibilities: aggregating each driver's already-recorded data
    (export_scoped(), scope-filtered) and writing it to a .pngt file (write_pngt()).
    Records nothing itself and owns no per-driver state -- each driver feeds its own
    DriverTelemetryRecorder directly over the session. Constructed once per session."""

    def __init__(
        self,
        scope_config: SessionExportScopeConfig,
        recorder_config: TelemetryRecorderConfig,
        mapper: SensorMapper,
    ) -> None:
        """
        Args:
            scope_config (SessionExportScopeConfig): Recording-scope knobs.
            recorder_config (TelemetryRecorderConfig): Sensor keys recorders were built
                with -- write_pngt() uses these for the .pngt manifest.
            mapper (SensorMapper): Resolves each sensor key's SensorConfig/dtype for the
                manifest -- write_pngt() uses mapper.sensor_config(), not part of the
                ABC itself, so a mapper without one raises AttributeError there.
        """
        self._scope_config = scope_config
        self._recorder_config = recorder_config
        self._mapper = mapper

    def in_scope(
        self,
        *,
        is_telemetry_public: bool,
        is_player: bool,
        is_spectating: bool,
    ) -> bool:
        """Recording-scope rule:
            - not public -> never in scope
            - spectating -> in scope only if `enabled_in_spectator_mode` (no "own car"
              while spectating, so `record_other_players_cars` doesn't apply)
            - driving, own car -> always in scope (if public)
            - driving, another car -> in scope only if `record_other_players_cars`
        """
        if not is_telemetry_public:
            return False
        if is_spectating:
            return self._scope_config.enabled_in_spectator_mode
        if is_player:
            return True
        return self._scope_config.record_other_players_cars

    def export_scoped(
        self,
        candidates: Iterable[DriverExportCandidate],
        *,
        is_spectating: bool,
    ) -> dict[int, IngestDriverExportData]:
        """Aggregates every in-scope driver's data in one pass, at session end.
        `is_spectating` is session-wide, not per-driver."""
        result: dict[int, IngestDriverExportData] = {}
        for candidate in candidates:
            if self.in_scope(
                is_telemetry_public=candidate.is_telemetry_public,
                is_player=candidate.is_player,
                is_spectating=is_spectating,
            ):
                result[candidate.driver_index] = candidate.export_fn()
        return result

    def compute_session_best(
        self,
        driver_exports: dict[int, IngestDriverExportData],
    ) -> Optional[SessionBest]:
        """Scans already-exported data for the fastest valid lap across all drivers."""
        best: Optional[SessionBest] = None
        for driver_index, export in driver_exports.items():
            for lap in export.completed_laps:
                if not lap.metadata.valid or lap.metadata.lap_time_ms is None:
                    continue
                if best is None or lap.metadata.lap_time_ms < best.lap_time_ms:
                    best = SessionBest(
                        driver_index=driver_index,
                        lap_number=lap.metadata.lap_number,
                        lap_time_ms=lap.metadata.lap_time_ms,
                    )
        return best

    def write_pngt(
        self,
        dest_path: Path,
        session: SessionMetadata,
        drivers: list[DriverRecord],
        driver_exports: dict[int, IngestDriverExportData],
    ) -> Path:
        """Writes export_scoped()'s result to a .pngt file.

        `session`/`drivers` come from the caller: session/driver identity data this
        class has no access to. Every driver needs a `drivers` entry (including
        out-of-scope ones); each entry's `is_telemetry_public` must agree with whether
        that index is a key in `driver_exports`, or write_session() rejects it.

        Returns:
            Path: dest_path, once written.
        """
        sensor_keys = self._recorder_config.sensors
        sensors = [self._mapper.sensor_config(key) for key in sensor_keys]
        dtypes = {key: self._mapper.get_dtype(key) for key in sensor_keys}
        driver_data = {
            driver_index: adapt_driver_export(export)
            for driver_index, export in driver_exports.items()
        }
        return write_session(dest_path, session, sensors, dtypes, drivers, driver_data)
