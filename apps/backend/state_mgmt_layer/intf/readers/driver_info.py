# MIT License
#
# Copyright (c) [2025] [Ashwin Natarajan]
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

from typing import Any, Dict

from apps.backend.state_mgmt_layer.overtakes import GetOvertakesStatus
from apps.backend.state_mgmt_layer.session_state import SessionState

from ..base import BaseAPI

# ------------------------- API - CLASSES ------------------------------------------------------------------------------

class DriverInfoRsp(BaseAPI):
    """
    Driver info response class.
    """

    def __init__(self, session_state: SessionState, index: int):
        """Get the driver info and prepare the rsp fields

        Args:
            session_state (SessionState): Handle to the session state data structure
            index (int): Index of the driver
        """

        self.m_rsp = session_state.getDriverInfoJsonByIndex(index)
        assert self.m_rsp
        status, overtakes_info = session_state.getOvertakeJSON(self.m_rsp["driver-name"])
        self.m_rsp["overtakes-status-code"] = str(status)
        self.m_rsp['overtakes'] = overtakes_info
        assert status != GetOvertakesStatus.INVALID_INDEX

    def toJSON(self) -> Dict[str, Any]:
        """Dump this object into JSON

        Returns:
            Dict[str, Any]: The JSON dump
        """

        return self.m_rsp
