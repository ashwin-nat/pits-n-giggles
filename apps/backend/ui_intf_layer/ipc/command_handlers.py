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

import asyncio
import logging
import os

import apps.backend.state_mgmt_layer as TelWebAPI

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

async def handleManualSave(_msg: dict, _logger: logging.Logger) -> dict:
    """Handle manual save command"""
    return await TelWebAPI.ManualSaveRsp().saveToDisk()

async def handleShutdown(msg: dict, logger: logging.Logger) -> dict:
    """Handle shutdown command"""

    logger.info(f"Received shutdown command. Reason: {msg.get('reason', 'N/A')}")
    asyncio.create_task(_clean_exit())
    return {'status': 'success'}

async def _clean_exit():
    """Clean exit"""
    # TODO - Clean exit
    await asyncio.sleep(1)
    os._exit(0)
