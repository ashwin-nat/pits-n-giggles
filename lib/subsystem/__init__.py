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

"""Child-side lifecycle base for launcher-managed subsystems.

The launcher spawns five children and manages them like systemd units - spawn, handshake,
heartbeat, shutdown, stats. The parent side of that contract lives in
`apps/launcher/subsystems/base_mgr.py`; this package is the child side of it.

    PngSubsystem   - args, logger, config, handshake tokens, the three IPC surfaces,
                     exception funnel
    AsyncSubsystem - adds an asyncio task registry and gather/cancel teardown
    SyncSubsystem  - adds a thread registry and a blocking run_forever() handoff

There are three flavours of IPC, and a subsystem sees each under its own name and keeps each
one's own vocabulary - there is no abstraction over the three:

    @self.mgmt.on("manual-save")                # reqrep, the launcher's control channel
    @self.subscriber.route("race-table-update") # pub/sub, the telemetry fabric
    @self.dealer.route("driver-info")           # router/dealer, between apps

...and self.publisher.publish(topic, data) for the other end of the pub/sub fabric.
"""

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

from .async_app import AsyncSubsystem
from .base import MgmtIpcHandle, PngSubsystem, PubSubRole
from .sync_app import SyncSubsystem

# -------------------------------------- EXPORTS -----------------------------------------------------------------------

__all__ = [
    "AsyncSubsystem",
    "MgmtIpcHandle",
    "PngSubsystem",
    "PubSubRole",
    "SyncSubsystem",
]
