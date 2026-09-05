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

from enum import Enum

# TODO: move PngAppId out to a top-level module (e.g. lib/app_id.py).
# It is subsystem identity, not a router/dealer detail - lib/subsystem/ now declares it as
# APP_ID on every subsystem, so consumers with no interest in the router still have to reach
# into lib/ipc/router_dealer/ to name themselves. The enum stays re-exported from lib.ipc
# either way, so the move is an import change rather than an API change.

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class PngAppId(Enum):
    """Fixed ZMQ identities for PNG apps that connect to the router."""
    BACKEND = "backend"
    HUD = "hud"
    MCP = "mcp"
    WEB = "web"

    def __str__(self):
        return self.value
