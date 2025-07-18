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
from typing import Callable, Awaitable, Dict

from .command_handlers import handleManualSave

# -------------------------------------- CONSTANTS ---------------------------------------------------------------------

# Define a type for async handler functions
CommandHandler = Callable[[dict], Awaitable[dict]]


# Registry of command handlers
COMMAND_HANDLERS: Dict[str, CommandHandler] = {
    "manual-save": handleManualSave,
}

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

async def processIpcCommand(msg: dict, logger: logging.Logger) -> dict:
    """Handle IPC commands from the parent process (launcher)

    Args:
        msg (dict): IPC command
        logger (logging.Logger): Logger

    Returns:
        dict: IPC response
    """
    logger.debug(f"Received IPC command: {json.dumps(msg, indent=2)}")

    if not (cmd := msg.get("cmd")):
        return {"status": "error", "message": "Missing command name"}

    if not (handler := COMMAND_HANDLERS.get(cmd)):
        return {"status": "error", "message": f"Unknown command: {cmd}"}

    try:
        args = msg.get("args", {})
        return await handler(args)
    except Exception as e: # pylint: disable=broad-except
        logger.exception(f"Error handling command '{cmd}': {e}")
        return {"status": "error", "message": f"Exception during command handling: {str(e)}"}
