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

from apps.backend.state_mgmt_layer import SessionState
from apps.backend.state_mgmt_layer.intf import ManualSaveRsp
from lib.inter_task_communicator import AsyncInterTaskCommunicator

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

async def handleManualSave(_msg: dict, logger: logging.Logger, session_state: SessionState) -> dict:
    """Handle manual save command"""
    return await ManualSaveRsp(logger, session_state).saveToDisk()

async def handleShutdown(msg: dict, logger: logging.Logger) -> dict:
    """Handle shutdown command"""

    reason = msg.get('reason', 'N/A')
    logger.info(f"Received shutdown command. Reason: {reason}")
    await AsyncInterTaskCommunicator().send('shutdown', {"reason" : reason})
    return {'status': 'success'}
