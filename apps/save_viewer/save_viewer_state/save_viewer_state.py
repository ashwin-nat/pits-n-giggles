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

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

import logging
from typing import Any, Dict

from .get_driver_info import _getDriverInfo
from .get_race_info import _getRaceInfo
from .get_telemetry_info import _getTelemetryInfo

# -------------------------------------- GLOBALS -----------------------------------------------------------------------

_logger: logging.Logger = None

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def init_state(logger: logging.Logger) -> None:
    """Initialize the state of the application. Init the module level logger"""
    global _logger
    _logger = logger

def getTelemetryInfoFrom(data: Dict[str, Any]) -> Dict[str, Any]:
    """Get telemetry info from an explicit JSON payload (slug-based path).

    Args:
        data: Session JSON dict.

    Returns:
        Dict[str, Any]: Telemetry info (same shape as getTelemetryInfo).
    """
    return _getTelemetryInfo(data)

def getRaceInfoFrom(data: Dict[str, Any]) -> Dict[str, Any]:
    """Get race info from an explicit JSON payload (slug-based path).

    Args:
        data: Session JSON dict.

    Returns:
        Dict[str, Any]: Race info.
    """
    global _logger
    return _getRaceInfo(data, _logger)

def getDriverInfoFrom(data: Dict[str, Any], index: int) -> Dict[str, Any]:
    """Get driver info from an explicit JSON payload (slug-based path).

    Args:
        data: Session JSON dict.
        index: Driver index.

    Returns:
        Dict[str, Any]: Driver info.
    """
    return _getDriverInfo(data, index)
