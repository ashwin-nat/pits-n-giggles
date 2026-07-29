# MIT License
#
# Copyright (c) [2024] [Ashwin Natarajan]
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

# ------------------------- IMPORTS ------------------------------------------------------------------------------------

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from apps.backend.state_mgmt_layer.session_state import SessionState
from lib.save_to_disk import save_json_to_file

# ------------------------- API - CLASSES ------------------------------------------------------------------------------

class ManualSaveRsp:
    """
    Manual save response class.
    """

    def __init__(self, logger: logging.Logger, session_state: SessionState, reason: str = "Manual"):
        """Prepare all data for saving. The saveToDisk method only performs the async write.

        Args:
            logger (logging.Logger): Logger
            session_state (SessionState): Reference to the session state
            reason (str, optional): Reason for the save. Defaults to "Manual".
        """

        self.m_logger: logging.Logger = logger

        event_str, final_json = self._prepareData(session_state)
        now = datetime.now().astimezone()
        self.m_file_name: str = self._buildFileName(event_str, reason, now)
        self.m_final_json: Dict[str, Any] = self._injectDebugFields(final_json, session_state, now, reason, self.m_file_name)

    @staticmethod
    def _prepareData(session_state: SessionState):
        """Validate session state and extract the base JSON payload.

        Raises:
            ValueError: If no data is available to save.

        Returns:
            tuple: (event_str, final_json)
        """
        if not session_state.is_data_available:
            raise ValueError("No data available to save")
        event_str = session_state.getEventInfoStr()
        if not event_str:
            raise ValueError("No data available to save")
        final_json = session_state.buildFinalClassificationJSON()
        if not final_json:
            raise ValueError("No data available to save")
        return event_str, final_json

    @staticmethod
    def _buildFileName(event_str: str, reason: str, now: datetime) -> str:
        """Construct the output filename from event, reason, and timestamp.

        Note: event_str is already suffixed with an underscore.
        """
        return f"{event_str}{reason}_{now.strftime('%Y_%m_%d_%H_%M_%S')}.json"

    @staticmethod
    def _injectDebugFields(
        final_json: Dict[str, Any],
        session_state: SessionState,
        now: datetime,
        reason: str,
        file_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Stamp debug metadata into the JSON payload and return it."""
        final_json["debug"] = final_json.get("debug", {})
        debug_fields: Dict[str, Any] = {
            "session-uid": session_state.m_session_info.m_session_uid,
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S %Z"),
            "timezone": now.tzinfo.key if hasattr(now.tzinfo, "key") else str(now.tzinfo),
            "utc-offset-seconds": int(now.utcoffset().total_seconds()),
            "reason": reason,
            "packet-count": session_state.m_pkt_count,
        }
        if file_name is not None:
            debug_fields["file-name"] = file_name
        final_json["debug"].update(debug_fields)
        return final_json

    async def saveToDisk(self) -> Dict[str, Any]:
        """Write the prepared data to disk.

        Returns:
            Dict[str, Any]: The response JSON
        """

        try:
            path = await save_json_to_file(self.m_final_json, self.m_file_name)
            self.m_logger.info("Wrote session info to %s", self.m_file_name)
            return {"status": "success", "message": f"Data saved to {path}"}
        except Exception as e:  # pylint: disable=broad-except
            self.m_logger.exception("Failed to write session info to %s", self.m_file_name)
            return {
                "status": "error",
                "message": f"Failed to write session info: {e.__class__.__name__}: {e}"
            }
