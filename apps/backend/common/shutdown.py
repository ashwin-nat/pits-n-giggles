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

from logging import Logger
from lib.inter_task_communicator import AsyncInterTaskCommunicator
from lib.web_server import BaseWebServer
import asyncio
import os

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

async def shutdown_tasks(logger: Logger, server: BaseWebServer, shutdown_event: asyncio.Event) -> None:
    """Shutdown all the tasks and stop the event loop"""

    logger.debug("Starting shutdown task. Awaiting shutdown command...")
    await AsyncInterTaskCommunicator().receive("shutdown")
    logger.debug("Received shutdown command. Stopping tasks...")

    # TODO - Clean exit
    shutdown_event.set()
    await AsyncInterTaskCommunicator().unblock_receivers()
    await server.stop()
    await asyncio.sleep(1)
    os._exit(0)
