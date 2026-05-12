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

import logging
import os

from lib.error_status import PNG_LOST_CONN_TO_PARENT
from lib.inter_task_communicator import AsyncInterTaskCommunicator
from lib.ipc import IpcDealerAsync, IpcSubscriberAsync

from ..telemetry_web_server import TelemetryWebServer

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

async def handleShutdown(msg: dict, logger: logging.Logger) -> dict:
    """Handle shutdown command."""
    reason = msg.get('reason', 'N/A')
    logger.info("Received shutdown command. Reason: %s", reason)
    await AsyncInterTaskCommunicator().send('shutdown', {"reason": reason})
    return {'status': 'success'}

async def handleHeartbeatMissed(count: int, logger: logging.Logger) -> dict:
    """Terminate when parent heartbeat is lost."""
    logger.error("Missed heartbeat %d times. This process has probably been orphaned. Terminating...", count)
    os._exit(PNG_LOST_CONN_TO_PARENT)

async def handleGetStats(
        web_server: TelemetryWebServer,
        subscriber: IpcSubscriberAsync,
        dealer: IpcDealerAsync,
        ) -> dict:
    """Handle get-stats command."""
    return {
        "status": "success",
        "stats": {
            "web_server": web_server.get_stats(),
            "subscriber": subscriber.stats.get_stats(),
            "dealer": dealer.get_stats(),
        }
    }
