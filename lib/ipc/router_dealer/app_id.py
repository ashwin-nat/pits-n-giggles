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
    """The launcher-managed subsystems, and the one identity each of them has.

    This is the single source of truth for who a subsystem is: the logger name, the management
    IPC server name, the argparse description, and - for the four that speak router/dealer -
    the ZMQ identity all come off it. PngSubsystem declares one member as APP_ID and reads
    everything else from that, so the names cannot drift apart.

    The set is closed on purpose: these five are the processes the launcher spawns, so being a
    subsystem and having a member here are the same fact. PIT_WALL is the broker - it has an
    identity like the rest, but it is the pub/sub fabric itself and never addresses, or is
    addressed by, anyone over the router.
    """

    BACKEND = "backend"
    HUD = "hud"
    MCP = "mcp"
    WEB = "web"
    PIT_WALL = "pit_wall"

    def __str__(self):
        return self.value
