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
from typing import Any, Dict

from apps.backend.state_mgmt_layer.session_state import SessionState
from lib.save_to_disk import save_json_to_file

# ------------------------- API - CLASSES ------------------------------------------------------------------------------

class ManualSaveRsp:
    """
    Manual save response class.
    """

    def __init__(self, logger: logging.Logger, session_state: SessionState):
        """Get the drivers list and prepare the rsp fields

        Args:
            logger (logging.Logger): Logger
            session_state_ref (TelState.SessionState): Reference to the session state
        """

        self.m_logger: logging.Logger = logger
        self.m_session_state: SessionState = session_state
        self.m_data_available = self.m_session_state.is_data_available
        self.m_event_str = self.m_session_state.getEventInfoStr()
        if self.m_data_available:
            self.m_data = self.m_session_state.getSaveDataJSON()
        else:
            self.m_data = None

    async def saveToDisk(self) -> Dict[str, Any]:
        """Dump the session state into JSON

        Returns:
            Dict[str, Any]: The response JSON
        """

        # Sanity checks
        if not self.m_data_available or not self.m_event_str:
            return {
                "status": "error",
                "message": "No data available to save"
            }

        now = datetime.now().astimezone()

        # Construct output filename using timestamp
        timestamp_str = now.strftime("%Y_%m_%d_%H_%M_%S")
        final_json_file_name = f"{self.m_event_str}Manual_{timestamp_str}.json"

        # Build final classification JSON
        final_json = self.m_session_state.buildFinalClassificationJSON()
        if not final_json:
            return {
                "status": "error",
                "message": "No data available to save"
            }

        final_json["debug"] = final_json.get("debug", {})
        final_json["debug"].update({
            "session-uid" : self.m_session_state.m_session_info.m_session_uid,
            "timestamp" : now.strftime("%Y-%m-%d %H:%M:%S %Z"),
            "timezone" : now.tzinfo.key if hasattr(now.tzinfo, "key") else str(now.tzinfo),
            "utc-offset-seconds" : int(now.utcoffset().total_seconds()),
            "reason": "Manual save",
            "packet-count": self.m_session_state.m_pkt_count,
            "file-name": final_json_file_name,
        })

        # Save to disk
        try:
            path = await save_json_to_file(final_json, final_json_file_name)
            self.m_logger.info("Wrote session info to %s", final_json_file_name)
            return {
                "status": "success",
                "message": f"Data saved to {path}"
            }
        except Exception as e:  # pylint: disable=broad-except
            self.m_logger.exception("Failed to write session info to %s", final_json_file_name)
            return {
                "status": "error",
                "message": f"Failed to write session info: {e.__class__.__name__}: {e}"
            }
