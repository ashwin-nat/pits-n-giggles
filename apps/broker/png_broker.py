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

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

from typing import Any, Dict, Optional, override

from lib.ipc import IpcPubSubBroker, IpcRouter
from lib.subsystem import SyncSubsystem

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------

class BrokerSubsystem(SyncSubsystem):
    """The Pit Wall - the ZeroMQ pub/sub broker and router that every other subsystem talks
    through.

    Declares no data plane of its own: this process *is* the fabric, not a participant in it.
    """

    NAME = "pit_wall"
    DESCRIPTION = "Pit Wall"

    def __init__(self) -> None:
        """Construct the subsystem. Nothing is started until main() runs."""

        super().__init__()
        self.broker: Optional[IpcPubSubBroker] = None
        self.router: Optional[IpcRouter] = None

    @override
    def setup(self) -> None:
        """Start the pub/sub broker and the router, each in its own thread."""

        self.broker = IpcPubSubBroker(
            xsub_port=self.settings.Network.broker_xsub_port,
            xpub_port=self.settings.Network.broker_xpub_port,
            logger=self.logger)
        self.add_thread(self.broker.run_in_thread())

        self.router = IpcRouter(port=self.settings.Network.broker_router_port, logger=self.logger)
        self.add_thread(self.router.run_in_thread())

    @override
    def run_forever(self) -> None:
        """Wait until the launcher asks us to stop.

        The broker, the router and the management IPC server each service their own thread,
        so the main thread has nothing to do but hold the process open.
        """

        self.shutdown_event.wait()

    @override
    def collect_stats(self) -> Dict[str, Any]:
        """Return broker and router throughput stats.

        Returns:
            Dict[str, Any]: Stats body
        """

        return {
            "broker": self.broker.get_stats(),
            "router": self.router.get_stats(),
        }

    @override
    def on_shutdown(self, reason: str) -> None:
        """Close both sockets, which lets their threads wind up.

        Args:
            reason (str): Why the shutdown was requested
        """

        self.logger.debug("Shutting down the broker. Reason: %s", reason)
        self.broker.close()
        self.router.close()

# -------------------------------------- ENTRY POINT -------------------------------------------------------------------

def entry_point():
    """Entry point"""

    BrokerSubsystem.main()
