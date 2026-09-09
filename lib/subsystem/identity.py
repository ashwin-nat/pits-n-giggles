# MIT License
#
# Copyright (c) [2024] [Ashwin Natarajan]
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

"""Who each launcher-managed subsystem is.

Lives with the lifecycle base rather than under lib/ipc/, because this is identity, not
transport: lib/ipc/ never reads it, and only ever re-exported it. The router/dealer channel is
one consumer of the id among several, not its owner.

Imports nothing but enum, so a module that needs only to *address* a subsystem can import this
directly without pulling in the rest of lib/subsystem.
"""

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

from enum import Enum

# -------------------------------------- CLASSES -----------------------------------------------------------------------

class PngSubsysId(Enum):
    """The launcher-managed subsystems, and the one identity each of them has.

    This is the single source of truth for who a subsystem is: the logger name, the management
    IPC server name, the argparse description, and - for the four that speak router/dealer -
    the ZMQ identity all come off it. PngSubsystem declares one member as SUBSYS_ID and reads
    everything else from that, so the names cannot drift apart.

    The set is closed on purpose: these five are the processes the launcher spawns, so being a
    subsystem and having a member here are the same fact. PIT_WALL is the broker - it has an
    identity like the rest, but it is the pub/sub fabric itself and never addresses, or is
    addressed by, anyone over the router.

    UNKNOWN is the base class's default, so that SUBSYS_ID is a PngSubsysId at every point rather
    than an Optional that every reader has to narrow. A concrete subsystem that leaves it there
    is rejected at import - see PngSubsystem.__init_subclass__.
    """

    UNKNOWN = "unknown"

    BACKEND = "backend"
    HUD = "hud"
    MCP = "mcp"
    WEB = "web"
    PIT_WALL = "pit_wall"

    def __str__(self):
        return self.value
