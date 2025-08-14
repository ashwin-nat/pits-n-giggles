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
from logging import Logger

from apps.backend.telemetry_layer import F1TelemetryHandler
from lib.inter_task_communicator import AsyncInterTaskCommunicator
from lib.web_server import BaseWebServer

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

async def shutdown_tasks(logger: Logger,
                         server: BaseWebServer,
                         shutdown_event: asyncio.Event,
                         telemetry_handler: F1TelemetryHandler) -> None:
    """Shutdown all the tasks and stop the event loop

    Args:
        logger (Logger): Logger
        server (BaseWebServer): Web server handle
        shutdown_event (asyncio.Event): Event to signal shutdown
        telemetry_handler (F1TelemetryHandler): Telemetry handler handle
    """

    logger.debug("Starting shutdown task. Awaiting shutdown command...")
    await AsyncInterTaskCommunicator().receive("shutdown")
    logger.debug("Received shutdown command. Stopping tasks...")

    # Periodic UI update tasks and packet forwarder are listening to shutdown event
    shutdown_event.set()
    await AsyncInterTaskCommunicator().unblock_receivers()

    # Explicitly stop the
    await server.stop()
    await telemetry_handler.stop()
    await asyncio.sleep(1)

    logger.debug("Tasks stopped. Exiting...")
