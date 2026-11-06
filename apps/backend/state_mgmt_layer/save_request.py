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

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional, Set, Tuple

from lib.file_path import resolve_user_file
from lib.pngt import SessionDataEntry

from .lap_telemetry_export import build_lap_telemetry_write_args

if TYPE_CHECKING:
    from .session_state import SessionState

# Containers handed out by claim_stem(), so two saves in flight never share a file
_claimed_dests: Set[Path] = set()

# -------------------------------------- CLASS  DEFINITIONS ------------------------------------------------------------

class SaveReason(Enum):
    """Why a save happened. The value is the filename token and the JSON's debug.reason ("" = no token)."""
    AUTO = ""
    MANUAL = "Manual"
    JUST_IN_CASE = "Just_in_case"

    @property
    def debug_reason(self) -> str:
        return "Auto-save after final classification" if self is SaveReason.AUTO else self.value

@dataclass(frozen=True)
class SaveRequest:
    """Everything one unified save writes, snapshotted from session_state. Built synchronously,
    before any await and before the state is cleared. At least one of the two payloads is set.

    Attributes:
        stem (str): Shared name of the container and its inner JSON entry, computed once.
        dest_path (Path): The .pngt to write; its directory already exists.
        reason (SaveReason): Why this save happened.
        session_uid (int): For the write's own log messages.
        session_data (Optional[Dict]): The session data, debug block filled. None if not saved.
        lap_telemetry_args (Optional[Tuple]): write_session()'s args. None if lap telemetry is not saved.
    """
    stem: str
    dest_path: Path
    reason: SaveReason
    session_uid: int
    session_data: Optional[Dict[str, Any]]
    lap_telemetry_args: Optional[Tuple]

    def __str__(self) -> str:
        return f"lap_telemetry={self.lap_telemetry_args is not None} | session_data={self.session_data is not None}"

    def session_data_entry(self) -> Optional[SessionDataEntry]:
        """The session JSON as the container's session_data entry, byte-identical to what the loose
        file holds. CPU-heavy for a race (~100 ms), so call it off the event loop."""
        if self.session_data is None:
            return None
        payload = json.dumps(self.session_data, separators=(",", ":")).encode("utf-8")
        return SessionDataEntry(f"{self.stem}.json", payload)

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def build_stem(event_str: str, reason: SaveReason, now: datetime) -> str:
    """<event_str>[<reason>_]<YYYY_MM_DD_HH_MM_SS>. event_str already ends with an underscore."""
    token = f"{reason.value}_" if reason.value else ""
    return f"{event_str}{token}{now.strftime('%Y_%m_%d_%H_%M_%S')}"

def claim_stem(event_str: str, reason: SaveReason, now: datetime, dest_dir: Path) -> str:
    """build_stem(), moved forward a second at a time while that container is taken, either on disk
    or by a save still being written, so two saves in the same second never share a file."""
    while True:
        stem = build_stem(event_str, reason, now)
        dest = dest_dir / f"{stem}.pngt"
        if dest not in _claimed_dests and not dest.exists():
            _claimed_dests.add(dest)
            return stem
        now += timedelta(seconds=1)

def build_save_request(
    session_state: "SessionState",
    reason: SaveReason,
    *,
    include_session_data: bool,
    include_lap_telemetry: bool,
    logger: logging.Logger,
    final_json: Optional[Dict[str, Any]] = None,
) -> Optional[SaveRequest]:
    """Snapshots session_state into a SaveRequest. The include_* flags are the caller's gating
    decisions; this does not re-check them.

    Args:
        session_state (SessionState): The session to save.
        reason (SaveReason): Why this save is happening.
        include_session_data (bool): Save the session data.
        include_lap_telemetry (bool): Save the lap telemetry.
        logger (logging.Logger): Logger
        final_json (Optional[Dict]): The session data if the caller already built it (autosave
            does, when the final classification arrives). Built from session_state if omitted.

    Returns:
        Optional[SaveRequest]: None if the session has no event info to name it by, or nothing
            ended up to write (e.g. no data to build the JSON from, and no sensors selected).
    """
    event_str = session_state.getEventInfoStr()
    if not event_str:
        return None

    now = datetime.now().astimezone()
    dest_dir = Path(resolve_user_file("data")) / now.strftime("%Y_%m_%d")
    stem = claim_stem(event_str, reason, now, dest_dir)
    dest_path = dest_dir / f"{stem}.pngt"

    session_data = None
    if include_session_data:
        session_data = _build_session_data(session_state, reason, stem, now, logger, final_json)

    lap_telemetry_args = None
    if include_lap_telemetry:
        args = build_lap_telemetry_write_args(session_state, dest_path, session_state.m_lap_analyzer_settings)
        # An empty sensor list means settings were hot-swapped to no sensors after the caller's gating
        lap_telemetry_args = args if args[2] else None

    if session_data is None and lap_telemetry_args is None:
        return None

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    return SaveRequest(
        stem=stem,
        dest_path=dest_path,
        reason=reason,
        session_uid=session_state.m_session_info.m_session_uid or 0,
        session_data=session_data,
        lap_telemetry_args=lap_telemetry_args,
    )

def _build_session_data(
    session_state: "SessionState",
    reason: SaveReason,
    stem: str,
    now: datetime,
    logger: logging.Logger,
    final_json: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """The session JSON with its debug block filled, or None if there is no data to build it from."""
    if final_json is None:
        if session_state.is_data_available:
            final_json = session_state.buildFinalClassificationJSON()
        if not final_json:
            logger.warning("No session data available for the JSON. Saving without it.")
            return None

    final_json["debug"] = {
        "session-uid": session_state.m_session_info.m_session_uid,
        "timestamp": now.strftime("%Y-%m-%d %H:%M:%S %Z"),
        "timezone": now.tzinfo.key if hasattr(now.tzinfo, "key") else str(now.tzinfo),
        "utc-offset-seconds": int(now.utcoffset().total_seconds()),
        "reason": reason.debug_reason,
        "packet-count": session_state.m_pkt_count,
        "file-name": f"{stem}.json",
        "container": f"{stem}.pngt",
    }
    return final_json
