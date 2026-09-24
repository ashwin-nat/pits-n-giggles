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

from lib.pngt import DriverExportData, DriverRecord, SensorConfig, SessionMetadata, TrackInfo

from .data_per_driver.telemetry_recorder.telemetry_recorder import F1_SENSORS

if TYPE_CHECKING:
    from .session_state import SessionState

# -------------------------------------- FUNCTIONS ----------------------------------------------------------------------

def in_export_scope(
    *,
    is_public: bool,
    is_player: bool,
    is_spectating: bool,
    spectator_mode: bool,
    other_players: bool,
) -> bool:
    """Whether a driver's telemetry is included in the .pngt export.
        - not public -> never
        - spectating -> only if spectator_mode (no "own car" while spectating)
        - driving, own car -> always (if public)
        - driving, another car -> only if other_players
    """
    if not is_public:
        return False
    if is_spectating:
        return spectator_mode
    if is_player:
        return True
    return other_players


def build_pngt_write_args(
    session_state: "SessionState",
    dest_path: Path,
) -> Tuple[Path, SessionMetadata, list[SensorConfig], list[DriverRecord], dict[int, DriverExportData]]:
    """Builds write_session()'s args from session_state -- F1-specific identity data
    the format-agnostic writer has no access to. Cheap (dict/list construction only)

    Args:
        session_state (SessionState): The session to export.
        dest_path (Path): Where to write the .pngt file. Parent directory must already
            exist -- this function doesn't create it.

    Returns:
        Tuple: (dest_path, session, sensors, drivers, driver_data), ready for
            write_session(*result).
    """
    # TODO: hook up actual config (Phase 9) instead of this hardcoded scope.
    is_spectating = bool(session_state.m_session_info.m_is_spectating)
    driver_data: dict[int, DriverExportData] = {}
    for index, driver_obj in enumerate(session_state.m_driver_data):
        if driver_obj is None or not driver_obj.is_valid:
            continue
        if in_export_scope(
            is_public=bool(driver_obj.m_driver_info.telemetry_setting),
            is_player=bool(driver_obj.m_driver_info.is_player),
            is_spectating=is_spectating,
            spectator_mode=False,
            other_players=True,
        ):
            driver_data[index] = driver_obj.exportTelemetry()

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

    sensors = [sensor.config for sensor in F1_SENSORS]

    return dest_path, session, sensors, drivers, driver_data
