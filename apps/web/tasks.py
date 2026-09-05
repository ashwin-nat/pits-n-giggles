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

from .web_server import WebServer

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

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
