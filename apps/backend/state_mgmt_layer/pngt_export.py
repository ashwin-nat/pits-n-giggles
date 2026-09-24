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

from lib.pngt import DriverRecord, IngestDriverExportData, SessionMetadata, TrackInfo

if TYPE_CHECKING:
    from .session_state import SessionState

# -------------------------------------- FUNCTIONS ----------------------------------------------------------------------

def build_pngt_write_args(
    session_state: "SessionState",
    dest_path: Path,
) -> Tuple[Path, SessionMetadata, list[DriverRecord], dict[int, IngestDriverExportData]]:
    """Builds SessionExportManager.write_pngt()'s args from session_state -- F1-specific
    identity data this generic manager has no access to. Cheap (dict/list construction
    only) -- safe to call inline on the event loop. Actually calling write_pngt() with
    these args, and deciding whether/how to offload that call, is the caller's job.

    Args:
        session_state (SessionState): The session to export.
        dest_path (Path): Where to write the .pngt file. Parent directory must already
            exist -- this function doesn't create it.

    Returns:
        Tuple: (dest_path, session, drivers, driver_exports), ready for
            session_state.m_export_mgr.write_pngt(*result).
    """
    driver_exports, session_best = session_state.exportTelemetry()

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
        laps_count=session_info.m_total_laps or 0,
        session_best=session_best,
    )

    # is_telemetry_public = "has driver_data" (write_pngt()'s contract), not the raw
    # telemetry_setting flag -- scope can exclude a PUBLIC driver too.
    drivers = [
        DriverRecord(
            driver_index=index,
            name=driver_obj.m_driver_info.name or "",
            team=driver_obj.m_driver_info.team or "",
            car_number=driver_obj.m_driver_info.driver_number or 0,
            nationality=None,
            platform=None,
            is_telemetry_public=index in driver_exports,
        )
        for index, driver_obj in enumerate(session_state.m_driver_data)
        if driver_obj is not None and driver_obj.is_valid
    ]

    return dest_path, session, drivers, driver_exports
