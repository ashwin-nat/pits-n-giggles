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
from enum import auto, Enum
from typing import Any, Dict, Optional

from apps.backend.state_mgmt_layer import SessionState
from apps.backend.state_mgmt_layer.intf import DriverInfoRsp

# -------------------------------------- TYPES -------------------------------------------------------------------------

class RequestError(Enum):
    MISSING_PARAM   = auto()
    INVALID_PARAM   = auto()
    NOT_FOUND       = auto()

@dataclass
class DriverInfoResult:
    data:   Optional[Dict[str, Any]]  # set on success
    error:  Optional[RequestError]    # set on failure
    detail: Optional[str]             # human-readable detail for error cases

    @property
    def ok(self) -> bool:
        return self.error is None

    @classmethod
    def success(cls, data: Dict[str, Any]) -> "DriverInfoResult":
        return cls(data=data, error=None, detail=None)

    @classmethod
    def failure(cls, error: RequestError, detail: str) -> "DriverInfoResult":
        return cls(data=None, error=error, detail=detail)

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def handleDriverInfoRequest(session_state: SessionState, index_arg: Any) -> DriverInfoResult:
    """Process a driver info request given a raw index argument.

    Args:
        session_state (SessionState): The session state.
        index_arg (Any): Raw index value (string from HTTP query param or dict value from IPC).

    Returns:
        DriverInfoResult: Transport-agnostic result; inspect .ok to determine success.
    """

    if index_arg is None:
        return DriverInfoResult.failure(RequestError.MISSING_PARAM, 'Provide "index" parameter')

    if not isinstance(index_arg, int) and not str(index_arg).isdigit():
        return DriverInfoResult.failure(RequestError.INVALID_PARAM, '"index" parameter must be numeric')

    index_int = int(index_arg)
    if not session_state.isIndexValid(index_int):
        return DriverInfoResult.failure(RequestError.NOT_FOUND, f'No driver at index {index_int}')

    return DriverInfoResult.success(DriverInfoRsp(session_state, index_int).toJSON())
