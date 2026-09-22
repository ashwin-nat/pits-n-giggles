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

from ..dto import SessionBest
from .dto import BaseTelemetrySnapshot, IngestDriverExportData, IngestLapMetadata, TelemetryRecorderConfig
from .mapper import SensorMapper
from .recorder import DriverTelemetryRecorder

# -------------------------------------- CLASSES -----------------------------------------------------------------------

@dataclass(frozen=True)
class SessionExportScopeConfig:
    enabled_in_spectator_mode: bool = False
    record_other_players_cars: bool = False


class SessionExportManager:
    """Owns one DriverTelemetryRecorder per driver for the current session, applies
    recording-scope rules, and tracks the running session-best lap. Constructed once per
    session, not rebuilt per query. See this package's README for the full design
    rationale (scope rule table, late-arrival ordering, why `_discarded` exists
    independently of `_recorders`).
    """

    def __init__(
        self,
        scope_config: SessionExportScopeConfig,
        recorder_config: TelemetryRecorderConfig,
        mapper: SensorMapper,
    ) -> None:
        """
        Args:
            scope_config (SessionExportScopeConfig): Recording-scope knobs (spectator
                mode, other drivers' cars).
            recorder_config (TelemetryRecorderConfig): Sensor selection passed straight
                through to each driver's DriverTelemetryRecorder.
            mapper (SensorMapper): Sensor key resolver passed straight through to each
                driver's DriverTelemetryRecorder.
        """
        self._scope_config = scope_config
        self._recorder_config = recorder_config
        self._mapper = mapper
        self._recorders: dict[int, DriverTelemetryRecorder] = {}
        self._discarded: set[int] = set()
        self._session_best: Optional[SessionBest] = None

    # TODO: see if this can be removed. we will call update once per driver, since the driver recorder will
    # lie in DataPerDriver
    def update(self, driver_index: int, snapshot: BaseTelemetrySnapshot, frame_id: int) -> None:
        """Routes a telemetry sample to driver_index's recorder, creating it eagerly on
        first call for a never-seen, not-yet-discarded driver_index. No-ops for a
        discarded driver.

        Args:
            driver_index (int): The driver this sample belongs to.
            snapshot (BaseTelemetrySnapshot): The telemetry sample to record.
            frame_id (int): The sim's own per-packet frame identifier, used for
                flashback detection.
        """
        if driver_index in self._discarded:
            return
        recorder = self._recorders.get(driver_index)
        if recorder is None:
            recorder = DriverTelemetryRecorder(driver_index, self._recorder_config, self._mapper)
            self._recorders[driver_index] = recorder
        recorder.update(snapshot, frame_id)

    def on_lap_change(self, driver_index: int, completed_lap: IngestLapMetadata) -> None:
        """Finalises driver_index's current lap and updates the running session-best
        tracker if the completed lap is valid and faster than the current best. No-ops
        for a discarded driver, or one with no recorder yet (no update() call has
        happened for them, so there's nothing to finalise).

        Args:
            driver_index (int): The driver whose lap just completed.
            completed_lap (IngestLapMetadata): Metadata for the lap that just ended.
        """
        if driver_index in self._discarded:
            return
        recorder = self._recorders.get(driver_index)
        if recorder is None:
            return
        recorder.on_lap_change(completed_lap)

        if not completed_lap.valid or completed_lap.lap_time_ms is None:
            return
        if self._session_best is None or completed_lap.lap_time_ms < self._session_best.lap_time_ms:
            self._session_best = SessionBest(
                driver_index=driver_index,
                lap_number=completed_lap.lap_number,
                lap_time_ms=completed_lap.lap_time_ms,
            )

    def apply_scope_update(
        self,
        driver_index: int,
        *,
        is_telemetry_public: bool,
        is_player: bool,
        is_spectating: bool,
    ) -> None:
        """Re-evaluates driver_index's recording scope against newly-known facts -- the
        late-arrival discard trigger point (see this package's README). Marks the driver
        discarded, and drops any recorder already accumulated for them, the moment they
        fall out of scope. Idempotent for an already-discarded driver.

        Args:
            driver_index (int): The driver whose scope facts just became known.
            is_telemetry_public (bool): Whether this driver has consented to their
                telemetry being visible to others.
            is_player (bool): Whether this is the local player's own car.
            is_spectating (bool): Whether the app is currently spectating rather than
                driving.
        """
        if driver_index in self._discarded:
            return
        if not self._in_scope(
            is_telemetry_public=is_telemetry_public,
            is_player=is_player,
            is_spectating=is_spectating,
        ):
            self._discarded.add(driver_index)
            self._recorders.pop(driver_index, None)

    def export_all(self) -> dict[int, IngestDriverExportData]:
        """Exports every active (non-discarded) recorder. export() itself is
        non-mutating, so this can be called more than once if needed."""
        return {
            driver_index: recorder.export()
            for driver_index, recorder in self._recorders.items()
            if driver_index not in self._discarded
        }

    def session_best(self) -> Optional[SessionBest]:
        """The fastest valid lap seen across all drivers so far this session, or None if
        no valid lap has completed yet."""
        return self._session_best

    def clear(self) -> None:
        """Resets all state for reuse across a session boundary (reset in place, not
        reconstructed)."""
        self._recorders.clear()
        self._discarded.clear()
        self._session_best = None

    def _in_scope(
        self,
        *,
        is_telemetry_public: bool,
        is_player: bool,
        is_spectating: bool,
    ) -> bool:
        if not is_telemetry_public:
            return False
        if is_spectating:
            return self._scope_config.enabled_in_spectator_mode
        if is_player:
            return True
        return self._scope_config.record_other_players_cars
