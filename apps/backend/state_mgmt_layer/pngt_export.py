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

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Tuple

from lib.config import LapAnalyzerSettings
from lib.pngt import (MANDATORY_TELEMETRY_KEYS, CompletedLap, DriverExportData,
                      DriverRecord, SensorConfig, SessionMetadata, TrackInfo)

from .data_per_driver.telemetry_recorder.telemetry_recorder import F1_SENSORS

if TYPE_CHECKING:
    from .session_state import SessionState

# -------------------------------------- FUNCTIONS ----------------------------------------------------------------------

def selected_sensors(settings: LapAnalyzerSettings) -> list[SensorConfig]:
    """Configs of the sensors the user enabled. Empty means don't save."""
    if not settings.enable:
        return []
    return [sensor.config for field, sensor in F1_SENSORS.items() if getattr(settings.Sensors, field)]

def _filter_lap(lap: CompletedLap, keep_keys: frozenset[str]) -> CompletedLap:
    return CompletedLap(
        metadata=lap.metadata,
        telemetry={key: values for key, values in lap.telemetry.items() if key in keep_keys},
    )

def _filter_export(data: DriverExportData, sensor_keys: set[str]) -> DriverExportData:
    """Drop every sensor array not in sensor_keys, keeping the mandatory ones."""
    keep_keys = frozenset(MANDATORY_TELEMETRY_KEYS) | sensor_keys
    return DriverExportData(
        driver_index=data.driver_index,
        completed_laps=[_filter_lap(lap, keep_keys) for lap in data.completed_laps],
        in_progress_lap=_filter_lap(data.in_progress_lap, keep_keys) if data.in_progress_lap else None,
    )

def build_pngt_write_args(
    session_state: "SessionState",
    dest_path: Path,
    lap_analyzer_settings: LapAnalyzerSettings,
) -> Tuple[Path, SessionMetadata, list[SensorConfig], list[DriverRecord], dict[int, DriverExportData]]:
    """Builds write_session()'s args from session_state -- F1-specific identity data
    the format-agnostic writer has no access to. Cheap (dict/list construction only)

    Args:
        session_state (SessionState): The session to export.
        dest_path (Path): Where to write the .pngt file. Parent directory must already
            exist -- this function doesn't create it.
        lap_analyzer_settings (LapAnalyzerSettings): Settings snapshot for the whole save,
            so a hot swap mid-save can't give the sensor list and the driver scope different views.

    Returns:
        Tuple: (dest_path, session, sensors, drivers, driver_data), ready for
            write_session(*result).
    """
    sensors = selected_sensors(lap_analyzer_settings)
    sensor_keys = {sensor.key for sensor in sensors}
    driver_data: dict[int, DriverExportData] = {}
    for index, driver_obj in enumerate(session_state.m_driver_data):
        if driver_obj is None or not driver_obj.is_valid:
            continue
        # TODO: restricted telemetry. Another car set to Restricted sends zeros for ERS and tyre wear,
        # but the player's own car is always real, so telemetry_setting alone can't decide it
        driver_data[index] = _filter_export(driver_obj.exportTelemetry(), sensor_keys)

    session_info = session_state.m_session_info
    session = SessionMetadata(
        session_uid=session_info.m_session_uid or 0,
        session_name=str(session_info.m_session_type or ""),
        session_type=str(session_info.m_session_type or ""),
        app_version=session_state.m_png_version,
        game_year=session_info.m_game_year or 0,
        formula=str(session_info.m_formula or ""),
        game_version=session_state.m_game_version or "",
        timestamp=datetime.now().astimezone().isoformat(),  # export time, not session start (untracked)
        track=TrackInfo(
            id=session_info.m_track.value if session_info.m_track else 0,
            name=str(session_info.m_track or ""),
        ),
    )

    drivers = [
        DriverRecord(
            driver_index=index,
            name=driver_obj.m_driver_info.name or "",
            team=driver_obj.m_driver_info.team or "",
            car_number=driver_obj.m_driver_info.driver_number or 0,
            nationality=None,
            platform=None,
        )
        for index, driver_obj in enumerate(session_state.m_driver_data)
        if driver_obj is not None and driver_obj.is_valid
    ]

    return dest_path, session, sensors, drivers, driver_data
