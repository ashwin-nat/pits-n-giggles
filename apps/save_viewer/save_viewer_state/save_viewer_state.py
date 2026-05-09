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

import json
import logging
from pathlib import Path
from typing import Any, Dict

from apps.save_viewer.session_discovery import check_recompute_json

from .get_driver_info import _getDriverInfo
from .get_race_info import _getRaceInfo
from .get_telemetry_info import _getTelemetryInfo

# -------------------------------------- GLOBALS -----------------------------------------------------------------------

_json_data: Dict[str, Any] = {}
_logger: logging.Logger = None

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def init_state(logger: logging.Logger) -> None:
    """Initialize the state of the application. Init the module level logger"""
    global _logger
    _logger = logger

def getTelemetryInfo() -> Dict[str, Any]:
    """
    Main function to retrieve and format complete telemetry information.

    Returns:
        Complete telemetry data structure with session info and driver entries
    """
    global _json_data
    return _getTelemetryInfo(_json_data)

def getRaceInfo() -> Dict[str, Any]:
    """Get the race info."""
    global _json_data, _logger
    return _getRaceInfo(_json_data, _logger)

def getDriverInfo(index: int) -> Dict[str, Any]:
    """Get the driver info for the given index. Assumes the index is an int. Type checking is caller's responsibility

    Args:
        index (int): Index of the driver.

    Returns:
        Dict[str, Any]: Driver info.
    """
    global _json_data
    return _getDriverInfo(_json_data, index)

async def open_file_helper(file_path):
    """Validate, load the JSON file and parse it and update the module global."""

    if not file_path:
        return {"status": "error", "message": "Missing or invalid file path"}

    # Path traversal protection: block relative parent-directory escape
    if ".." in Path(file_path).parts:
        _logger.warning("Path traversal attempt blocked: %s", file_path)
        return {"status": "error", "message": "Path contains disallowed traversal sequence"}

    try:
        resolved = Path(file_path).resolve()
    except (OSError, ValueError):
        return {"status": "error", "message": "Invalid file path"}

    # Must point to an existing regular file with allowed extension
    if not resolved.is_file():
        return {"status": "error", "message": "Path does not point to an existing file"}

    if resolved.suffix.lower() != ".json":
        return {"status": "error", "message": "File type not allowed"}

    try:
        with open(str(resolved), 'r+', encoding='utf-8') as f:
            global _json_data
            _json_data = json.load(f)
            check_recompute_json(_json_data)

        _logger.info("Opened file: %s", resolved)
        return {"status": "success"}

    except (FileNotFoundError, PermissionError) as e:
        _logger.error("Failed to open file: %s. Error: %s", file_path, e)
        return {"status": "error", "message": f"Failed to open file: {file_path}. Error: {e}"}
    except json.JSONDecodeError as e:
        _logger.error("Invalid JSON in file: %s. Error: %s", file_path, e)
        return {"status": "error", "message": f"Failed to open file: {file_path}. Error: {e}"}
    except UnicodeDecodeError as e:
        _logger.error("Invalid UTF-8 in file: %s. Error: %s", file_path, e)
        return {"status": "error", "message": f"Failed to open file: {file_path}. Error: {e}"}
    except Exception as e:  # pylint: disable=broad-exception-caught
        _logger.exception("Unexpected error opening file: %s", file_path)
        return {"status": "error", "message": "Failed to open file"}


