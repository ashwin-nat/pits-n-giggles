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

import asyncio
import logging
from typing import List

from lib.config import PngSettings
from lib.ipc import IpcSubscriberAsync

from .telemetry_web_server import TelemetryWebServer

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def initSubscriberTasks(
    settings: PngSettings,
    logger: logging.Logger,
    server: TelemetryWebServer,
    tasks: List[asyncio.Task],
) -> IpcSubscriberAsync:
    """Create and wire the broker subscriber, register topic handlers, append task.

    Args:
        settings (PngSettings): App settings (provides broker XPUB port).
        logger (logging.Logger): Logger.
        server (TelemetryWebServer): Web server to receive and fan out payloads.
        tasks (List[asyncio.Task]): Task list to append the subscriber run task to.

    Returns:
        IpcSubscriberAsync: The configured subscriber instance.
    """

    subscriber = IpcSubscriberAsync(
        host="127.0.0.1",
        port=settings.Network.broker_xpub_port,
        logger=logger,
    )

    @subscriber.route("race-table-update")
    async def _on_race_table(data: dict) -> None:
        await server.update_race_table(data)

    @subscriber.route("stream-overlay-update")
    async def _on_stream_overlay(data: dict) -> None:
        await server.update_stream_overlay(data)

    @subscriber.route("frontend-update")
    async def _on_frontend_update(data: dict) -> None:
        await server.push_frontend_update(data)

    tasks.append(asyncio.create_task(subscriber.run(), name="Broker Subscriber"))

    return subscriber
