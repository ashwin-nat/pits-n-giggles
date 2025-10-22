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

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

import logging
import threading

from .client import HudClient
from ..ui.infra import WindowManager

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def _hud_update_task(port: int, logger: logging.Logger, window_manager: WindowManager, stop_event: threading.Event):
    """Hud update task."""
    client = HudClient(port, logger, window_manager, stop_event)
    client.run()

def run_hud_update_thread(
        port: int,
        window_manager: WindowManager,
        logger: logging.Logger,
        stop_event: threading.Event
        ) -> threading.Thread:
    """Creates, runs and returns the HUD update thread.

    Args:
        port: Port number of the Socket.IO server.
        logger: Logger instance.
        window_manager: WindowManager instance.
        stop_event: Event to signal stopping.

    Returns:
        threading.Thread: HUD update thread.
    """
    ret = threading.Thread(target=_hud_update_task, args=(port, logger, window_manager, stop_event), daemon=True)
    ret.start()
    return ret
