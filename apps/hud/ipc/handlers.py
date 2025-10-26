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

from ..ui.infra import WindowManager

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def handle_lock_widgets(msg: dict, logger: logging.Logger, window_manager: WindowManager) -> dict:
    """Handle the 'lock-widgets' IPC command to lock or unlock HUD widgets.

    Args:
        msg (dict): IPC command message
        logger (logging.Logger): Logger
        window_manager (WindowManager): WindowManager

    Returns:
        dict: IPC response
    """

    # TODO - instead of toggle, use set logic based on msg content
    logger.info("Received lock-widgets command. args: %s", msg)
    window_manager.toggle_locked_state_all()
    return {"status": "success", "message": "Dummy lock-widgets handler executed."}
