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

from lib.config import PngSettings
from lib.ipc import IpcDealerAsync, PngAppId

from .telemetry_web_server import TelemetryWebServer

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def initDealer(
        settings: PngSettings,
        logger: logging.Logger,
        server: TelemetryWebServer) -> IpcDealerAsync:
    """Create and configure the ZeroMQ DEALER for the HTTP server.

    Args:
        settings (PngSettings): App settings (provides broker router port).
        logger (logging.Logger): Logger.
        server (TelemetryWebServer): Web server instance for inbound route handlers.

    Returns:
        IpcDealerAsync: Configured dealer (not yet started).
    """

    dealer = IpcDealerAsync(
        host="127.0.0.1",
        port=settings.Network.broker_router_port,
        identity=str(PngAppId.HTTP_SERVER),
        logger=logger,
    )

    @dealer.route("frontend-update")
    async def _on_frontend_update(data: dict, _sender: str) -> None:
        await server.push_frontend_update(data)

    return dealer

# -------------------------------------- EXPORTS -----------------------------------------------------------------------

__all__ = [
    "initDealer",
]
