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
from typing import Any, Dict

from lib.ipc import IpcDealerAsync, IpcSubscriberAsync, PngAppId
from lib.web_server import ClientType

from .web_server import WebServer

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def initSubscriber(
        port: int,
        logger: logging.Logger,
        web_server: WebServer) -> IpcSubscriberAsync:
    """Create the broker subscriber. Routes only cache the latest payload — emission to browsers
    happens on the web server's own timer, not at broker cadence.

    Args:
        port (int): Broker XPUB port
        logger (logging.Logger): Logger
        web_server (WebServer): The web server whose cache gets updated

    Returns:
        IpcSubscriberAsync: The subscriber instance
    """
    ipc_sub = IpcSubscriberAsync(port=port, logger=logger)

    @ipc_sub.route("race-table-update")
    async def _handle_race_table_update(data: Dict[str, Any]) -> None:
        web_server.update_race_table_cache(data)

    @ipc_sub.route("stream-overlay-update")
    async def _handle_stream_overlay_update(data: Dict[str, Any]) -> None:
        web_server.update_stream_overlay_cache(data)

    return ipc_sub

def initDealer(
        port: int,
        logger: logging.Logger,
        web_server: WebServer) -> IpcDealerAsync:
    """Create the web subsystem's router/dealer client.

    Handles the unsolicited `frontend-update` push from the backend, and is also used by
    `WebServer` (via `set_dealer`) to bridge `/driver-info` and `/race-info` pulls.

    Args:
        port (int): Broker router port
        logger (logging.Logger): Logger
        web_server (WebServer): The web server to forward frontend-update messages to

    Returns:
        IpcDealerAsync: The dealer instance
    """
    dealer = IpcDealerAsync(
        host="127.0.0.1",
        port=port,
        identity=str(PngAppId.WEB),
        logger=logger,
    )

    @dealer.route("frontend-update")
    async def _handle_frontend_update(data: dict, _sender: str) -> None:
        await web_server.send_to_clients_of_type(
            event='frontend-update',
            data=data,
            client_type=ClientType.RACE_TABLE)

    web_server.set_dealer(dealer)
    return dealer

async def raceTableEmitTask(web_server: WebServer) -> None:
    """Emit the cached race-table-update payload verbatim, if any client is interested."""
    if web_server.m_race_table_cache is not None and web_server.is_any_client_interested_in_event('race-table-update'):
        await web_server.send_to_clients_interested_in_event(
            event='race-table-update',
            data=web_server.m_race_table_cache)

async def streamOverlayEmitTask(web_server: WebServer) -> None:
    """Emit the cached stream-overlay-update payload verbatim, if any client is interested."""
    if web_server.m_stream_overlay_cache is not None and \
            web_server.is_any_client_interested_in_event('stream-overlay-update'):
        await web_server.send_to_clients_interested_in_event(
            event='stream-overlay-update',
            data=web_server.m_stream_overlay_cache)
